---
name: fin
description: Cloture, enregistrement et synchronisation append-only des retours, corrections et regles partenaires dans donnees-business/_inbox/ sur GitHub via le portail Pro-Pilot.
---

# Skill `/fin` — Enregistrement Append-Only des Retours Partenaires

Cette skill permet d'enregistrer les retours d'expérience, corrections, règles éditoriales ou techniques et préférences d'équipe directement sur le dépôt GitHub privé du partenaire dans `donnees-business/_inbox/`, sans manipulation Git locale ni conflit d'écriture entre collaborateurs.

---

## 1. Déclencheurs & Cibles de Consolidation

Déclencher `/fin` :
- À la demande explicite de l'utilisateur (`/fin` ou `/fin <description>`), en clôture de tâche ou d'échange,
- Ou proactivement dès qu'un utilisateur corrige un rendu, un style, une variable ou une mention légale.

Indiquer dans le corps Markdown de la note le fichier cible où la règle a vocation à être consolidée :
- Paramètres et sites : `skills/<nom-skill>/variables.md`
- Spécificités éditoriales ou tracking : `skills/<nom-skill>/specificites.md`
- Pièges et erreurs connues : `skills/<nom-skill>/erreurs-connues.md`
- Charte visuelle : `donnees-business/design-system.md`
- Produit : `donnees-business/<sku>/fiche-produit.md`

---

## 2. Exécution Silencieuse via le Portail Pro-Pilot (`POST /api/feedback`)

```bash
set -a; source .env; set +a
python3 - "<sujet>" "<contenu_markdown>" "<partner_slug_si_multi>" <<'PY'
import os, sys, json, urllib.request, urllib.error

token = os.environ.get("PRO_PILOT_WRITE_TOKEN", "").strip()
if not token:
    print("Erreur: PRO_PILOT_WRITE_TOKEN manquant dans .env")
    sys.exit(1)

subject = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else "Note d'equipe"
content = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else "Contenu de la note"
partner = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else os.environ.get("PARTNER_SLUG", "")

payload = {"subject": subject, "content": content}
if partner:
    payload["partner"] = partner

req = urllib.request.Request(
    "https://pro-pilot.propulse-lab.com/api/feedback",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Pro-Pilot-CLI/2.0"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print(f"Succes: {res.get('path')} enregistre sur GitHub ({res.get('repo')}) - commit {str(res.get('commitSha', ''))[:7]}")
except urllib.error.HTTPError as err:
    print(f"Erreur HTTP {err.code}: {err.read().decode('utf-8')}")
    sys.exit(1)
PY
```

---

## 3. Confirmation Utilisateur

Confirmer sobrement l'enregistrement dans `donnees-business/_inbox/` sur GitHub en précisant le chemin retourné par l'API.
