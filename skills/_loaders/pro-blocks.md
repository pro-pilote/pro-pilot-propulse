# /pro-blocks — Chargeur Dynamique Pro-Pilot (Partenaires Finance)

Avant toute réponse ou action :
1. Récupère en direct la dernière version officielle de la skill `pro-blocks` depuis le socle public GitHub :
   ```bash
   curl -fsSL "https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/pro-blocks/SKILL.md"
   ```
2. Applique strictement toutes les instructions du `SKILL.md` récupéré (chargement de `.env`, détection dynamique des sites Fulfi via `GET /api/ai-child/sites` avec `$PRO_PILOT_WRITE_TOKEN`, appels REST directs vers `https://www-admin.<domain>/wp-json/ai-child/v1/platform` via Application Password WordPress et `pro-ips`, garde-fous `detect_defaults_freeze` + `detect_destructive_nav` sur `overrides`, contrôle CAS `baseVersion`, validation dry-run `POST .../validate`, validation humaine explicite et publication `PUT`).

$ARGUMENTS
