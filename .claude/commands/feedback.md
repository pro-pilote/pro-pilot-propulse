# Commande /feedback — Enregistrement et Synchronisation des Retours Partenaires

Cette commande permet a Claude d'enregistrer de facon autonome les retours d'experience, les corrections, les regles edifiees au cours des sessions et les preferences d'equipe, et de les synchroniser sur le depot GitHub du partenaire en mode append-only dans `donnees-business/_inbox/` sans conflit concurrentiel ni manipulation Git locale.

---

## 1. Declencheurs

Cette commande est executee :
- Soit a la demande explicite de l'utilisateur via `/feedback <description du retour>`
- Soit de maniere proactive par Claude des qu'un utilisateur formule une correction, une regle specifique, un retour sur un style ou une nouvelle mention legale.

---

## 2. Format & Stockage Append-Only

Toutes les notes sont conservees sous forme de fiches Markdown horodatees dans le dossier :
`donnees-business/_inbox/<date>_<auteur>_<sujet>_<uuid>.md`

Ce fonctionnement en mode append-only strict elimine tout risque d'ecrasement accidentel ou de conflit de fusion entre collaborateurs simultanes.

---

## 3. Garde-fous de Securite & Perimetre Autorise

Pour proteger l'integrite du harnais :
1. **Perimetre autorise (Allowlist)** :
   - Uniquement les notes destinees a `donnees-business/_inbox/`.
2. **Perimetre strictement interdit (Denylist)** :
   - Ne jamais modifier ni committer de scripts `.sh`, `.py`, `.js`.
   - Ne jamais modifier `.github/**`, `regles/**`, `ROUTER.md`, `.claude/commands/`.
   - Ne jamais committer de pages `*.html`, `*.htm`, `.tmp/`, `tmp/` ni de fichiers `.env`.

---

## 4. Execution Silencieuse du Commit via le Portail Pro-Pilot

Claude execute directement l'envoi securise vers le portail Pro-Pilot :

```bash
set -a; source .env; set +a
python3 - "<sujet>" "<contenu_markdown>" "<partner_slug_optionnel>" <<'PY'
import os, sys, json, urllib.request

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
        "Content-Type": "application/json"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print(f"Succes: {res.get('path')} enregistre sur GitHub ({res.get('repo')}) - commit {res.get('commitSha', '')[:7]}")
except urllib.error.HTTPError as err:
    print(f"Erreur HTTP {err.code}: {err.read().decode('utf-8')}")
    sys.exit(1)
PY
```

---

## 5. Confirmation Utilisateur

Une fois l'appel reussi, Claude confirme sobrement a l'utilisateur :
*« Votre note sur [sujet] a ete enregistree dans la boite de reception partagee (donnees-business/_inbox/) et synchronisee sur GitHub. Elle sera automatiquement prise en compte lors de nos prochaines sessions. »*
