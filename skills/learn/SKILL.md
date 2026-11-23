---
name: learn
version: "2.2.1"
description: Apprentissage continu, enregistrement immédiat de règles et bilan rétrospectif complet de session dans donnees-business/_inbox/ sur GitHub via le portail Pro-Pilot.
---

# Skill `/learn` — Apprentissage Continu & Bilan Rétrospectif de Session

Cette skill permet de capitaliser sur l'expérience, d'enregistrer des préférences, corrections, règles éditoriales ou graphiques et d'effectuer le bilan complet d'une session de travail. Les enseignements sont enregistrés directement sur le dépôt GitHub privé du partenaire dans `donnees-business/_inbox/` sans manipulation Git manuelle ni conflit d'écriture.


---

## 0. Contrôle de Version Ultra-Rapide (< 100 ms) & Nouveaux Skills

À chaque appel de `/learn`, exécute ce snippet Python compact borné à 2 secondes (dégradation gracieuse hors-ligne sans bloquer l'action) :
```bash
python3 - <<'PY'
import json, os, urllib.request

MANIFEST_URL = "https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/manifest.json"
LOADER_BASE = "https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/_loaders"
SKILL_NAME = "learn"
LOCAL_PATH = f".claude/commands/{SKILL_NAME}.md"
CURRENT_VERSION = "2.2.1"
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

    # 2. Détection de nouveaux skills disponibles (stables ou scoped éligibles au partenaire)
    req = urllib.request.Request(MANIFEST_URL, headers={"User-Agent": "Pro-Pilot-CLI/2.2"})
    with urllib.request.urlopen(req, timeout=2) as resp:
        manifest = json.loads(resp.read().decode("utf-8"))

    local_pid = None
    env_file = "." + "env"
    if os.path.exists(env_file):
        try:
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("PARTNER_ID="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        local_pid = int(val) if val.isdigit() else None
        except Exception:
            pass

    for name, data in manifest.get("skills", {}).items():
        is_scoped_ok = (data.get("status") == "partner_scoped" and local_pid in data.get("eligible_partner_ids", []))
        if data.get("status") == "stable" or is_scoped_ok:
            target_cmd = f".claude/commands/{name}.md"
            if not os.path.exists(target_cmd):
                print(f"[PRO_PILOT_NEW_SKILL] Nouveau skill disponible : /{name} — {data.get('summary', '')} (installer {LOADER_BASE}/{name}.md)")

    # 3. Signalement des anciens lanceurs dépréciés
    for old_cmd in ("fin", "feedback"):
        if os.path.exists(f".claude/commands/{old_cmd}.md"):
            print(f"[PRO_PILOT_DEPRECATED] .claude/commands/{old_cmd}.md est obsolète (remplacé par /learn) et peut être supprimé.")
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

## 2. Exécution Silencieuse via le Portail Pro-Pilot (`POST /api/feedback`)

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
