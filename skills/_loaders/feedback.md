# /feedback — Chargeur Dynamique Pro-Pilot

Avant toute réponse ou action :
1. Récupère en direct la dernière version officielle de la skill `feedback` depuis le socle public GitHub :
   ```bash
   curl -fsSL "https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/feedback/SKILL.md"
   ```
2. Applique strictement les instructions du `SKILL.md` récupéré pour enregistrer la règle ou le retour en mode append-only dans `donnees-business/_inbox/` via `POST https://pro-pilot.propulse-lab.com/api/feedback`.

$ARGUMENTS
