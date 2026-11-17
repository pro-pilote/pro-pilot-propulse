# Garde-fous de Sécurité & Préservation de la Production

## 1. Validation Humaine Obligatoire avant toute Écriture S3 / API
- Toute action qui crée ou modifie un objet en production (`POST /objects/signed-url` + `PUT <signedUrl>`, `POST /objects/upsert`) exige :
  1. Un contrôle préalable via `GET /objects/list/{websiteId}` pour vérifier si la `key` existe déjà (et, en cas de mise à jour, une sauvegarde locale de la version en ligne dans `.tmp/backups/`).
  2. La validation locale de l'aperçu (`.tmp/preview-<slug>.html`) par l'utilisateur.
  3. **L'accord explicite de l'utilisateur dans le chat** en précisant le domaine cible, le `websiteId` correspondant et la `key` exacte avant d'exécuter les requêtes HTTP d'écriture.
- **Suppression non autorisée en v1 par sécurité** : Aucune commande de suppression d'objet n'est autorisée par API. Toute suppression définitive doit être exécutée manuellement depuis l'interface web Pro Web.

## 2. Protection des Scripts Pro Web (`headerTools.js`, `preserveParamsV2.js`, `GTM`, `leadBox`)
- Toute page HTML (`PAGE`) générée ou modifiée doit inclure ou conserver intacts les scripts officiels Pro Web (`https://cdn.info-contenu.io/assets/`) :
  - `<script src="https://cdn.info-contenu.io/assets/headerTools.js" type="text/javascript"></script>`,
  - `<script src="https://cdn.info-contenu.io/assets/preserveParamsV2.js" type="text/javascript"></script>`,
  - Les scripts Google Tag Manager (`GTM-XXXXXXX` dans `<head>` et `<noscript>` dans `<body>`),
  - Les scripts de formulaires d'opt-in (`leadBox-v1.0.0.js`, `email-autocomplete.js`, `eventTriggerV1.js`, `redirect-v1.0.0.js`, `intlTelInput.js`), les balises `<form>` et le pied de page légal.

## 3. Sécurité des Secrets & Anti-TOCTOU Daily
- Ne jamais committer ni afficher en clair le fichier `.env` ou les clés `PRO_WEB_API_KEY`, `PRO_PILOT_WRITE_TOKEN`, `SFMC_CLIENT_SECRET` et `WP_APP_PASSWORD_*`.
- Pour toute publication via `daily-publisher`, vérifier en fail-closed le scellement `SHA-256` (`manifest.previewHash` + égalité stricte de `editable-email.html` et `editable-article.html`), bloquer toute liste dont `sfmc_folder_status` commence par `"TEMPORIZED"`, sauvegarder l'existant dans `.tmp/backups/` avant mise à jour et vérifier en `GET` le contenu réellement écrit sur Marketing Cloud et sur le site public.

## 4. Périmètres Lecture / Écriture du Dépôt Partenaire via le Portail
- Lecture en temps réel (`GET /api/repo`) : restreinte strictement à `donnees-business/**` et `skills/**` du dépôt associé au jeton `PRO_PILOT_WRITE_TOKEN`.
- Écriture auto-apprenante (`POST /api/feedback`) : append-only exclusivement dans `donnees-business/_inbox/<ISO>_<auteur>_<sujet>_<uuid8>.md` (committer `it-pro-pilot`, auteur = email Google vérifié).
