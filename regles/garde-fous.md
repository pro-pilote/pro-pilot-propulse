# Garde-fous de Sécurité & Préservation de la Production

## 1. Validation Humaine Obligatoire avant toute Écriture S3 / API
- Toute action qui crée ou modifie un objet en production (`POST /objects/signed-url` + `PUT <signedUrl>`, `POST /objects/upsert`) exige :
  1. Un contrôle préalable via `GET /objects/list/{websiteId}` pour vérifier si la `key` existe déjà (et, en cas de mise à jour, une sauvegarde locale de la version en ligne dans `backups/`).
  2. La validation locale de l'aperçu par l'utilisateur.
  3. **L'accord explicite de l'utilisateur dans le chat** en précisant le domaine cible, le `websiteId` correspondant et la `key` exacte avant d'exécuter les requêtes HTTP d'écriture.
- **Suppression non autorisée en v1 par sécurité** : Aucune commande de suppression d'objet n'est autorisée par API. Toute suppression définitive doit être exécutée manuellement depuis l'interface web Pro Web.

## 2. Protection des Scripts Pro Web (`headerTools.js`, `preserveParamsV2.js`, `GTM`, `leadBox`)
- Toute page HTML (`PAGE`) générée ou modifiée doit inclure ou conserver intacts les scripts officiels Pro Web (`https://cdn.info-contenu.io/assets/`) :
  - `<script src="https://cdn.info-contenu.io/assets/headerTools.js" type="text/javascript"></script>` (lecture sécurisée des paramètres d'URL via `getParameterByName`),
  - `<script src="https://cdn.info-contenu.io/assets/preserveParamsV2.js" type="text/javascript"></script>` (propagation automatique des paramètres `utm_*`, `leadcode`, `salescode`, `bdc`, `url2`/`bdc2`, `urlBdc` vers les liens et bons de commande `https://secure.bdc.com`),
  - Les scripts Google Tag Manager (`GTM-XXXXXXX` dans `<head>` et `<noscript>` dans `<body>`),
  - Les scripts de formulaires d'opt-in (`https://cdn.info-contenu.io/assets/leadBox-v1.0.0.js`, `email-autocomplete.js`, `eventTriggerV1.js`, `redirect-v1.0.0.js`, `intlTelInput.js`), les balises `<form>` et le pied de page légal (Mentions légales, CGV, Politique de confidentialité).

## 3. Sécurité des Secrets, Anti-TOCTOU Daily & Socle `.pro-pilot/`
- Ne jamais committer ni afficher en clair le fichier `.env` ou les clés `PRO_WEB_API_KEY`, `SFMC_CLIENT_SECRET` et `WP_APP_PASSWORD_*`.
- Pour toute publication via `daily-publisher`, vérifier systématiquement en fail-closed le scellement `SHA-256` (`manifest.previewHash` + égalité stricte de `editable-email.html` et `editable-article.html`), bloquer toute liste dont `sfmc_folder_status` commence par `"TEMPORIZED"`, sauvegarder l'existant dans `backups/` avant mise à jour et vérifier en `GET` le contenu réellement écrit sur Marketing Cloud et sur le site public.
- Ne jamais modifier ni écrire de fichier dans le dossier `.pro-pilot/` (le profil utilisateur local est stocké dans `./.pro-pilot-profile.md` à la racine du dépôt partenaire).

## 4. Alimentation du Dépôt Partenaire & Périmètre d'Écriture
- Le partenaire a vocation à enrichir en continu son propre dépôt avec ses spécificités métier au format standardisé.
- Périmètre autorisé en écriture : `donnees-business/**` (fiches produits, design system) et `outils/**` (`variables.md`, `specificites.md`, `erreurs-connues.md`, `guide.md`).
- Périmètre strictement protégé (lecture seule) : `tools/**`, `.github/**`, `regles/**`, `ROUTER.md`, `RULES.md`, `.gitignore`, scripts exécutables.
- Signature des commits : committer `it-pro-pilot <it-pro-pilot@users.noreply.github.com>`, auteur `<sub_email>`, authentification via jeton nominatif 6 mois (`pro-pilot-auth.cfg`, expiration 180 jours = 15 552 000 secondes).
