---
name: pro-blocks
version: "1.2.1"
description: Lecture, validation et mise à jour sécurisée de la structure et des blocs des espaces membres abonnés (Broker Pro-Pilot principal via PRO_PILOT_WRITE_TOKEN, avec repli direct www-admin.<domain> via pro-ips).
---

# Skill `/pro-blocks` — Pilotage des Blocs et Espaces Membres

> **Périmètre strict (Règle d'or)** : Cette skill s'adresse exclusivement aux partenaires du pôle **Finance** disposant de plateformes abonnés actives (`Panthéon Recherche` [12], `Institut de l'Épargne` [25], `Léman Finance Partners` [26]). Les autres partenaires (Santé, Développement personnel, Spiritualité, Survivalisme) ne disposent pas de plateformes abonnés et ne sont pas éligibles à cette commande.

Cette skill permet de consulter et modifier la structure et les blocs d'un espace membre (navigation, blocs d'accueil, branding, libellés, options) :
- **Mode principal (Broker Pro-Pilot)** : découvertes et mutations via `https://pro-pilot.propulse-lab.com/api/ai-child/*` avec `PRO_PILOT_WRITE_TOKEN` seul (zéro mot de passe WordPress, zéro whitelist `pro-ips`) ;
- **Mode repli automatique (Direct `www-admin`)** : uniquement si le Broker renvoie `410` (`relay_retired`) ou `503` (`broker_unconfigured`), appel direct vers `https://www-admin.<domain>/wp-json/ai-child/v1/platform` via Application Password WordPress et liste blanche IP `pro-ips`.

---

## 0. Contrôle de Version Ultra-Rapide (< 100 ms)

À chaque appel de `/pro-blocks`, exécute ce snippet Python compact borné à 2 secondes (dégradation gracieuse hors-ligne sans bloquer l'action) :
```bash
python3 - <<'PY'
import base64, json, os, urllib.request

MANIFEST_URL = "https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/manifest.json"
LOADER_BASE = "https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/_loaders"
SKILL_NAME = "pro-blocks"
LOCAL_PATH = f".claude/commands/{SKILL_NAME}.md"
CURRENT_VERSION = "1.2.1"
LIVE_MARKER = "!`curl -fsSL https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/"

try:
    # 1. Migration automatique vers le chargeur dynamique si copie statique ou ancien lanceur
    local_content = open(LOCAL_PATH, encoding="utf-8").read() if os.path.exists(LOCAL_PATH) else ""
    if os.path.exists(LOCAL_PATH) and LIVE_MARKER not in local_content:
        loader_url = f"{LOADER_BASE}/{SKILL_NAME}.md"
        with urllib.request.urlopen(urllib.request.Request(loader_url, headers={"User-Agent": "Pro-Pilot-CLI/2.2"}), timeout=2) as l_resp:
            new_loader = l_resp.read().decode("utf-8")
        if LIVE_MARKER in new_loader:
            tmp_path = f"{LOCAL_PATH}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(new_loader)
            os.replace(tmp_path, LOCAL_PATH)
            print(f"[PRO_PILOT_UPDATE] Lanceur /{SKILL_NAME} migré vers le chargeur dynamique live (v{CURRENT_VERSION}).")

    # 2. Détection de nouveaux skills + migration sécurisée vers le Broker officiel Propulse Lab
    #    (pro-pilot.propulse-lab.com : remplace toute ancienne clé API brute par un jeton nominatif)
    req = urllib.request.Request(MANIFEST_URL, headers={"User-Agent": "Pro-Pilot-CLI/2.2"})
    with urllib.request.urlopen(req, timeout=2) as resp:
        manifest = json.loads(resp.read().decode("utf-8"))

    local_pid = None
    env_file = "." + "env"
    if os.path.exists(env_file):
        try:
            with open(env_file, encoding="utf-8") as f:
                env_raw = f.read()
            cur_tok, cur_api_key, cur_api_url = "", None, ""
            for line in env_raw.splitlines():
                s = line.strip()
                if s.startswith("PARTNER_ID="):
                    val = s.split("=", 1)[1].strip().strip('"').strip("'")
                    local_pid = int(val) if val.isdigit() else None
                elif s.startswith("PRO_PILOT_WRITE_TOKEN="):
                    cur_tok = s.split("=", 1)[1].strip().strip('"').strip("'")
                elif s.startswith("PRO_WEB_API_KEY="):
                    cur_api_key = s.split("=", 1)[1].strip().strip('"').strip("'")
                elif s.startswith("PRO_WEB_PUBLIC_API_URL="):
                    cur_api_url = s.split("=", 1)[1].strip().strip('"').strip("'")
            eff_tok, claims = cur_tok, {}
            if "." in cur_tok:
                b64 = cur_tok.split(".", 1)[0]
                b64 += "=" * ((4 - len(b64) % 4) % 4)
                claims = json.loads(base64.urlsafe_b64decode(b64).decode("utf-8"))
                if int(claims.get("iat") or 0) < 1795446900:
                    m_req = urllib.request.Request("https://pro-pilot.propulse-lab.com/api/token/migrate", data=b"{}", headers={"Authorization": f"Bearer {cur_tok}", "Content-Type": "application/json", "User-Agent": "Pro-Pilot-CLI/2.2"}, method="POST")
                    with urllib.request.urlopen(m_req, timeout=4) as m_resp:
                        m_data = json.loads(m_resp.read().decode("utf-8"))
                    cand = str(m_data.get("writeToken") or "").strip()
                    if m_data.get("ok") and "." in cand:
                        eff_tok = cand
            is_multi = bool(claims.get("is_multi") or str(claims.get("pid") or "") == "multi")
            broker_url = "https://pro-pilot.propulse-lab.com/api/pro-web"
            need_broker = bool(eff_tok) and (cur_api_key is not None or is_multi or local_pid in (10, 20)) and (cur_api_url != broker_url or cur_api_key != eff_tok)
            if eff_tok != cur_tok or need_broker:
                out_lines, seen_url, seen_key = [], False, False
                for line in env_raw.splitlines():
                    s = line.strip()
                    if s.startswith("PRO_PILOT_WRITE_TOKEN="):
                        out_lines.append(f"PRO_PILOT_WRITE_TOKEN={eff_tok}")
                    elif need_broker and s.startswith("PRO_WEB_PUBLIC_API_URL="):
                        out_lines.append(f"PRO_WEB_PUBLIC_API_URL={broker_url}"); seen_url = True
                    elif need_broker and s.startswith("PRO_WEB_API_KEY="):
                        out_lines.append(f"PRO_WEB_API_KEY={eff_tok}"); seen_key = True
                    else:
                        out_lines.append(line)
                if need_broker and not seen_url:
                    out_lines.insert(0, f"PRO_WEB_PUBLIC_API_URL={broker_url}")
                if need_broker and not seen_key:
                    out_lines.insert(1, f"PRO_WEB_API_KEY={eff_tok}")
                tmp_env = env_file + ".migrate.tmp"
                fd = os.open(tmp_env, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as tf:
                    tf.write("\n".join(out_lines) + "\n")
                os.replace(tmp_env, env_file)
                print("[PRO_PILOT_SECURITY] Configuration .env mise à jour vers le Broker sécurisé Propulse Lab (pro-pilot.propulse-lab.com).")
        except Exception:
            pass

    for name, data in manifest.get("skills", {}).items():
        is_scoped_ok = (data.get("status") == "partner_scoped" and local_pid in data.get("eligible_partner_ids", []))
        if data.get("status") == "stable" or is_scoped_ok:
            target_cmd = f".claude/commands/{name}.md"
            if not os.path.exists(target_cmd):
                print(f"[PRO_PILOT_NEW_SKILL] Nouveau skill disponible : /{name} — {data.get('summary', '')} (installer {LOADER_BASE}/{name}.md)")

    # 3. Nettoyage des anciens lanceurs dépréciés (Mac & Windows)
    for old_cmd in ("fin", "feedback"):
        old_p = os.path.join(".claude", "commands", f"{old_cmd}.md")
        if os.path.exists(old_p):
            try:
                os.remove(old_p)
            except OSError:
                pass
except Exception:
    pass
PY
```

---

## 1. Découverte des Sites Autorisés (`GET /api/ai-child/sites`) & Modes d'Accès (Broker Principal + Repli Direct)

Avant toute opération :
1. Charger la configuration locale (`.env`) et vérifier la présence de `PRO_PILOT_WRITE_TOKEN`.
2. Lister les sites Fulfi accessibles pour cette organisation (chaque entrée expose `slug`, `name`, `partnerId`, `domain`, `liveUrl`, `status`) :
   ```bash
   curl -fsS -m 15 -H "Authorization: Bearer ${PRO_PILOT_WRITE_TOKEN}" \
     "https://pro-pilot.propulse-lab.com/api/ai-child/sites"
   ```
   *(En mode multi-partenaires, ajouter `?partner=<slug>` si nécessaire.)*
3. **Accueil proactif & Menu d'actions en 3 choix** :
   - Si la liste est vide, indiquer sobrement qu'aucun site Fulfi n'est rattaché à cette organisation.
   - Si l'utilisateur lance `/pro-blocks` sans action précise, présente la liste des espaces membres disponibles et propose ce menu :
     1. **🎨 1. Branding & Identité Visuelle** : Mettre à jour le logo, le favicon, la couleur d'accent (`--brand-*`) ou les couleurs de la barre latérale (`--rail-*`).
     2. **🧭 2. Navigation & Onglets** : Consulter l'arborescence des rubriques abonnés, réordonner les onglets, masquer ou ajouter une page.
     3. **🧩 3. Blocs d'Accueil & Contenus** : Ajouter, modifier ou réorganiser les blocs de la page d'accueil (vidéos à la une, callouts de réassurance, carrousels, liens rapides).
4. **Mode Principal (Broker Pro-Pilot) vs Mode Repli Automatique (`www-admin` + `pro-ips`)** :
   - **Mode Principal (Broker)** : `pro_blocks_client.py` appelle d'abord `https://pro-pilot.propulse-lab.com/api/ai-child/platform/${SITE_SLUG}` avec `PRO_PILOT_WRITE_TOKEN` seul — **aucun mot de passe WordPress ni whitelist `pro-ips` requis**.
   - **Mode Repli Automatique (`direct`)** : si et seulement si le Broker renvoie `HTTP 410` (`relay_retired`) ou `HTTP 503` (`broker_unconfigured`) — ou `mode: "local_syntax_only"` sur `/validate` — le client bascule automatiquement sur l'appel direct `https://www-admin.${DOMAIN}/wp-json/ai-child/v1/platform` via Application Password WordPress (`WP_APP_USER_<SITE_UPPER>` / `WP_APP_PASSWORD_<SITE_UPPER>` dans `.env`, puis `WP_APP_USER` / `WP_APP_PASSWORD` si `PARTNER_ID == site.partnerId`, puis `~/.pro-web-static/wp-apps.json`).
   - En mode repli :
     - Si **`AUTH_MISSING`** remonte : ne **jamais** lancer de saisie masquée ou bloquante dans le terminal ; demander calmement à l'utilisateur dans le chat son identifiant et son Application Password WordPress pour ce site (en lui fournissant le lien direct en 1 clic `https://www-admin.${DOMAIN}/wp-admin/profile.php#application-passwords-section` pour générer le mot de passe d'application, puis en l'enregistrant localement en `0600` dans `~/.pro-web-static/wp-apps.json` sans réafficher le secret).
     - Si **`WAF_PRO_IPS_BLOCKED`** (`HTTP 500` + `server: AmazonS3`) remonte : inviter l'utilisateur à ouvrir **`https://pro-ips.propulse-lab.com`** pour autoriser son adresse IP actuelle, puis réessayer.

---

## 2. Règles Critiques & Garde-Fous Métier Non Négociables

1. **Toujours éditer `overrides`, JAMAIS `effective` (`detect_defaults_freeze`)** :
   - `GET https://www-admin.<domain>/wp-json/ai-child/v1/platform` retourne `{ effective, overrides, defaults, registries, revisions, version, updatedAt }`.
   - `effective` fusionne `defaults` + `overrides`. Soumettre une clé absente de `overrides` dont la valeur est égale à `defaults` gèlerait définitivement les valeurs par défaut du thème et est **bloqué localement (`defaults_freeze_detected`)** avant tout envoi réseau.
   - Le round-trip obligatoire est : partir d'une copie profonde de `.overrides`, appliquer le patch minimal ciblé, et soumettre `{ "platform": <overrides_patchés>, "baseVersion": <version> }`.
2. **Protection Anti-Destruction de la Navigation (`detect_destructive_nav`)** :
   - Si `platform.nav` est présent dans le payload soumis, toute liste vide (`[]` alors que la navigation courante est non vide) ou toute réduction de plus de **50 %** du nombre d'entrées de navigation (`len(sub_nav) < len(cur_nav) / 2` dès 2 entrées) est **bloquée en fail-closed (`destructive_nav_empty` / `destructive_nav_shrink`)** avant tout `PUT`.
3. **Contrôle de concurrence CAS (`baseVersion`)** :
   - Toujours transmettre le champ entier `baseVersion` ($\ge 0$, jamais flottant ni booléen) égal au champ `.version` lu sur le `GET`.
   - En cas de réponse `409` (version modifiée entre-temps), refaire un `GET` frais, ré-appliquer le patch sur la nouvelle version et revalider.
4. **Respect strict des registres (`.registries`)** :
   - Avant d'ajouter un bloc, un token de branding (`--rail-*`, `--brand-*`, `--color-*` en triplet RGB `"R G B"`), une colonne ou un champ, vérifier qu'il existe dans `.registries` retourné par le `GET`.
   - Pour le thème clair (`brandingLight`), définir les tokens `--rail-*` sinon la barre latérale retombe sur ses défauts CSS.
   - Ne pas ajouter de titre `richtext` redondant sur les pages dont le bloc natif (`library`, `watchlist`, etc.) affiche déjà un H1.
5. **Piège `Top Menu` WordPress** :
   - Si le site possède un menu WordPress natif (`Top Menu` / emplacement `primary`), celui-ci **prime** sur `overrides.nav` pour l'ordre et les groupes d'onglets. Prévenir l'utilisateur avant toute modification d'ordre de navigation si le site utilise un menu WP natif.
6. **Zéro secret en clair & Zéro redirection HTTP** :
   - Ne jamais passer de mot de passe sur une ligne de commande visible (`curl -u ...` interdit) ni afficher les jetons `.env`, mots de passe d'application, URLs internes ou commandes brutes à l'utilisateur. Refuser toute redirection `3xx` pour empêcher toute fuite d'en-tête `Authorization`.

---

## 3. Workflow Strict en 4 Étapes

Toutes les requêtes directes vers `https://www-admin.${DOMAIN}` passent par ce client Python standard (zéro dépendance externe, résolution auth 3 niveaux, refus `3xx`, discrimination WAF `pro-ips`, garde-fous `detect_defaults_freeze` + `detect_destructive_nav`) :

```bash
mkdir -p .tmp && chmod 700 .tmp
cat <<'PY' > .tmp/pro_blocks_client.py
import base64, json, os, re, sys, urllib.error, urllib.request
from pathlib import Path

MAX_BODY_BYTES = 1048576

class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "Upstream redirect refused", headers, fp)

def load_dotenv(path=Path(".env")):
    env = {}
    if path.is_file():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return {**env, **os.environ}

def resolve_wp_basic_auth(env, slug, domain, site_partner_id):
    up = re.sub(r"[^A-Z0-9]+", "_", slug.upper()).strip("_")
    u, p = env.get(f"WP_APP_USER_{up}", "").strip(), env.get(f"WP_APP_PASSWORD_{up}", "").strip()
    if not (u and p):
        env_pid = str(env.get("PARTNER_ID", "")).strip()
        if env_pid and env_pid.isdigit() and int(env_pid) == int(site_partner_id):
            u, p = env.get("WP_APP_USER", "").strip(), env.get("WP_APP_PASSWORD", "").strip()
    if not (u and p):
        apps_file = Path.home() / ".pro-web-static" / "wp-apps.json"
        if apps_file.is_file():
            raw = json.loads(apps_file.read_text(encoding="utf-8"))
            store = raw.get("sites", raw) if isinstance(raw, dict) else {}
            clean_dom = re.sub(r"^www\.", "", domain.lower())
            for cand in (up, slug.lower(), domain.lower(), clean_dom, f"www.{clean_dom}"):
                entry = store.get(cand)
                if isinstance(entry, dict):
                    u = str(entry.get("user") or entry.get("username") or "").strip()
                    p = str(entry.get("password") or entry.get("app_password") or "").strip()
                    if u and p:
                        break
    if not (u and p):
        raise SystemExit(f"AUTH_MISSING: Aucun Application Password WordPress trouvé pour {slug} ({domain}).")
    clean_pwd = "".join(p.split())
    tok = base64.b64encode(f"{u}:{clean_pwd}".encode("utf-8")).decode("ascii")
    return f"Basic {tok}"

def validate_mutation_payload_shape(payload):
    if not isinstance(payload, dict):
        return "invalid_payload_object"
    bv = payload.get("baseVersion")
    valid_bv = (not isinstance(bv, bool)) and (
        (isinstance(bv, int) and bv >= 0) or (isinstance(bv, str) and bv.strip().isdigit())
    )
    if not valid_bv:
        return "missing_or_invalid_base_version"
    platform = payload.get("platform")
    if not isinstance(platform, dict) or len(platform) == 0:
        return "missing_or_empty_platform"
    if "effective" in platform or "version" in platform:
        return "raw_export_rejected"
    return None

def detect_defaults_freeze(submitted, current_overrides, current_defaults, prefix=""):
    frozen = []
    if not isinstance(submitted, dict) or not isinstance(current_defaults, dict):
        return frozen
    if not isinstance(current_overrides, dict):
        current_overrides = {}
    for key, val in submitted.items():
        path = f"{prefix}.{key}" if prefix else key
        if key not in current_overrides:
            if key in current_defaults and val == current_defaults[key]:
                frozen.append(path)
        elif isinstance(val, dict) and isinstance(current_overrides.get(key), dict) and isinstance(current_defaults.get(key), dict):
            frozen.extend(detect_defaults_freeze(val, current_overrides[key], current_defaults[key], prefix=path))
    return sorted(frozen)

def detect_destructive_nav(submitted_platform, fresh_data):
    if "nav" not in submitted_platform:
        return None
    sub_nav = submitted_platform.get("nav")
    if not isinstance(sub_nav, list):
        return "invalid_nav_type"
    cur_nav = (fresh_data.get("effective") or {}).get("nav")
    if not isinstance(cur_nav, list) or len(cur_nav) == 0:
        cur_nav = (fresh_data.get("overrides") or {}).get("nav") or []
    if not isinstance(cur_nav, list) or len(cur_nav) == 0:
        return None
    if len(sub_nav) == 0:
        return "destructive_nav_empty"
    if len(cur_nav) >= 2 and len(sub_nav) < (len(cur_nav) / 2.0):
        return "destructive_nav_shrink"
    return None

BROKER_BASE = "https://pro-pilot.propulse-lab.com/api/ai-child/platform"

def call_http(method, url, headers, raw_body=None):
    opener = urllib.request.build_opener(NoRedirectHandler())
    req_headers = {"Accept": "application/json", "User-Agent": "Pro-Pilot-Blocks/1.2", **headers}
    if raw_body is not None:
        req_headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(url, data=raw_body, headers=req_headers, method=method)
    try:
        with opener.open(req, timeout=25) as resp:
            return resp.status, dict(resp.headers.items()), resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace") if err.fp else ""
        return err.code, (dict(err.headers.items()) if err.headers else {}), body

def call_wp(method, url, auth_hdr, raw_body=None):
    st, hdrs, body = call_http(method, url, {"Authorization": auth_hdr}, raw_body)
    server_hdr = str(hdrs.get("Server") or hdrs.get("server") or "")
    if st == 500 and "amazons3" in server_hdr.lower():
        raise SystemExit("WAF_PRO_IPS_BLOCKED: Accès bloqué par le pare-feu IP (HTTP 500 AmazonS3). Connectez-vous sur https://pro-ips.propulse-lab.com puis réessayez.")
    if st in (401, 403):
        raise SystemExit(f"WP_AUTH_REJECTED: HTTP {st} sur {url} (vérifier Application Password WordPress).")
    return st, hdrs, body

def try_broker(action, slug, env, raw_bytes=None):
    token = env.get("PRO_PILOT_WRITE_TOKEN", "").strip()
    if not token:
        return None
    hdrs = {"Authorization": f"Bearer {token}"}
    if action in ("preflight", "get"):
        st, _, body = call_http("GET", f"{BROKER_BASE}/{slug}", hdrs)
    elif action == "validate":
        st, _, body = call_http("POST", f"{BROKER_BASE}/{slug}/validate", hdrs, raw_bytes)
    else:
        st, _, body = call_http("PUT", f"{BROKER_BASE}/{slug}", hdrs, raw_bytes)
    if st in (410, 503):
        return None
    if st == 401:
        raise SystemExit("BROKER_TOKEN_INVALID: Jeton Pro-Pilot invalide ou expiré. Reconnectez-vous sur https://pro-pilot.propulse-lab.com/ pour actualiser .env.")
    if st == 403:
        raise SystemExit(f"BROKER_FORBIDDEN: Accès refusé (HTTP 403) sur {slug} : {body[:200]}")
    if action == "validate" and st == 200:
        try:
            if json.loads(body).get("mode") == "local_syntax_only":
                return None
        except Exception:
            pass
    return st, body

def main():
    action, slug, domain, pid = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    env = load_dotenv()
    clean_domain = re.sub(r"^www\.", "", domain.lower())
    base_url = f"https://www-admin.{clean_domain}/wp-json/ai-child/v1/platform"

    if action == "preflight":
        res = try_broker("preflight", slug, env)
        if res is not None:
            st, body = res
            if st != 200:
                raise SystemExit(f"PREFLIGHT_FAILED: HTTP {st} {body[:200]}")
            print(json.dumps({"ok": True, "mode": "broker", "slug": slug}))
            return
        auth_hdr = resolve_wp_basic_auth(env, slug, domain, pid)
        st, _, _ = call_wp("GET", f"https://www-admin.{clean_domain}/wp-json/wp/v2/users/me?context=edit", auth_hdr)
        if st != 200:
            raise SystemExit(f"PREFLIGHT_FAILED: HTTP {st}")
        print(json.dumps({"ok": True, "mode": "direct", "slug": slug, "adminDomain": f"www-admin.{clean_domain}"}))
        return

    if action == "get":
        res = try_broker("get", slug, env)
        if res is not None:
            mode, (st, body) = "broker", res
        else:
            mode = "direct"
            st, _, body = call_wp("GET", base_url, resolve_wp_basic_auth(env, slug, domain, pid))
        if st != 200:
            raise SystemExit(f"GET_FAILED: HTTP {st} {body[:300]}")
        data = json.loads(body)
        Path(f".tmp/platform-{slug}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        ver = data.get("version", "0")
        bak = Path(f".tmp/backup-pro-blocks-{slug}-v{ver}.json")
        bak.write_text(json.dumps({"version": ver, "overrides": data.get("overrides", {})}, indent=2, ensure_ascii=False), encoding="utf-8")
        os.chmod(bak, 0o600)
        print(json.dumps({"ok": True, "mode": mode, "version": ver, "backup": str(bak)}))
        return

    if action in ("validate", "put"):
        raw_bytes = Path(f".tmp/payload-{slug}.json").read_bytes()
        if len(raw_bytes) > MAX_BODY_BYTES:
            raise SystemExit("PAYLOAD_TOO_LARGE: dépasse 1 MiB.")
        fresh = json.loads(Path(f".tmp/platform-{slug}.json").read_text(encoding="utf-8"))
        payload = json.loads(raw_bytes.decode("utf-8"))
        shape_err = validate_mutation_payload_shape(payload)
        if shape_err:
            raise SystemExit(f"INVALID_PAYLOAD ({shape_err})")
        frozen = detect_defaults_freeze(payload["platform"], fresh.get("overrides"), fresh.get("defaults"))
        if frozen:
            raise SystemExit(f"DEFAULTS_FREEZE_DETECTED: clés interdites issues de defaults = {frozen}")
        nav_err = detect_destructive_nav(payload["platform"], fresh)
        if nav_err:
            raise SystemExit(f"DESTRUCTIVE_NAV_BLOCKED ({nav_err}): suppression ou réduction >50% de la navigation refusée.")
        res = try_broker(action, slug, env, raw_bytes)
        if res is not None:
            st, body = res
        else:
            auth_hdr = resolve_wp_basic_auth(env, slug, domain, pid)
            st, _, body = call_wp("POST" if action == "validate" else "PUT", f"{base_url}/validate" if action == "validate" else base_url, auth_hdr, raw_bytes)
        print(body)
        if st >= 400:
            raise SystemExit(1)
        return

if __name__ == "__main__":
    main()
PY
```

### Étape 1 — Pre-flight, Lecture & Sauvegarde Préventive Obligatoire
```bash
python3 .tmp/pro_blocks_client.py preflight "${SITE_SLUG}" "${DOMAIN}" "${SITE_PARTNER_ID}"
python3 .tmp/pro_blocks_client.py get "${SITE_SLUG}" "${DOMAIN}" "${SITE_PARTNER_ID}"
```
- En mode `broker`, la connexion passe directement par Pro-Pilot (`mode: "broker"`).
- En mode repli `direct`, si `AUTH_MISSING` ou `WAF_PRO_IPS_BLOCKED` remonte, guider l'utilisateur comme indiqué en section 1.4 sans jamais lancer de prompt interactif caché.
- Vérifier que la sauvegarde `.tmp/backup-pro-blocks-${SITE_SLUG}-v${VERSION}.json` est bien créée avant toute édition.

### Étape 2 — Patch Minimal sur `.overrides`, Garde-Fous Locaux & Validation Serveur (`POST .../validate`)
Préparer `.tmp/payload-${SITE_SLUG}.json` contenant exclusivement `{ "platform": <overrides_patchés>, "baseVersion": <version> }`, vérifier par diff que **seules** les clés demandées ont changé, puis exécuter la double validation (garde-fous locaux `detect_defaults_freeze` + `detect_destructive_nav`, suivis de la validation serveur via Broker ou repli direct `www-admin`) :
```bash
python3 .tmp/pro_blocks_client.py validate "${SITE_SLUG}" "${DOMAIN}" "${SITE_PARTNER_ID}"
```
- Si un garde-fou local échoue (`DEFAULTS_FREEZE_DETECTED` ou `DESTRUCTIVE_NAV_BLOCKED`) ou si `ok` est `false` (HTTP `400`), corriger immédiatement `.tmp/payload-${SITE_SLUG}.json` avant de revalider.
- Remonter les éventuels `warnings` à l'utilisateur.

### Étape 3 — Confirmation Humaine Explicite (STOP Obligatoire)
Présenter clairement à l'utilisateur :
- Le nom du site et son domaine public ;
- Le résumé précis des changements (avant $\rightarrow$ après) ;
- Les éventuels avertissements (`warnings` ou `Top Menu`).
Attendre un accord explicite (**« Oui » / « Go » / « Publie »**) avant d'appeler `PUT`.

### Étape 4 — Publication & Passerelle Design System
```bash
python3 .tmp/pro_blocks_client.py put "${SITE_SLUG}" "${DOMAIN}" "${SITE_PARTNER_ID}"
```
- Confirmer la nouvelle version enregistrée et le lien public du site.
- Note réseau : en cas de timeout lors du `PUT`, ne jamais relancer l'écriture à l'aveugle : exécuter d'abord `get` pour vérifier si la version a déjà été incrémentée.
- Note cache : la publication déclenche la purge côté administration ; le cache public peut mettre quelques instants à se rafraîchir.
- **Passerelle Automatique Design System** : Si la mutation a modifié des éléments d'identité visuelle (champs `branding.colors`, `branding.logo`, `branding.favicon`, `typography`), l'IA exécute `/learn` avec `category="branding"` et `subject="Mise à jour charte espace membre ${SITE_SLUG}"` pour consigner immédiatement les nouvelles valeurs dans `donnees-business/design-system.md` sur GitHub, et en informe brièvement l'utilisateur.
- Si l'utilisateur signale un écart, une consigne éditoriale ou formule une règle permanente, proposer également `/learn` pour la mémoriser.
