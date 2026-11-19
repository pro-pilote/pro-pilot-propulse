# /pro-blocks — Chargeur Dynamique Pro-Pilot (Partenaires Finance)

Avant toute réponse ou action :
1. Récupère en direct la dernière version officielle de la skill `pro-blocks` depuis le socle public GitHub :
   ```bash
   curl -fsSL "https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/pro-blocks/SKILL.md"
   ```
2. Applique strictement toutes les instructions du `SKILL.md` récupéré (chargement de `.env`, détection dynamique des sites Fulfi via `GET /api/ai-child/sites` avec `$PRO_PILOT_WRITE_TOKEN`, patch minimal sur `overrides`, contrôle CAS `baseVersion`, validation dry-run `POST /validate`, validation humaine explicite et publication `PUT`).

$ARGUMENTS
