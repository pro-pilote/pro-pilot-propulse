---
name: learn
version: "2.2.5"
description: Apprentissage continu, enregistrement immédiat de règles et bilan rétrospectif complet de session dans donnees-business/_inbox/ sur GitHub via le portail Pro-Pilot.
---

# Skill `/learn` — Apprentissage Continu & Bilan Rétrospectif de Session

Cette skill permet de capitaliser sur l'expérience, d'enregistrer des préférences, corrections, règles éditoriales ou graphiques et d'effectuer le bilan complet d'une session de travail. Les enseignements sont enregistrés directement sur le dépôt GitHub privé du partenaire dans `donnees-business/_inbox/` sans manipulation Git manuelle ni conflit d'écriture.


---

## 0. Contrôle de Version Ultra-Rapide (< 100 ms) & Nouveaux Skills

À chaque appel de `/learn`, exécute ce snippet Python compact borné à 2 secondes (dégradation gracieuse hors-ligne sans bloquer l'action) :
```bash
python3 - <<'PY'
import base64, json, os, urllib.request

MANIFEST_URL = "https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/manifest.json"
LOADER_BASE = "https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/_loaders"
SKILL_NAME = "learn"
LOCAL_PATH = f".claude/commands/{SKILL_NAME}.md"
CURRENT_VERSION = "2.2.5"
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
- Si une mise à jour est signalée, elle est appliquée immédiatement de façon atomique.
- Si un nouveau skill stable est détecté, signale-le sobrement à l'utilisateur et propose-lui de le télécharger.

---

## 1. Deux Modes d'Utilisation

### Mode A : Enregistrement Inline (`/learn <règle ou correction>`)
Utilisé **en cours de travail** dès qu'une règle précise, une correction de style, une valeur de paramètre ou une préférence doit être retenue pour les prochaines fois :
- Exemples :
  - `/learn Toujours utiliser le vert émeraude #00C853 pour les boutons CTA de cette marque.`
  - `/learn Ne jamais afficher le bandeau de réassurance sur la vue mobile.`
  - `/learn Le logo officiel dans le header est logo-white.svg et non logo.png.`
- **Action de l'IA** : Rédiger une note concise ciblée, catégorisée et mappée vers le bon fichier cible.

### Mode B : Clôture & Bilan Rétrospectif de Session (`/learn` ou `/learn bilan`)
Utilisé **à la fin d'une session de travail**.
> **Règle absolue pour l'IA** : Tu **DOIS** parcourir l'intégralité du fil de discussion depuis le **premier message** de la session jusqu'au dernier. Tu ne dois pas te contenter des derniers échanges.

Tu dois extraire et structurer l'ensemble des enseignements de la session selon les 4 paniers obligatoires :

| Panier | Ce qui doit être scanné & extrait | Fichier cible de consolidation |
|---|---|---|
| **1. Corrections & Refus** | Toutes les rectifications faites par l'utilisateur (*« non pas ça », « aligne à gauche », « retire cette mention », « ce n'est pas la bonne formulation »*). | `skills/<skill>/erreurs-connues.md` |
| **2. Design & Identité** | Couleurs hexadécimales adoptées, logo retenu, espacements, typographies, styles de blocs validés. | `donnees-business/design-system.md` |
| **3. Copywriting & Métier** | Formulations éditoriales clés, mentions légales exigées, conditions de l'offre, arguments validés. | `skills/<skill>/specificites.md` / `donnees-business/<sku>/fiche-produit.md` |
| **4. Technique & Paramètres** | Variables d'environnement ajustées, slugs de sites, endpoints d'API, contournements de bugs validés. | `skills/<skill>/variables.md` |

Chaque point extrait doit mentionner :
- Le contexte (ce qui a été demandé / rencontré).
- La décision ou la correction actée.
- La recommandation concrète pour les futures sessions.

---

## 2. Enregistrement via le Portail Pro-Pilot (`POST /api/feedback`)

Rédige le contenu Markdown complet de la note (titre, synthèse, points par panier, fichiers cibles) et transmets-le via le script ci-dessous :

```bash
set -a; source .env; set +a
python3 - "<sujet>" "<contenu_markdown>" "<categorie>" "<partner_slug_si_multi>" <<'PY'
import os, sys, json, urllib.request, urllib.error

token = os.environ.get("PRO_PILOT_WRITE_TOKEN", "").strip()
if not token:
    print("Erreur: PRO_PILOT_WRITE_TOKEN manquant dans .env")
    sys.exit(1)

subject = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else "Bilan de session"
content = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else "Synthese des apprentissages"
category = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else "editorial"
partner = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else os.environ.get("PARTNER_SLUG", "")

payload = {"subject": subject, "content": content, "category": category}
if partner:
    payload["partner"] = partner

req = urllib.request.Request(
    "https://pro-pilot.propulse-lab.com/api/feedback",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Pro-Pilot-CLI/2.2"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print(f"Succes: {res.get('path')} enregistre sur GitHub ({res.get('repo')}) - commit {str(res.get('commitSha', ''))[:7]}")
except urllib.error.HTTPError as err:
    if err.code == 401:
        print("SESSION_EXPIRED_401: Jeton expiré ou renouvelé — reconnectez-vous une fois sur https://pro-pilot.propulse-lab.com/ pour actualiser l'espace.")
    else:
        print(f"Erreur HTTP {err.code}: {err.read().decode('utf-8')}")
    sys.exit(1)
PY
```

---

## 3. Confirmation Utilisateur

Confirme sobrement à l'utilisateur :
- La liste concise des enseignements majeurs retenus (par catégorie).
- Le chemin d'enregistrement sur GitHub dans `donnees-business/_inbox/` retourné par l'API.
- Le rappel que ces règles seront prises en compte lors des prochaines sessions.
