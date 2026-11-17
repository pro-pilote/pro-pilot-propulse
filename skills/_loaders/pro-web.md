# /pro-web — Chargeur Dynamique Pro-Pilot

Avant toute réponse ou action :
1. Récupère en direct la dernière version officielle de la skill `pro-web` depuis le socle public GitHub :
   ```bash
   curl -fsSL "https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/pro-web/SKILL.md"
   ```
2. Applique strictement toutes les instructions du `SKILL.md` récupéré (chargement de `.env`, lecture en temps réel de `skills/pro-web/*` et `donnees-business/*` sur le dépôt partenaire via `GET https://pro-pilot.propulse-lab.com/api/repo` avec `$PRO_PILOT_WRITE_TOKEN`, aperçu `.tmp/` et validation humaine avant écriture).

$ARGUMENTS
