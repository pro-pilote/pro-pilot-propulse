# Instructions d'Espace de Travail — Pro-Pilot

Tu opères dans un dossier local **Pro-Pilot** (`pro-pilot-<slug>/` ou `pro-pilot-multi/`).

## 1. Initialisation & Configuration

- Charge `.env` (`PRO_PILOT_WRITE_TOKEN`, `PARTNER_ID`, `PARTNER_NAME`).
- Suis les instructions de `https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/ROUTER.md` (ou du prompt de démarrage).
- **Ne jamais demander de clé Pro-Pilot à la main** : si un appel au portail renvoie `HTTP 401`, invite l'utilisateur à se reconnecter une fois sur `https://pro-pilot.propulse-lab.com/` pour actualiser son espace.
- **Ne jamais afficher de secrets ou jetons** issus de `.env` ou `~/.pro-web-static/wp-apps.json`.

## 2. Routage Automatique en Langage Naturel

Applique directement la compétence locale correspondante dès que l'intention correspond — sans attendre que l'utilisateur tape une commande slash :

- **Espace membre / plateforme abonné (`ai-child`)** :
  - Dès que l'utilisateur mentionne un **espace membre**, un **site abonné**, une **plateforme**, des **onglets**, des **blocs**, un **branding**, un **portefeuille**, ou le **nom / domaine d'un site** retourné par `GET https://pro-pilot.propulse-lab.com/api/ai-child/sites` $\rightarrow$ **lire et appliquer immédiatement `.claude/commands/pro-blocks.md`** (`/pro-blocks`).
  - **Interdiction absolue** : ne JAMAIS ouvrir `wp-login.php`, l'interface `/wp-admin/` dans un navigateur, ni lancer d'automatisation navigateur pour se connecter ou éditer un espace membre. Tout passe par `/pro-blocks`.
  - Si un repli direct demande un identifiant/mot de passe WordPress (`AUTH_MISSING`), ne lance jamais de saisie masquée ou bloquante dans le terminal : demande calmement à l'utilisateur dans le chat son identifiant et son Application Password WordPress.
- **Page web HTML, document PDF ou média Pro Web** :
  - Dès que l'utilisateur souhaite créer, modifier, prévisualiser ou publier une page web ou un document $\rightarrow$ **lire et appliquer `.claude/commands/pro-web.md`** (`/pro-web`).
- **Règle métier, correction ou retour d'expérience** :
  - Dès que l'utilisateur formule une règle ou corrige un résultat $\rightarrow$ **lire et appliquer `.claude/commands/learn.md`** (`/learn`).
