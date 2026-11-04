# Getting Started — Starter Pack Pro-Pilot

Bienvenue dans **Pro-Pilot**. Ce dossier permet à votre assistant IA (Claude Code, Cursor, ChatGPT, Grok, Antigravity) de connaître votre métier, vos produits et d'exécuter vos actions sur Pro Web via l'API publique en toute sécurité.

## Étape 0 — Prérequis Techniques (1 seule fois)

1. Créez un fichier `.env` à la racine de votre dépôt partenaire avec la clé API fournie par Propulse Lab :
   ```env
   PRO_WEB_API_KEY=votre_cle_api_ici
   ```
2. Votre assistant IA synchronise automatiquement le socle de règles dans `.pro-pilot/` (ignoré par Git) via :
   ```bash
   [ -d .pro-pilot ] && git -C .pro-pilot pull --ff-only || git clone --depth 1 https://github.com/pro-pilote/pro-pilot-propulse.git .pro-pilot
   ```

## Étape 1 — Premier lancement (Onboarding)

Lors de votre toute première session, votre IA vous pose **4 questions rapides** :
1. **Qui êtes-vous ?** (Votre organisation / marque et votre rôle)
2. **Quel est votre périmètre au quotidien ?** (Édito, Acquisition, ou actions ciblées)
3. **Confirmation de vos actions :** l'IA vous propose la liste des actions correspondant à votre besoin et vous demande de la confirmer.
4. **Votre niveau technique :** pour adapter son vocabulaire (zéro jargon technique si vous préférez une approche 100 % métier).

Vos réponses sont enregistrées uniquement sur votre ordinateur dans `.pro-pilot/profile.md`.

## Étape 2 — Utilisation au quotidien

Exprimez simplement votre demande en langage naturel et glissez vos pièces jointes (Google Docs, PDF, brief) :
- *« Crée une page HTML de présentation à partir de ce document et publie cet objet sur Pro Web. »*
- *« Importe cette URL Leadpages sur notre site Pro Web. »*

Votre IA consulte automatiquement le routeur [`ROUTER.md`](../ROUTER.md), charge les fiches de votre dépôt partenaire et appelle l'API Pro Web après votre validation.
