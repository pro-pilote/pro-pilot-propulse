# /daily-publisher — Chargeur Dynamique Pro-Pilot

Avant toute réponse ou action :
1. Récupère en direct la dernière version officielle de la skill `daily-publisher` depuis le socle public GitHub :
   ```bash
   curl -fsSL "https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/daily-publisher/SKILL.md"
   ```
2. Applique strictement toutes les instructions du `SKILL.md` récupéré (chargement de `.env`, lecture en temps réel de `skills/daily-publisher/*` sur le dépôt partenaire via `GET https://pro-pilot.propulse-lab.com/api/repo` avec `$PRO_PILOT_WRITE_TOKEN`, Studio 2 étapes scellé SHA-256 et validation humaine).

$ARGUMENTS
