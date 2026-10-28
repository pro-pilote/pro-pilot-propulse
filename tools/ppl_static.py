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
SITES = BASE / "sites"
CACHE = BASE / ".cache.json"
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


def content_meta(key):
    ext = Path(key).suffix.lower()
    if ext in FORBIDDEN_VIDEO_EXTS:
        die(f"Fichier vidéo non autorisé sur STATIC ({key}). Les vidéos doivent être hébergées sur Pro-Vidéo.")
    return CONTENT_TYPES.get(ext, ("application/octet-stream", "DOCUMENT:TEXT"))


def die(msg):
    sys.exit(f"❌ {msg}")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def confirm(msg):
    try:
        return input(f"{msg} [oui/non] ").strip().lower() in ("oui", "o", "yes", "y")
    except EOFError:
        return False


def gate(args, dry_msg, confirm_msg):
    """Dry-run/confirmation partagés par toutes les commandes d'écriture.
    Retourne True si l'action doit s'exécuter."""
    if not args.go:
        print(f"\n[DRY-RUN] {dry_msg}")
        return False
    if getattr(args, "yes", False):
        print(f"\n🚀 [CONFIRMATION AGENT] Action approuvée via --yes. Publication en cours...")
        return True
    if args.go and not sys.stdin.isatty():
        die("Publication en production interdite en mode non-interactif (TTY requis). Lancez la commande directement dans votre terminal ou utilisez --yes avec l'accord explicite de l'utilisateur.")
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


def check_static(info):
    if info.get("type") != "STATIC":
        die(f"{info['domain']} est de type {info.get('type')} (pas STATIC) — "
            f"cette boîte ne gère que les sites STATIC.")


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


def deploy_file(info, key, content):
    """signed-url -> PUT S3 -> upsert."""
    if len(content) > MAX_FILE_SIZE:
        die(f"Fichier '{key}' trop lourd ({len(content) / 1_000_000:.1f} Mo > 20 Mo max autorisé sur STATIC).")

    # Garde-fou mécanique anti-troncature pour les pages HTML (défense en profondeur)
    check_html_integrity(key, content)

    ct, subtype = content_meta(key)
    wid, partner = info["websiteId"], info["partner"]
    su = api("POST", "/api/objects/signed-url", partner,
             {"websiteId": wid, "contentType": ct, "fileName": key, "key": key})
    signed = su.get("data") if isinstance(su, dict) else su
    if not signed:
        die(f"pas de signed-url pour {key}: {su}")
    # ⚠️ le PUT S3 signé n'accepte QUE Content-Type en header (le reste est
    # déjà signé dans la query) — ajouter un header type x-amz-acl → 403.
    r = requests.put(signed, data=content, headers={"Content-Type": ct}, timeout=180)
    if not r.ok:
        die(f"PUT S3 {key} → HTTP {r.status_code} {r.text[:300]}")
    api("POST", "/api/objects/upsert", partner,
        {"websiteId": wid, "originalFileName": os.path.basename(key),
         "subtype": subtype, "type": "DOCUMENT", "key": key})


# --- commandes -------------------------------------------------------------
def cmd_resolve(args):
    info = resolve(args.domain, refresh=args.refresh)
    print(to_json(info))


def cmd_ls(args):
    info = get_info(args)
    objs = list_objects(info)
    print(f"{site_label(info)} — websiteId {info['websiteId']} · "
          f"partner {info['partner']} · type {info['type']} · {len(objs)} objets")
    for o in sorted(objs, key=lambda x: x["key"]):
        home = "  ← ACCUEIL" if o["key"] == "index.html" else ""
        print(f"  {o['key']:<45} {o.get('subtype', ''):<16}{home}")


def cmd_pull(args):
    info = get_info(args)
    check_static(info)
    objs = list_objects(info)
    sitedir = site_dir(info)
    burl = base_url(info)
    manifest = {"objects": {}}
    ok = 0

    def fetch(o):
        r = requests.get(f"{burl}/{o['key']}", timeout=60, allow_redirects=False)
        if r.status_code == 301 and r.headers.get("location", "").endswith("/"):
            raise RuntimeError("Redirection 301 vers accueil (objet non trouvé)")
        r.raise_for_status()
        return r.content

    with ThreadPoolExecutor(max_workers=PUSH_WORKERS) as pool:
        futures = {pool.submit(fetch, o): o for o in objs}
        for fut in as_completed(futures):
            o = futures[fut]
            key = o["key"]
            try:
                content = fut.result()
            except Exception as e:
                print(f"  ⚠️  skip {key} ({e})")
                continue
            dest = sitedir / key
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
            manifest["objects"][key] = {"record": o, "sha256": sha(content)}
            ok += 1
            print(f"  ↓ {key} ({len(content)} o)")

    write_json(sitedir / MANIFEST, manifest)
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
    info = get_info(args, fresh=True)
    check_static(info)
    sitedir = site_dir(info)
    mpath = sitedir / MANIFEST
    if not mpath.exists():
        die(f"pas de miroir local pour {info['domain']} — fais 'pull' d'abord.")
    manifest = read_json(mpath)
    objects = manifest["objects"]

    local = {}
    TEXT_EXTENSIONS = {".html", ".css", ".js", ".json", ".txt", ".svg", ".xml"}
    EXCLUDED_NAMES = {MANIFEST, "RULES.md", "CLAUDE.md", "README.md"}
    for p in sitedir.rglob("*"):
        rel = p.relative_to(sitedir)
        if not p.is_file() or p.name in EXCLUDED_NAMES or p.suffix.lower() == ".md":
            continue
        if any(part.startswith(".") for part in rel.parts):
            continue
        data = p.read_bytes()
        # Normalisation automatique des retours chariot Windows (CRLF -> LF) pour fiabiliser le hash SHA-256
        if p.suffix.lower() in TEXT_EXTENSIONS and b"\r\n" in data:
            data = data.replace(b"\r\n", b"\n")
        local["/".join(rel.parts)] = data

    new = [k for k in local if k not in objects]
    changed = [k for k in local if k in objects and sha(local[k]) != objects[k]["sha256"]]
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

    # Contrôles de validation pré-vol (taille, formats interdits et intégrité HTML) dès le dry-run
    for k in to_publish:
        if len(local[k]) > MAX_FILE_SIZE:
            die(f"Fichier '{k}' trop lourd ({len(local[k]) / 1_000_000:.1f} Mo > 20 Mo max autorisé sur STATIC).")
        ext = Path(k).suffix.lower()
        if ext in FORBIDDEN_VIDEO_EXTS:
            die(f"Fichier vidéo non autorisé sur STATIC ({k}). Les vidéos doivent être hébergées sur Pro-Vidéo.")
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
    for key in changed:
        u = f"{base_url(info)}/{key}"
        try:
            resp = requests.get(u, timeout=60, allow_redirects=False)
            if resp.status_code == 200:
                remote_bytes = resp.content
                remote_sha = sha(remote_bytes)
                expected_sha = objects[key].get("sha256")
                local_sha = sha(local[key])
                if expected_sha and remote_sha != expected_sha:
                    if remote_sha == local_sha:
                        # Le contenu distant correspond déjà à notre version locale (ex: échec d'upsert précédent)
                        pass
                    else:
                        die(f"[CONFLIT DE CONCURRENCE] L'objet distant '{key}' a été modifié en production depuis votre dernier pull.\n"
                            f"SHA distant: {remote_sha[:12]}... != SHA manifeste pull: {expected_sha[:12]}...\n"
                            f"Re-pull requis avant publication.")
            elif resp.status_code in (404, 301):
                die(f"[CONFLIT DE CONCURRENCE] L'objet distant '{key}' a été supprimé en production depuis votre dernier pull (statut HTTP {resp.status_code}). Re-pull requis.")
            elif resp.status_code != 200:
                die(f"[CONTRÔLE DE DÉRIVE IMPOSSIBLE] '{key}' a renvoyé HTTP {resp.status_code} — re-pull ou relance.")
        except requests.RequestException as e:
            die(f"[CONTRÔLE DE DÉRIVE ÉCHOUÉ] Erreur réseau lors de la vérification de '{key}' ({e}) — relancez.")

    # Conflit sur les nouveaux fichiers (ne doivent pas déjà exister en prod avec un contenu divergent)
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
            elif resp.status_code not in (404, 301):
                die(f"[CONTRÔLE DE DÉRIVE IMPOSSIBLE] Nouveau fichier '{key}' a renvoyé HTTP {resp.status_code} (attendu: 404/301).")
        except requests.RequestException as e:
            die(f"[CONTRÔLE DE DÉRIVE ÉCHOUÉ] Erreur réseau lors de la vérification du nouveau fichier '{key}' ({e}) — relancez.")

    if not gate(args, "Ajoute --go pour publier en PROD.",
                f"Publier {len(to_publish)} fichier(s) en PROD ?"):
        return

    failed = []
    with ThreadPoolExecutor(max_workers=PUSH_WORKERS) as pool:
        futures = {pool.submit(deploy_file, info, key, local[key]): key for key in to_publish}
        for fut in as_completed(futures):
            key = futures[fut]
            try:
                fut.result()
            except SystemExit as e:
                failed.append(key)
                print(f"  ❌ {key} — {e}")
                continue
            objects[key] = {"record": {"key": key}, "sha256": sha(local[key])}
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
    content = src.read_bytes()
    ct, _ = content_meta(key)
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
        p.add_argument("--yes", "-y", action="store_true", help="confirmer sans prompt interactif TTY (pour les agents IA autorisés par l'utilisateur)")

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
    p.set_defaults(func=cmd_pull)

    p = add_sub("preview", "Serveur local pour prévisualiser")
    p.add_argument("domain", nargs="?", help="défaut : dossier courant")
    p.add_argument("--port", type=int, default=8080)
    p.set_defaults(func=cmd_preview)

    p = add_sub("push", "Déploie les fichiers modifiés (diff local vs miroir)")
    add_domain(p)
    add_go(p)
    p.set_defaults(func=cmd_push)

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
    args.func(args)


if __name__ == "__main__":
    main()
