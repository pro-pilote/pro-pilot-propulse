#!/usr/bin/env python3
"""
ppl_static — boîte à outils pour gérer un site STATIC sur la plateforme Pro Web
(pro-web.propulse-lab.com), assisté par IA (Claude Code).

La boîte fournit les *mains* (récupérer / éditer en local / publier) ; le
*cerveau*, c'est Claude Code — ta propre session, en local. Aucune IA côté
serveur, rien à payer en tokens en plus de ta souscription habituelle.

Workflow type :

    python3 ppl_static.py pull   <domaine>     # miroir local complet du site
    (ouvre Claude Code à la racine du kit et décris ta modif dans sites/<domaine>/)
    python3 ppl_static.py preview <domaine>    # http://localhost:8080 avant publication
    python3 ppl_static.py push   <domaine>     # publie seulement les fichiers modifiés

Auth : lance d'abord `python ppl.py login` (voir README.md). Toute écriture
(push/add/rm/set-home) est en PROD → dry-run par défaut, `--go` pour publier.

Commandes : resolve · ls · pull · preview · push · add · rm · set-home
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import proweb_env as env
env.setup_console()

try:
    import requests
except ImportError:
    sys.exit(f"❌ dépendance manquante : {env.PY_CMD} -m pip install requests")

BASE_URL = f"https://{env.DOMAIN}"
TOKEN_PATH = env.TOKEN_PATH
BASE = Path(__file__).resolve().parent
WORKSPACE = Path(os.environ.get("PPL_WORKSPACE") or os.getcwd()).resolve()
SITES = WORKSPACE / "sites"
CACHE = WORKSPACE / ".cache.json"
MANIFEST = ".ppl-manifest.json"
PUSH_WORKERS = 8

CONTENT_TYPES = {
    ".html": ("text/html", "DOCUMENT:TEXT"),
    ".htm": ("text/html", "DOCUMENT:TEXT"),
    ".css": ("text/css", "DOCUMENT:TEXT"),
    ".js": ("application/javascript", "DOCUMENT:TEXT"),
    ".mjs": ("application/javascript", "DOCUMENT:TEXT"),
    ".json": ("application/json", "DOCUMENT:TEXT"),
    ".txt": ("text/plain", "DOCUMENT:TEXT"),
    ".xml": ("application/xml", "DOCUMENT:TEXT"),
    ".webmanifest": ("application/manifest+json", "DOCUMENT:TEXT"),
    ".png": ("image/png", "DOCUMENT:IMAGE"),
    ".jpg": ("image/jpeg", "DOCUMENT:IMAGE"),
    ".jpeg": ("image/jpeg", "DOCUMENT:IMAGE"),
    ".gif": ("image/gif", "DOCUMENT:IMAGE"),
    ".webp": ("image/webp", "DOCUMENT:IMAGE"),
    ".ico": ("image/x-icon", "DOCUMENT:IMAGE"),
    ".svg": ("image/svg+xml", "DOCUMENT:IMAGE"),
    ".avif": ("image/avif", "DOCUMENT:IMAGE"),
    ".pdf": ("application/pdf", "DOCUMENT:PDF"),
}

FORBIDDEN_VIDEO_EXTS = {".mp4", ".webm", ".mov", ".avi", ".mkv", ".m4v", ".ogv"}
MAX_FILE_SIZE = 20_000_000  # 20 Mo (conforme WebsiteAddObject.vue:399, 825)


def content_meta(key, content=None, existing_record=None):
    ext = Path(key).suffix.lower()
    if ext in FORBIDDEN_VIDEO_EXTS:
        die(f"Fichier vidéo non autorisé sur STATIC ({key}). Les vidéos doivent être hébergées sur Pro-Vidéo.")
    if ext in CONTENT_TYPES:
        return CONTENT_TYPES[ext]
    if isinstance(content, (bytes, bytearray)):
        if content.startswith(b"%PDF-"):
            return ("application/pdf", "DOCUMENT:PDF")
        if content.startswith(b"\x89PNG\r\n\x1a\n"):
            return ("image/png", "DOCUMENT:IMAGE")
        if content.startswith(b"\xff\xd8\xff"):
            return ("image/jpeg", "DOCUMENT:IMAGE")
        head = content[:512].lstrip().lower()
        if head.startswith(b"<!doctype html") or head.startswith(b"<html") or b"<head" in head or b"<body" in head:
            return ("text/html; charset=utf-8", "DOCUMENT:TEXT")
    if existing_record and existing_record.get("subtype") == "DOCUMENT:PDF":
        return ("application/pdf", "DOCUMENT:PDF")
    if existing_record and existing_record.get("type") == "PAGE":
        return ("text/html; charset=utf-8", existing_record.get("subtype"))
    return ("application/octet-stream", "DOCUMENT:TEXT")


def die(msg):
    sys.exit(f"❌ {msg}")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def confirm(msg):
    try:
        ans = input("Tapez OUI pour confirmer le déploiement en PRODUCTION : ").strip()
        return ans == "OUI"
    except (EOFError, KeyboardInterrupt):
        return False


def gate(args, dry_msg, confirm_msg):
    """Dry-run/confirmation partagés par toutes les commandes d'écriture.
    Retourne True si l'action doit s'exécuter."""
    if not args.go:
        print(f"\n[DRY-RUN] {dry_msg}")
        return False
    if args.go and not sys.stdin.isatty():
        die("Publication en production interdite en mode non-interactif (TTY requis). Lancez la commande directement dans votre terminal.")
    if not confirm(f"\n{confirm_msg}"):
        print("Annulé.")
        return False
    return True


def to_json(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, obj):
    path.write_text(to_json(obj), encoding="utf-8")


# --- auth + appel API ----------------------------------------------------
def load_token():
    if not TOKEN_PATH.exists():
        die(f"pas de token — lance d'abord : {env.PY_CMD} ppl.py login\n"
            f"   (ou crée {TOKEN_PATH} à la main, voir README.md)")
    data = read_json(TOKEN_PATH)
    if not data.get("bearer"):
        die(f"{TOKEN_PATH} ne contient pas de champ 'bearer' — relance : {env.PY_CMD} ppl.py login")
    return data


_TOKEN = None
_TOKEN_EPOCH = 0
_REFRESH_LOCK = threading.Lock()


def _get_token():
    """Charge le token une seule fois par process (il ne change pas en cours
    d'exécution, et push/pull peuvent faire des centaines d'appels API)."""
    global _TOKEN
    if _TOKEN is None:
        _TOKEN = load_token()
    return _TOKEN


def _refresh_token(epoch_seen):
    """Rafraîchissement interactif du token sur 401. `push`/`pull` tournent
    en parallèle (plusieurs threads) : si le token expire en cours de route,
    plusieurs appels peuvent 401 en même temps — un seul déclenche le prompt
    (verrou + comparaison d'epoch), les autres attendent puis réessaient avec
    le token déjà rafraîchi sans re-demander à l'utilisateur."""
    global _TOKEN, _TOKEN_EPOCH
    with _REFRESH_LOCK:
        if _TOKEN_EPOCH != epoch_seen:
            return True  # déjà rafraîchi par un autre thread pendant l'attente du verrou
        try:
            if env.get_auth_strategy() == "chrome_keychain":
                try:
                    import proweb_auth
                    payload = proweb_auth.fetch_token()
                    if payload.get("bearer") and payload.get("bearer") != (_TOKEN or {}).get("bearer"):
                        write_json(TOKEN_PATH, payload)
                        _TOKEN = payload
                        _TOKEN_EPOCH += 1
                        return True
                except Exception:
                    pass
                if not sys.stdin.isatty():
                    return False
                input(f"\n⏸  Token expiré. Recharge {BASE_URL} dans Chrome (déconnecte-toi puis "
                      f"reconnecte-toi si le simple rechargement ne suffit pas), puis appuie sur "
                      f"Entrée pour réessayer (Ctrl+C pour abandonner)… ")
                try:
                    import proweb_auth
                    payload = proweb_auth.fetch_token()
                except Exception as e:
                    print(f"  ⚠️  rafraîchissement automatique impossible ({e}) — "
                          f"relance '{env.PY_CMD} ppl.py login' toi-même (voir README).")
                    return False
                write_json(TOKEN_PATH, payload)
                _TOKEN = payload
                _TOKEN_EPOCH += 1
                return True
            else:
                if not sys.stdin.isatty():
                    return False
                input(f"\n⏸  Token expiré. Lance '{env.PY_CMD} ppl.py login' dans un terminal séparé pour "
                      f"renouveler ton token, puis appuie sur Entrée pour continuer (Ctrl+C pour abandonner)… ")
                tok = load_token()
                if tok and tok.get("bearer"):
                    _TOKEN = tok
                    _TOKEN_EPOCH += 1
                    return True
                print("  ❌ Aucun token valide trouvé dans token.json après Entrée.")
                return False
        except (EOFError, KeyboardInterrupt):
            print()
            return False


def api(method, path, partner=None, body=None, soft=False, _retried=False):
    """Appelle l'API Pro Web. `partner` = x-partner-id (requis par la plupart
    des endpoints /api/websites, /api/objects/* — PAS par /api/auth/user).
    `soft=True` renvoie None sur échec HTTP au lieu de terminer le process —
    réservé aux appels tolérants (ex. scan de partenaires dans resolve())."""
    epoch = _TOKEN_EPOCH
    tok = _get_token()
    cookies = {"userCredential": tok["bearer"]}
    if tok.get("g_state_cookie"):
        cookies["g_state"] = tok["g_state_cookie"]
    if tok.get("auth_cookie"):
        cookies["auth"] = tok["auth_cookie"]
    if partner is not None:
        cookies["partner"] = str(partner)
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {tok['bearer']}",
        "origin": BASE_URL,
        "referer": f"{BASE_URL}/",
        "user-agent": "Mozilla/5.0 ppl_static.py",
    }
    if partner is not None:
        headers["x-partner-id"] = str(partner)
    url = BASE_URL.rstrip("/") + "/" + path.lstrip("/")
    r = requests.request(method, url, headers=headers, cookies=cookies, json=body, timeout=30)
    if r.status_code == 401:
        if soft:
            return None
        if not _retried and _refresh_token(epoch):
            return api(method, path, partner, body, soft=soft, _retried=True)
        die(f"401 sur {url} — token toujours expiré. Relance : {env.PY_CMD} ppl.py login")
    if not r.ok:
        if soft:
            return None
        die(f"{method} {url} → HTTP {r.status_code}\n{r.text[:500]}")
    if not r.content:
        return None
    try:
        return r.json()
    except ValueError:
        return r.text


def _items(data):
    if isinstance(data, dict):
        return data.get("data", data)
    return data or []


def load_cache():
    return read_json(CACHE) if CACHE.exists() else {}


def save_cache(c):
    write_json(CACHE, c)


def norm_domain(d):
    return d.strip().lower().replace("https://", "").replace("http://", "").rstrip("/")


def site_dir(info):
    return SITES / (info["domain"] or info["websiteId"])


def site_label(info):
    return info["domain"] or info["websiteId"]


def my_partners():
    """Les partenaires accessibles à TON compte (endpoint /api/auth/user, ne
    nécessite pas de x-partner-id — c'est ta propre identité)."""
    data = api("POST", "/api/auth/user")
    partners = (data or {}).get("data", {}).get("partners") or []
    if not partners:
        die("ton compte n'est rattaché à aucun partenaire Pro Web (réponse /api/auth/user vide).")
    return partners


def _website_info(w, partner):
    return {
        "domain": (w.get("domainName") or "").lower(),
        "websiteId": w.get("_id"),
        "partner": partner,
        "type": w.get("type"),
        "url": w.get("url"),
    }


def resolve(domain, refresh=False, require=True):
    """Trouve le website record d'un domaine, en cherchant uniquement parmi
    LES PARTENAIRES DE TON PROPRE COMPTE (jamais un scan global)."""
    domain = norm_domain(domain)
    cache = load_cache()
    if not refresh and domain in cache:
        cached = cache[domain]
        # Contrôle Fail-Closed : l'entrée en cache doit appartenir aux organisations autorisées du compte courant
        if cached.get("partner") in my_partners():
            return cached
    exact = None
    fallback = None
    for pid in my_partners():
        data = api("GET", "/api/websites", pid, soft=True)
        if not data:
            continue
        for w in _items(data):
            w_dom = norm_domain(w.get("domainName") or "")
            if w_dom == domain:
                exact = _website_info(w, pid)
                break
            elif w_dom.removeprefix("www.") == domain.removeprefix("www."):
                if not fallback:
                    fallback = _website_info(w, pid)
        if exact:
            break
    matched = exact or fallback
    if matched:
        cache[domain] = matched
        if matched.get("domain"):
            cache[norm_domain(matched["domain"])] = matched
        save_cache(cache)
        return matched
    if require:
        die(f"'{domain}' introuvable parmi les sites de ton compte. Vérifie le domaine, "
            f"ou utilise --website-id/--partner directement (visibles dans l'URL Pro Web : "
            f"#/websites/<ID>/objects/).")
    return None


def resolve_by_id(website_id, partner):
    """Bypass 'resolve' : website-id + partner donnés directement (pas besoin
    de connaître le domaine). Alimente aussi le cache domaine→info si le site
    a un domaine, pour que 'resolve <domaine>' en profite ensuite."""
    data = api("GET", "/api/websites", partner)
    for w in _items(data):
        if w.get("_id") == website_id:
            info = _website_info(w, partner)
            if info["domain"]:
                cache = load_cache()
                cache[info["domain"]] = info
                save_cache(cache)
            return info
    die(f"websiteId '{website_id}' introuvable sous le partenaire {partner}.")


def get_info(args, fresh=False):
    """`fresh=True` force un resolve() non caché — à utiliser avant toute
    mutation (push/add/rm/set-home) : check_static() ne doit pas se fier à un
    `type` périmé si le site a changé de nature côté Pro Web depuis le
    dernier resolve mis en cache."""
    if getattr(args, "website_id", None):
        if not args.partner:
            die("--website-id nécessite --partner (visible dans l'URL Pro Web).")
        return resolve_by_id(args.website_id, args.partner)
    if not getattr(args, "domain", None):
        die("indique un domaine, ou --website-id/--partner.")
    return resolve(args.domain, refresh=fresh)


def base_url(info):
    return (info.get("url") or f"https://{info['domain']}").rstrip("/")


def list_objects(info):
    data = api("GET", f"/api/objects/list/{info['websiteId']}", info["partner"])
    return _items(data)


ALLOWED_NON_STATIC_PREFIXES = ("pages/", "leads/", "cadeau/")


def is_static_site(info):
    """Vérifie si le site est de type STATIC (ex: doc.propulse-lab.com, sites vitrines)."""
    return (info.get("type") or "").upper() == "STATIC"


def is_allowed_key(key):
    """Vérifie si la clé commence par l'un des préfixes autorisés pour les sites non-STATIC."""
    clean = key.lstrip("/")
    return any(clean.startswith(p) for p in ALLOWED_NON_STATIC_PREFIXES)


def check_key_allowed(info, key):
    """Garde-fou : sur les sites non-STATIC, seules les pages /pages/, /leads/, /cadeau/ sont autorisées."""
    if is_static_site(info):
        return True
    if not is_allowed_key(key):
        die(f"❌ [VETO DOCTRINE GLOBALE] Site non-STATIC ({info.get('type')}) :\n"
            f"   Le chemin '{key}' est interdit.\n"
            f"   SEULES les pages commençant par /pages/, /leads/ ou /cadeau/ sont autorisées à la modification.")
    return True


def check_static(info, key=None):
    """Garde-fou de type de site.
    - STATIC : accès complet à l'ensemble des fichiers (ex: doc.propulse-lab.com).
    - Non-STATIC (WORDPRESS, BLOG...) : restreint STRICTEMENT aux chemins /pages/, /leads/, /cadeau/.
    """
    if is_static_site(info):
        return True
    if key is not None:
        check_key_allowed(info, key)
    return True


def check_html_integrity(key, content):
    """Garde-fou mécanique anti-troncature pour les pages HTML (Fail-Closed)."""
    if not key.lower().endswith(".html"):
        return
    text = content.decode("utf-8", errors="ignore") if isinstance(content, (bytes, bytearray)) else str(content)
    # 1. Troncature par IA (balise fermante manquante)
    if "</html>" not in text.lower():
        die(f"❌ [SÉCURITÉ PRODUCTION] Le fichier HTML '{key}' est incomplet ou tronqué "
            f"(balise </html> absente). Déploiement bloqué pour protéger la production.")
    # 2. Placeholders de troncature classiques de LLM
    suspicious_placeholders = [
        "<!-- rest of code unchanged",
        "<!-- rest of the code unchanged",
        "<!-- remaining code unchanged",
        "<!-- same as before",
        "<!-- reste du code inchang",
        "<!-- suite du code inchang",
        "/* rest of code unchanged",
        "// rest of code unchanged",
    ]
    for placeholder in suspicious_placeholders:
        if placeholder in text.lower():
            die(f"❌ [SÉCURITÉ PRODUCTION] Le fichier HTML '{key}' contient un commentaire de troncature "
                f"IA ('{placeholder}'). Le fichier doit être fourni complet. Déploiement bloqué.")


def deploy_file(info, key, content, existing_record=None, extra_aliases=None):
    """signed-url -> PUT S3 -> upsert (préserve type=PAGE et synchronise les alias clean-URL)."""
    if len(content) > MAX_FILE_SIZE:
        die(f"Fichier '{key}' trop lourd ({len(content) / 1_000_000:.1f} Mo > 20 Mo max autorisé sur STATIC).")

    # Garde-fou mécanique anti-troncature pour les pages HTML (défense en profondeur)
    check_html_integrity(key, content)

    ct, subtype = content_meta(key, content, existing_record)
    wid, partner = info["websiteId"], info["partner"]

    targets = [key] + [a for a in (extra_aliases or []) if a != key]
    for target_key in targets:
        su = api("POST", "/api/objects/signed-url", partner,
                 {"websiteId": wid, "contentType": ct, "fileName": os.path.basename(target_key), "key": target_key})
        signed = su.get("data") if isinstance(su, dict) else su
        if not signed:
            die(f"pas de signed-url pour {target_key}: {su}")
        # ⚠️ le PUT S3 signé n'accepte QUE Content-Type en header (le reste est
        # déjà signé dans la query) — ajouter un header type x-amz-acl → 403.
        r = requests.put(signed, data=content, headers={"Content-Type": ct}, timeout=180)
        if not r.ok:
            die(f"PUT S3 {target_key} → HTTP {r.status_code} {r.text[:300]}")

        if existing_record and target_key == key and existing_record.get("type") == "PAGE":
            upsert_body = {
                "websiteId": wid,
                "key": target_key,
                "type": "PAGE",
                "subtype": existing_record.get("subtype"),
                "folder": existing_record.get("folder", "pages"),
                "slug": existing_record.get("slug") or os.path.basename(target_key),
                "originalFileName": existing_record.get("originalFileName") or os.path.basename(target_key),
                "originalUrl": existing_record.get("originalUrl"),
                "leadpageEditUrl": existing_record.get("leadpageEditUrl"),
                "hasIndexing": existing_record.get("hasIndexing", False),
                "emailOwner": existing_record.get("emailOwner"),
                "emailLastUser": existing_record.get("emailLastUser"),
            }
            upsert_body = {k: v for k, v in upsert_body.items() if v is not None}
        else:
            upsert_body = {
                "websiteId": wid,
                "originalFileName": (existing_record.get("originalFileName") if (existing_record and target_key == key) else None) or os.path.basename(target_key),
                "subtype": subtype,
                "type": "DOCUMENT",
                "key": target_key,
            }
            if "/" in target_key:
                upsert_body["folder"] = target_key.rsplit("/", 1)[0]
                upsert_body["slug"] = target_key.rsplit("/", 1)[1]
        api("POST", "/api/objects/upsert", partner, upsert_body)


# --- commandes -------------------------------------------------------------
def cmd_resolve(args):
    info = resolve(args.domain, refresh=args.refresh)
    print(to_json(info))


def cmd_ls(args):
    info = get_info(args)
    objs = list_objects(info)
    if not is_static_site(info):
        total_count = len(objs)
        objs = [o for o in objs if is_allowed_key(o.get("key", ""))]
        print(f"🧩 Site non-STATIC ({info.get('type')}) : affichage filtré sur /pages/, /leads/ et /cadeau/ ({len(objs)}/{total_count} objets)")
    print(f"{site_label(info)} — websiteId {info['websiteId']} · "
          f"partner {info['partner']} · type {info['type']} · {len(objs)} objets")
    for o in sorted(objs, key=lambda x: x["key"]):
        home = "  ← ACCUEIL" if o["key"] == "index.html" else ""
        print(f"  {o['key']:<45} {o.get('subtype', ''):<16}{home}")


def cmd_pull(args):
    info = get_info(args)
    check_static(info)
    objs = list_objects(info)
    if not is_static_site(info):
        total_count = len(objs)
        objs = [o for o in objs if is_allowed_key(o.get("key", ""))]
        print(f"🧩 Site non-STATIC ({info.get('type')}) : pull restreint aux chemins /pages/, /leads/ et /cadeau/ ({len(objs)}/{total_count} objets retenus).")
        if not objs:
            print("ℹ️  Aucune page trouvée sous /pages/, /leads/ ou /cadeau/ sur ce site.")
    elif not getattr(args, "full", False):
        before = len(objs)
        objs = [o for o in objs if not o.get("key", "").startswith(("wp-content/uploads/", "wp-includes/"))]
        if len(objs) < before:
            print(f"ℹ️  {before - len(objs)} assets statiques WordPress (wp-content/uploads/, wp-includes/) ignorés par défaut (utilisez --full pour tout télécharger).")

    # Filtrer les alias S3 Clean-URL redondants (<slug>, <slug>/index, <slug>/index/index.html)
    # qui entreraient en collision fichier/dossier sur le système de fichiers local.
    all_keys = {o["key"] for o in objs}
    clean_url_aliases = {}
    kept_objs = []
    for o in objs:
        k = o["key"]
        if k.endswith("/index/index.html"):
            base_idx = k[:-len("/index/index.html")] + "/index.html"
            base_htm = k[:-len("/index/index.html")] + ".html"
            if base_idx in all_keys or base_htm in all_keys:
                if base_idx in all_keys:
                    clean_url_aliases.setdefault(base_idx, []).append(k)
                if base_htm in all_keys:
                    clean_url_aliases.setdefault(base_htm, []).append(k)
                continue
        if k.endswith("/index"):
            base_idx = k + ".html"
            base_htm = k[:-len("/index")] + ".html"
            if base_idx in all_keys or base_htm in all_keys:
                if base_idx in all_keys:
                    clean_url_aliases.setdefault(base_idx, []).append(k)
                if base_htm in all_keys:
                    clean_url_aliases.setdefault(base_htm, []).append(k)
                continue
        if not k.endswith(".html") and (f"{k}.html" in all_keys or f"{k}/index.html" in all_keys):
            if f"{k}.html" in all_keys:
                clean_url_aliases.setdefault(f"{k}.html", []).append(k)
            if f"{k}/index.html" in all_keys:
                clean_url_aliases.setdefault(f"{k}/index.html", []).append(k)
            continue
        kept_objs.append(o)

    kept_keys = {o["key"] for o in kept_objs}
    prefix_conflicts = {k for k in kept_keys if any(other.startswith(k + "/") for other in kept_keys)}

    # Détection des casses multiples sur dossiers ou clés (systèmes de fichiers insensibles à la casse type APFS/NTFS)
    dir_cases = {}
    for k in kept_keys:
        parts = k.split("/")[:-1]
        for i in range(1, len(parts) + 1):
            d = "/".join(parts[:i])
            dir_cases.setdefault(d.lower(), set()).add(d)
    mixed_dirs = [sorted(v) for v in dir_cases.values() if len(v) > 1]
    if mixed_dirs:
        print(f"ℹ️  {len(mixed_dirs)} dossier(s) en casse mixte détecté(s) sur S3 (normalisé via manifeste au push).")

    sitedir = site_dir(info)
    burl = base_url(info)
    manifest = {
        "domain": info.get("domain"),
        "websiteId": info.get("websiteId"),
        "partnerId": info.get("partner"),
        "url": info.get("url"),
        "objects": {},
        "clean_url_aliases": clean_url_aliases,
    }
    seen_lower_local = {}
    ok = 0

    def fetch(o):
        r = requests.get(f"{burl}/{o['key']}", timeout=60, allow_redirects=False)
        if r.status_code == 301 and r.headers.get("location", "").endswith("/"):
            raise RuntimeError("Redirection 301 vers accueil (objet non trouvé)")
        r.raise_for_status()
        return r.content

    with ThreadPoolExecutor(max_workers=PUSH_WORKERS) as pool:
        futures = {pool.submit(fetch, o): o for o in kept_objs}
        for fut in as_completed(futures):
            o = futures[fut]
            s3_key = o["key"]
            local_key = f"{s3_key}.html" if s3_key in prefix_conflicts else s3_key
            if local_key.lower() in seen_lower_local and seen_lower_local[local_key.lower()] != local_key:
                print(f"  ⚠️  collision de casse sur '{local_key}' vs '{seen_lower_local[local_key.lower()]}' — suffixé localement")
                local_key = f"{local_key}__case_{sha(s3_key.encode())[:6]}"
            seen_lower_local[local_key.lower()] = local_key
            try:
                content = fut.result()
            except Exception as e:
                print(f"  ⚠️  skip {s3_key} ({e})")
                continue
            dest = sitedir / local_key
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
            manifest["objects"][local_key] = {
                "record": o,
                "sha256": sha(content),
                "sha256_lf": sha(content.replace(b"\r\n", b"\n")),
                "s3_key": s3_key,
            }
            ok += 1
            print(f"  ↓ {local_key} ({len(content)} o)")

    write_json(sitedir / MANIFEST, manifest)
    write_site_rules(sitedir, info)
    print(f"\n✅ {ok} fichier(s) → {sitedir}")
    print("→ Ouvre Claude Code à la racine du kit pour éditer sites/<domaine>/, puis :")
    print(f"   python3 ppl_static.py preview {site_label(info)}")
    print(f"   python3 ppl_static.py push {site_label(info)}")


def cmd_preview(args):
    d = SITES / norm_domain(args.domain) if args.domain else Path.cwd()
    if args.domain and not d.exists():
        die(f"pas de miroir local pour {args.domain} — fais 'pull' d'abord.")
    os.chdir(d)
    print(f"Preview {d}\n→ http://localhost:{args.port}   (Ctrl+C pour arrêter)")
    subprocess.run([sys.executable, "-m", "http.server", str(args.port), "--bind", "127.0.0.1"])


def cmd_push(args):
    local_mpath = (SITES / norm_domain(args.domain) / MANIFEST) if getattr(args, "domain", None) else None
    if not getattr(args, "go", False) and local_mpath and local_mpath.exists():
        mdata = read_json(local_mpath)
        cached = load_cache().get(norm_domain(args.domain), {})
        info = {
            "domain": mdata.get("domain") or cached.get("domain") or norm_domain(args.domain),
            "websiteId": mdata.get("websiteId") or cached.get("websiteId"),
            "partner": mdata.get("partnerId") or cached.get("partner"),
            "type": cached.get("type") or "STATIC",
            "url": mdata.get("url") or cached.get("url") or f"https://{norm_domain(args.domain)}",
        }
        check_static(info)
    else:
        info = get_info(args, fresh=True)
        check_static(info)
    sitedir = site_dir(info)
    mpath = sitedir / MANIFEST
    if not mpath.exists():
        die(f"pas de miroir local pour {info['domain']} — fais 'pull' d'abord.")
    manifest = read_json(mpath)
    objects = manifest["objects"]
    clean_url_aliases = manifest.get("clean_url_aliases", {})

    lower_to_manifest = {}
    for mk in objects:
        lower_to_manifest[mk.lower()] = mk

    local = {}
    local_raw = {}
    TEXT_EXTENSIONS = {".html", ".css", ".js", ".json", ".txt", ".svg", ".xml"}
    EXCLUDED_NAMES = {MANIFEST, "RULES.md", "CLAUDE.md", "README.md"}
    for p in sitedir.rglob("*"):
        rel = p.relative_to(sitedir)
        if not p.is_file() or p.name in EXCLUDED_NAMES or p.suffix.lower() == ".md":
            continue
        if any(part.startswith(".") for part in rel.parts):
            continue
        rel_str = "/".join(rel.parts)
        canonical_key = lower_to_manifest.get(rel_str.lower(), rel_str)
        raw_data = p.read_bytes()
        local_raw[canonical_key] = raw_data
        data = raw_data
        # Normalisation automatique des retours chariot Windows (CRLF -> LF) pour fiabiliser le hash SHA-256
        if p.suffix.lower() in TEXT_EXTENSIONS and b"\r\n" in data:
            data = data.replace(b"\r\n", b"\n")
        local[canonical_key] = data

    def is_changed(k):
        rec_entry = objects[k]
        if sha(local_raw[k]) == rec_entry.get("sha256"):
            return False
        expected_lf = rec_entry.get("sha256_lf") or rec_entry.get("sha256")
        if sha(local[k]) == expected_lf:
            return False
        return True

    new = [k for k in local if k not in objects]
    changed = [k for k in local if k in objects and is_changed(k)]
    deleted = [k for k in objects if k not in local]

    print(f"Site : {info['domain']} · websiteId {info['websiteId']} · partner {info['partner']}")
    if not new and not changed:
        print("Rien à publier (aucun fichier modifié).")
        if deleted:
            print("Absents en local (non touchés en prod) :", ", ".join(deleted))
        return
    print("À publier :")
    for k in sorted(new):
        print(f"  + {k}  (nouveau)")
    for k in sorted(changed):
        print(f"  ~ {k}  (modifié)")
    if deleted:
        print("Absents en local (utilise 'rm <domaine> <key>' pour les retirer de la prod) :")
        for k in sorted(deleted):
            print(f"  - {k}")

    to_publish = new + changed

    # Contrôles de validation pré-vol (taille, formats interdits, périmètre doctrine et intégrité HTML) dès le dry-run
    for k in to_publish:
        if not is_static_site(info):
            check_key_allowed(info, k)
        if len(local[k]) > MAX_FILE_SIZE:
            die(f"Fichier '{k}' trop lourd ({len(local[k]) / 1_000_000:.1f} Mo > 20 Mo max autorisé).")
        ext = Path(k).suffix.lower()
        if ext in FORBIDDEN_VIDEO_EXTS:
            die(f"Fichier vidéo non autorisé ({k}). Les vidéos doivent être hébergées sur Pro-Vidéo.")
        check_html_integrity(k, local[k])

    # Alerte de cohérence sur les paires de pages HTML doublons (ex: mentions-legales.html vs mentions-legales/index.html)
    for k in to_publish:
        if k.endswith("/index.html") and k != "index.html":
            slug_html = k[:-len("/index.html")] + ".html"
            if slug_html in objects and slug_html not in to_publish:
                print(f"⚠️  [DOUBLE ARBORESCENCE] '{k}' est modifié mais son fichier jumeau '{slug_html}' ne l'est pas.")
                print(f"   Pensez à reporter la même modification sur '{slug_html}' pour éviter tout déphasage.")
        elif k.endswith(".html") and not k.endswith("/index.html") and k != "index.html":
            folder_index = k[:-len(".html")] + "/index.html"
            if folder_index in objects and folder_index not in to_publish:
                print(f"⚠️  [DOUBLE ARBORESCENCE] '{k}' est modifié mais son fichier jumeau '{folder_index}' ne l'est pas.")
                print(f"   Pensez à reporter la même modification sur '{folder_index}' pour éviter tout déphasage.")

    # Contrôle de dérive (drift detection) avant toute publication (exécuté dès le dry-run)
    def check_drift_one(key):
        s3_key = objects[key].get("s3_key") or key
        u = f"{base_url(info)}/{s3_key}"
        try:
            resp = requests.get(u, timeout=60, allow_redirects=False)
            if resp.status_code == 200:
                remote_bytes = resp.content
                remote_sha = sha(remote_bytes)
                remote_lf_sha = sha(remote_bytes.replace(b"\r\n", b"\n"))
                expected_sha = objects[key].get("sha256")
                expected_lf_sha = objects[key].get("sha256_lf") or expected_sha
                local_sha = sha(local[key])
                if expected_sha and remote_sha != expected_sha and remote_lf_sha != expected_lf_sha:
                    if remote_sha == local_sha or remote_lf_sha == local_sha:
                        # Le contenu distant correspond déjà à notre version locale (ex: échec d'upsert précédent)
                        return None
                    return (
                        f"[CONFLIT DE CONCURRENCE] L'objet distant '{s3_key}' a été modifié en production depuis votre dernier pull.\n"
                        f"SHA distant: {remote_sha[:12]}... != SHA manifeste pull: {expected_sha[:12]}...\n"
                        f"Re-pull requis avant publication."
                    )
            elif resp.status_code in (404, 301):
                return f"[CONFLIT DE CONCURRENCE] L'objet distant '{s3_key}' a été supprimé en production depuis votre dernier pull (statut HTTP {resp.status_code}). Re-pull requis."
            elif resp.status_code != 200:
                return f"[CONTRÔLE DE DÉRIVE IMPOSSIBLE] '{s3_key}' a renvoyé HTTP {resp.status_code} — re-pull ou relance."
        except requests.RequestException as e:
            return f"[CONTRÔLE DE DÉRIVE ÉCHOUÉ] Erreur réseau lors de la vérification de '{s3_key}' ({e}) — relancez."
        return None

    if changed:
        with ThreadPoolExecutor(max_workers=PUSH_WORKERS) as pool:
            for err in pool.map(check_drift_one, changed):
                if err:
                    die(err)

    # Conflit sur les nouveaux fichiers (ne doivent pas déjà exister en prod avec un contenu divergent)
    if new and getattr(args, "go", False):
        remote_existing_keys = {o.get("key") for o in list_objects(info)}
    else:
        remote_existing_keys = set(objects.keys())
    for key in new:
        u = f"{base_url(info)}/{key}"
        try:
            resp = requests.get(u, timeout=30, allow_redirects=False)
            if resp.status_code == 200:
                remote_sha = sha(resp.content)
                if remote_sha == sha(local[key]):
                    # Déjà téléversé lors d'une tentative précédente interrompue
                    pass
                else:
                    die(f"[CONFLIT DE CRÉATION] La clé '{key}' déclarée comme nouvelle existe déjà en production — faites un pull pour la récupérer.")
            elif resp.status_code == 500 and key not in remote_existing_keys:
                print(f"  ℹ️  Note: '{key}' absent de list_objects (Edge HTTP 500 ignoré).")
            elif resp.status_code not in (404, 301):
                die(f"[CONTRÔLE DE DÉRIVE IMPOSSIBLE] Nouveau fichier '{key}' a renvoyé HTTP {resp.status_code} (attendu: 404/301).")
        except requests.RequestException as e:
            die(f"[CONTRÔLE DE DÉRIVE ÉCHOUÉ] Erreur réseau lors de la vérification du nouveau fichier '{key}' ({e}) — relancez.")

    if not gate(args, "Ajoute --go pour publier en PROD.",
                f"Publier {len(to_publish)} fichier(s) en PROD ?"):
        return

    failed = []
    claimed_aliases = set()

    def build_deploy_args(k):
        s3_key = objects.get(k, {}).get("s3_key") or k
        rec = objects.get(k, {}).get("record")
        aliases = []
        for a in clean_url_aliases.get(k, []):
            if a not in claimed_aliases:
                claimed_aliases.add(a)
                aliases.append(a)
        return s3_key, rec, aliases

    deploy_plan = {k: build_deploy_args(k) for k in to_publish}

    with ThreadPoolExecutor(max_workers=PUSH_WORKERS) as pool:
        futures = {
            pool.submit(deploy_file, info, deploy_plan[key][0], local[key], deploy_plan[key][1], deploy_plan[key][2]): key
            for key in to_publish
        }
        for fut in as_completed(futures):
            key = futures[fut]
            s3_key, rec, _ = deploy_plan[key]
            try:
                fut.result()
            except SystemExit as e:
                failed.append(key)
                print(f"  ❌ {key} — {e}")
                continue
            objects[key] = {
                "record": rec or {"key": s3_key},
                "sha256": sha(local[key]),
                "sha256_lf": sha(local[key].replace(b"\r\n", b"\n")),
                "s3_key": s3_key,
            }
            # Persistance immédiate : si un fichier suivant échoue, on ne perd
            # pas la trace de ceux déjà publiés (pas de republication inutile).
            write_json(mpath, manifest)
            print(f"  ✅ {key}")

    if failed:
        die(f"{len(failed)} fichier(s) en échec sur {len(to_publish)} : {', '.join(failed)}\n"
            f"   Les autres sont déjà publiés (manifest à jour) — relance 'push' pour ne "
            f"réessayer que ceux en échec.")
    print("\n✅ Publié. L'upsert déclenche l'invalidation CloudFront → propagation immédiate.")
    for key in to_publish:
        if key.endswith("index.html"):
            folder = os.path.dirname(key)
            folder_path = f"/{folder}/" if folder else "/"
            print(f"   ⚠️ Attention : '{key}' a été mis à jour. CloudFront purge automatiquement '/{key}', mais la forme dossier '{folder_path}' peut nécessiter une invalidation manuelle si l'affichage ne s'actualise pas immédiatement.")


def cmd_add(args):
    info = get_info(args, fresh=True)
    check_static(info)
    src = Path(args.file)
    if not src.exists():
        die(f"fichier introuvable : {src}")
    key = args.key or src.name
    check_key_allowed(info, key)
    content = src.read_bytes()
    ct, _ = content_meta(key, content)
    print(f"add : {src}  →  {info['domain']} / {key}  ({len(content)} o, {ct})")
    if not gate(args, "Ajoute --go pour publier.", "Publier en PROD ?"):
        return
    deploy_file(info, key, content)
    print(f"✅ publié : {base_url(info)}/{key}")
    if key.endswith("index.html"):
        folder = os.path.dirname(key)
        folder_path = f"/{folder}/" if folder else "/"
        print(f"   ⚠️ Attention : '{key}' a été mis à jour. CloudFront purge automatiquement '/{key}', mais la forme dossier '{folder_path}' peut nécessiter une invalidation manuelle si l'affichage ne s'actualise pas immédiatement.")


def cmd_rm(args):
    info = get_info(args, fresh=True)
    check_static(info)
    check_key_allowed(info, args.key)
    rec = next((o for o in list_objects(info) if o["key"] == args.key), None)
    if not rec:
        die(f"objet '{args.key}' introuvable sur {info['domain']}")
    print(f"rm : {info['domain']} / {args.key}  (id {rec['_id']})")
    if not gate(args, "Ajoute --go pour supprimer.", "SUPPRIMER en PROD ?"):
        return
    api("DELETE", "/api/objects", info["partner"], {"s3Object": rec})
    print("✅ supprimé.")


def cmd_sethome(args):
    info = get_info(args, fresh=True)
    check_static(info)
    if not is_static_site(info):
        die(f"❌ Impossible de redéfinir l'accueil sur un site non-STATIC ({info.get('type')}).")
    key = args.key
    localf = site_dir(info) / key
    if localf.exists():
        content = localf.read_bytes()
        src = f"local ({localf})"
    else:
        r = requests.get(f"{base_url(info)}/{key}", timeout=60, allow_redirects=False)
        if r.status_code == 301 and r.headers.get("location", "").endswith("/"):
            die(f"clé '{key}' non trouvée en prod (redirection 301 vers accueil).")
        if not r.ok:
            die(f"impossible de récupérer {key} depuis la prod → HTTP {r.status_code}")
        content = r.content
        src = f"prod ({base_url(info)}/{key})"
    print(f"set-home : {key} → index.html sur {info['domain']}  (source : {src})")
    if not gate(args, "Ajoute --go pour publier.", "Écraser l'accueil (index.html) en PROD ?"):
        return
    deploy_file(info, "index.html", content)
    print("✅ accueil défini. ⚠️ pense à l'invalidation manuelle de '/' (voir README).")


def cmd_doctor(args):
    """Vérification diagnostique complète de la machine hôte et du connecteur."""
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                   PROPULSE LAB · PRO WEB STATIC CONNECTOR                  ║")
    print("╠════════════════════════════════════════════════════════════════════════════╣")
    print(f"║ 💻 OS Hôte        : {env.OS_NAME:<54} ║")
    print(f"║ 🏷️ Machine        : {env.HOSTNAME:<54} ║")
    print(f"║ 🐍 Lanceur Python : {env.PY_CMD:<54} ║")
    strat = "macOS Chrome Keychain (auto)" if env.get_auth_strategy() == "chrome_keychain" else "Mode Guidé / Token collé"
    print(f"║ 🔑 Stratégie Auth : {strat:<54} ║")

    st = env.check_token_status()
    t_status = "Inexistant"
    if st["exists"]:
        if st["valid"]:
            rem_m = int((st["remaining_seconds"] or 0) / 60)
            t_status = f"Valide ({rem_m} min restantes · {st['email'] or 'connecté'})"
        else:
            t_status = "Expiré (rafraîchissement requis)"
    print(f"║ 📂 Token Local    : {t_status:<54} ║")

    # Test réseau rapide vers l'API
    net_status = "Vérification en cours..."
    try:
        r = requests.head(BASE_URL, timeout=4)
        net_status = f"Accessible (HTTP {r.status_code})"
    except Exception as e:
        net_status = f"Inaccessible ({str(e)[:30]})"
    print(f"║ 🌐 API Pro Web    : {net_status:<54} ║")

    # Test TTY interactif
    tty_ok = sys.stdin.isatty()
    tty_desc = "Interactif (OK pour --go)" if tty_ok else "Non-interactif (Bash/Agent : dry-run seul)"
    print(f"║ 🖥️ Terminal TTY   : {tty_desc:<54} ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝\n")

    if env.OS_FAMILY == "windows":
        print("💡 [CONSEIL WINDOWS] : Veillez à ce que votre éditeur et Git conservent les fins de ligne")
        print("   en LF (et non CRLF) pour ne pas altérer les calculs de hash SHA-256 lors des push.\n")

    if not st["exists"] or st["expired"]:
        print(f"👉 Action requise : lancez '{env.PY_CMD} ppl.py login' pour initialiser votre session Pro Web.\n")
    else:
        print("✅ Connecteur opérationnel et prêt à l'emploi.\n")


def build_rules(clean_domain: str, partner_id: int, site_type: str = "STATIC", duplicate_pairs: list = None) -> str:
    """Génère le contenu de RULES.md / CLAUDE.md pour un site statique ou les pages autorisées d'un site non-STATIC."""
    dup_rules = ""
    if duplicate_pairs:
        dup_rules = (
            f"\n### ⚠️ Règle Double Arborescence HTML ({len(duplicate_pairs)} pages détectées) :\n"
            "Les sous-pages suivantes existent à la fois sous forme de dossier et de fichier .html :\n"
            + "\n".join(f"  - /{p}/index.html ET /{p}.html" for p in duplicate_pairs)
            + "\n👉 Si tu modifies l'une de ces pages, mets TOUJOURS à jour les deux fichiers de façon identique !\n"
        )

    if site_type == "STATIC":
        arch_desc = "Site **statique pur** (HTML5, CSS, JS, images). Zéro WordPress, zéro CMS."
        scope_section = ""
    else:
        arch_desc = f"Site **{site_type}** — Gestion restreinte aux pages `/pages/`, `/leads/` et `/cadeau/`."
        scope_section = """
### 🛑 RÈGLE ABSOLUE DE PÉRIMÈTRE (SITE NON-STATIC)
- **SEULES les pages commençant par `/pages/`, `/leads/` ou `/cadeau/` sont vibecodables.**
- Toute création ou modification d'un fichier en dehors de ces trois dossiers est strictement bloquée par le CLI pour protéger le Core WordPress.
"""

    return f"""# Consignes Assistant IA (Grok / ChatGPT / Claude / Cursor) — {clean_domain}

> **Site** : {clean_domain} (Partner ID: {partner_id})
> **Architecture** : {arch_desc}

---

## 🛑 RÈGLE D'OR POUR L'IA (GROK / CHATGPT) : ZÉRO TRONCATURE

Quand tu génères du code HTML, CSS ou JS pour ce site :
1. **INTERDICTION FORMELLE DE TRONQUER LE CODE** avec des commentaires du type :
   - `<!-- rest of code unchanged -->`
   - `<!-- reste du code inchangé -->`
   - `<!-- same as before -->`
   - `/* rest of code unchanged */`
2. **FOURNIR LE FICHIER COMPLET** : Tout fichier HTML doit être fourni intégralement, de `<!DOCTYPE html>` jusqu'à `</html>`.
   L'utilisateur travaille en remplacement complet dans son éditeur local. Un fichier tronqué détruirait la mise en page en production.

---
{scope_section}
## 🔄 Workflow Autonome pour l'Agent IA (Grok / Cursor / Claude)

1. **Édition du Code ou Remplacement Multi-Fichiers** :
   - Modifie directement les fichiers locaux (ex: `index.html`) en fournissant toujours le code HTML complet.
   - Pour remplacer une URL ou un texte sur toutes les pages du site d'un coup (sans toucher aux PDF ni aux images) :
     `python3 ppl.py static replace {clean_domain} <ancien_texte> <nouveau_texte> --go`
2. **Contrôle Pré-vol (Dry-Run)** :
   - Lance le contrôle pré-vol : `python3 ppl.py static push {clean_domain}`
   - Présente le récapitulatif des fichiers modifiés à l'utilisateur dans le chat.
3. **Publication en Production (Sur Accord de l'Utilisateur)** :
   - Dès que l'utilisateur valide dans le chat (ex: "go", "publie", "oui"), exécute :
     `python3 ppl.py static push {clean_domain} --go`
   - L'utilisateur tape OUI pour confirmer la mise en production.

---

## 5 Règles Techniques Essentielles

### 1. Chemins d'Assets Statiques
- Les images et styles sont servis depuis la racine : `/assets/images/...`, `/assets/css/...`.
- Ne convertis jamais ces chemins en relatifs. Utilise `preview` pour tester en local.
{dup_rules}
### 2. Formats Autorisés & Interdiction Vidéo
- Formats autorisés : HTML, CSS, JS, JSON, images WebP/PNG/JPG/SVG, PDF.
- **Vidéos strictement interdites** sur STATIC : elles doivent être hébergées sur la plateforme Pro Video.
- Taille max : 20 Mo par fichier.

### 3. Navigation & Liens Internes
- Liens internes toujours avec slash final : `href="/"`, `href="/<slug>/"`.

### 4. Sécurité & Approbation Chat
- L'agent exécute les commandes à la place de l'utilisateur.
- L'agent ne doit lancer `--go` qu'après approbation explicite de l'utilisateur dans la conversation chat.
"""


def write_site_rules(sitedir: Path, info: dict) -> None:
    """Calcule les paires doublons récursivement et écrit RULES.md, CLAUDE.md et .claude/settings.json."""
    if not sitedir.exists():
        return
    clean_domain = info.get("domain") or sitedir.name
    partner_id = info.get("partner") or 0
    site_type = info.get("type") or "STATIC"

    duplicate_pairs = []
    for idx in sorted(sitedir.rglob("index.html")):
        rel_dir = idx.parent.relative_to(sitedir)
        if not rel_dir.parts or any(part.startswith(".") for part in rel_dir.parts):
            continue
        rel_slug = "/".join(rel_dir.parts)
        if (sitedir / f"{rel_slug}.html").exists():
            duplicate_pairs.append(rel_slug)

    rules_content = build_rules(clean_domain, partner_id, site_type, duplicate_pairs)
    (sitedir / "RULES.md").write_text(rules_content, encoding="utf-8")
    (sitedir / "CLAUDE.md").write_text(rules_content, encoding="utf-8")

    claude_dir = sitedir / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    settings_path = claude_dir / "settings.json"
    repo_settings = BASE / ".claude" / "settings.json"
    if repo_settings.exists():
        settings_path.write_text(repo_settings.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        settings_path.write_text(json.dumps({
            "permissions": {
                "ask": [
                    "Bash(*--go*)", "Bash(*--g*)"
                ],
                "deny": [
                    "Bash(script *)", "Bash(*xargs*)", "Bash(*expect*)", "Bash(*unbuffer*)", "Bash(*tmux*)",
                    "Read(~/.pro-web-static/**)", "Bash(*token.json*)", "Bash(*.pro-web-static*)",
                    "Bash(curl*pro-web.propulse-lab.com*)", "Bash(python*-c*)",
                    "Edit(*.py)", "Edit(**/*.py)", "Write(*.py)", "Write(**/*.py)",
                    "Edit(**/*.sh)", "Write(**/*.sh)", "Bash(*.sh*)", "Bash(perl*)",
                    "Bash(node*-e*)", "Bash(ruby*)", "Edit(.claude/**)", "Write(.claude/**)"
                ]
            }
        }, indent=2), encoding="utf-8")


def cmd_replace(args):
    """Remplace une chaîne dans tous les fichiers texte/HTML du site local (multi-OS, ignore PDF/images)."""
    info = get_info(args)
    check_static(info)
    sitedir = site_dir(info)
    mpath = sitedir / MANIFEST
    if not mpath.exists():
        die(f"pas de miroir local pour {info['domain']} — fais 'pull' d'abord.")
    if not args.old:
        die("la chaîne à rechercher (<old>) ne peut pas être vide.")

    old_bytes = args.old.encode("utf-8")
    new_bytes = args.new.encode("utf-8")
    EXCLUDED_NAMES = {MANIFEST, "RULES.md", "CLAUDE.md", "README.md"}
    BINARY_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2", ".ttf", ".eot", ".zip"}

    matches = []
    for p in sorted(sitedir.rglob("*")):
        rel = p.relative_to(sitedir)
        if not p.is_file() or p.name in EXCLUDED_NAMES or p.suffix.lower() == ".md":
            continue
        if any(part.startswith(".") for part in rel.parts):
            continue
        if p.suffix.lower() in BINARY_SUFFIXES:
            continue
        raw = p.read_bytes()
        if raw.startswith((b"%PDF-", b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff", b"GIF8", b"RIFF")):
            continue
        count = raw.count(old_bytes)
        if count > 0:
            matches.append((p, "/".join(rel.parts), count, raw))

    if not matches:
        print(f"Aucune occurrence de '{args.old}' trouvée dans {sitedir}.")
        return

    total_occ = sum(c for _, _, c, _ in matches)
    print(f"Site : {info['domain']} — {total_occ} occurrence(s) dans {len(matches)} fichier(s) :")
    for _, rel_str, c, _ in matches[:25]:
        print(f"  ~ {rel_str} ({c}x)")
    if len(matches) > 25:
        print(f"  ... et {len(matches) - 25} autre(s) fichier(s).")

    if not gate(args, "Ajoute --go pour appliquer le remplacement sur les fichiers locaux.",
                f"Remplacer '{args.old}' par '{args.new}' dans {len(matches)} fichier(s) ?"):
        return

    for p, _, _, raw in matches:
        p.write_bytes(raw.replace(old_bytes, new_bytes))
    print(f"✅ Remplacement appliqué dans {len(matches)} fichier(s). Lance 'push' pour vérifier et publier.")


def _emit_telemetry(op: str, domain: str = None, duration_ms: int = 0, status: str = "ok", error_reason: str = None) -> None:
    """Sonde Phase 8 (append JSONL non bloquant et sans PII)."""
    try:
        target = os.environ.get("PPL_TELEMETRY_PATH")
        if not target:
            agy_dir = Path.home() / ".gemini" / "antigravity" / "state" / "telemetry"
            if agy_dir.exists():
                target = str(agy_dir / "briques_metrics.jsonl")
            else:
                target = str(TOKEN_PATH.parent / "briques_metrics.jsonl")
        tpath = Path(target)
        tpath.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "brique": "ppl_static",
            "operation": op,
            "domain": domain or "",
            "duration_ms": duration_ms,
            "status": status,
            "error_reason": error_reason,
        }
        with _REFRESH_LOCK:
            with open(tpath, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser(prog="ppl_static", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 allow_abbrev=False)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_sub(name, help_text):
        return sub.add_parser(name, help=help_text, allow_abbrev=False)

    def add_domain(p):
        p.add_argument("domain", nargs="?", default=None,
                        help="domaine du site (ex. www.mon-site.com) — "
                        "omissible si --website-id/--partner sont donnés")
        p.add_argument("--website-id", help="bypass la résolution par domaine")
        p.add_argument("--partner", type=int, help="requis avec --website-id")

    def add_go(p):
        p.add_argument("--go", action="store_true", help="publier en PROD (sinon dry-run)")

    p = add_sub("doctor", "Diagnostic complet de l'OS, de la machine et du token")
    p.set_defaults(func=cmd_doctor)

    p = add_sub("resolve", "Trouve le websiteId d'un domaine (parmi tes partenaires)")
    p.add_argument("domain")
    p.add_argument("--refresh", action="store_true", help="ignore le cache")
    p.set_defaults(func=cmd_resolve)

    p = add_sub("ls", "Liste les objets d'un site")
    add_domain(p)
    p.set_defaults(func=cmd_ls)

    p = add_sub("pull", "Miroir local complet du site")
    add_domain(p)
    p.add_argument("--full", action="store_true", help="inclure wp-content/uploads et wp-includes")
    p.set_defaults(func=cmd_pull)

    p = add_sub("preview", "Serveur local pour prévisualiser")
    p.add_argument("domain", nargs="?", help="défaut : dossier courant")
    p.add_argument("--port", type=int, default=8080)
    p.set_defaults(func=cmd_preview)

    p = add_sub("push", "Déploie les fichiers modifiés (diff local vs miroir)")
    add_domain(p)
    add_go(p)
    p.set_defaults(func=cmd_push)

    p = add_sub("replace", "Remplace un texte/URL dans tous les fichiers HTML/texte du site local")
    add_domain(p)
    p.add_argument("old", help="texte ou URL à rechercher")
    p.add_argument("new", help="texte ou URL de remplacement")
    add_go(p)
    p.set_defaults(func=cmd_replace)

    p = add_sub("add", "Ajoute/écrase un fichier")
    add_domain(p)
    p.add_argument("file")
    p.add_argument("--key", help="clé de destination (défaut : nom du fichier)")
    add_go(p)
    p.set_defaults(func=cmd_add)

    p = add_sub("rm", "Supprime un objet (DELETE /api/objects)")
    add_domain(p)
    p.add_argument("key")
    add_go(p)
    p.set_defaults(func=cmd_rm)

    p = add_sub("set-home", "Définit la page d'accueil (copie <key> en index.html)")
    add_domain(p)
    p.add_argument("key")
    add_go(p)
    p.set_defaults(func=cmd_sethome)

    args = ap.parse_args()
    t0 = time.monotonic()
    status = "ok"
    err_reason = None
    try:
        args.func(args)
    except BaseException as e:
        if isinstance(e, SystemExit) and e.code in (0, None):
            status = "ok"
        else:
            status = "error"
            err_reason = str(e)
        raise
    finally:
        dur_ms = int((time.monotonic() - t0) * 1000)
        _emit_telemetry(getattr(args, "cmd", "unknown"), getattr(args, "domain", None), dur_ms, status, err_reason)


if __name__ == "__main__":
    main()
