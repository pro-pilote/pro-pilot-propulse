# Prise en Main — Pro-Pilot (`getting-started`)

Bienvenue dans **Pro-Pilot**, le socle d'instructions permettant de créer, prévisualiser et publier des objets web (`PAGE` HTML ou `DOCUMENT` PDF/image) ou d'importer des pages externes sur **Pro Web** via l'API officielle (`https://api-pro-web.propulse-lab.com`) avec votre assistant IA (Claude Code, Cursor, Antigravity).

## 1. Initialisation en 2 étapes (Zéro Dépendance)

1. **Configurer la clé API** : créez un fichier `.env` à la racine de votre dépôt partenaire `pro-pilot-<partenaire>` (ignoré par Git) :
   ```env
   PRO_WEB_API_KEY=votre_cle_api_pro_web
   ```
2. **Synchroniser le socle `.pro-pilot/`** (exécuté automatiquement par votre assistant IA à la lecture de `CLAUDE.md` / `AGENTS.md` / `RULES.md`) :
   ```bash
   if [ -d .pro-pilot/.git ]; then
     git -C .pro-pilot pull --ff-only
   else
     git clone --depth 1 https://github.com/pro-pilote/pro-pilot-propulse.git .pro-pilot
   fi
   ```

## 2. Questionnaire de Profilage Initial (Exécuté par l'IA au 1er lancement)

Lors de la toute première session d'un collaborateur (si `./.pro-pilot-profile.md` n'existe pas à la racine du dépôt partenaire), l'IA pose ces **3 questions courtes** :
1. **Quel est ton rôle principal ?** *(ex. Copywriter / Édito, Traffic Manager / Acquisition, Chef de projet, Intégrateur / Tech)*
2. **Sur quelle marque / Business Unit travailles-tu principalement ?** *(voir `donnees-business/README.md`)*
3. **Quel niveau d'accompagnement souhaites-tu ?**
   - **Mode Guidé (No-Code)** : l'IA s'occupe de toute la technique (`curl`, aperçu navigateur, publication API) et ne te pose que des questions métier.
   - **Mode Expert (Tech)** : l'IA affiche les payloads JSON et les réponses HTTP détaillées.

Les réponses sont enregistrées localement dans `./.pro-pilot-profile.md` (à la racine du dépôt partenaire, ignoré par Git ; ne jamais écrire dans `.pro-pilot/`).
