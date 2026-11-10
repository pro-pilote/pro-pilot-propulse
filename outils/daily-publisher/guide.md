# Guide Universel — `daily-publisher` (Email Marketing Cloud & Article Blog / Statique)

Ce guide définit le protocole universel de génération, de prévisualisation locale en **2 étapes non-techniques** (**① Daily Email** $\rightarrow$ **② Article sur le blog**) et de publication multi-canal via l'**API REST Salesforce Marketing Cloud**, l'**API REST WordPress** (`type: "BLOG"`) ou l'**API Pro Web** (`type: "STATIC"`).

---

## 1. Périmètre & Contrat Métier

Lorsqu'un éditeur dépose son document source (Google Doc ou fichier `.docx` / `.html`) et indique la liste cible (ex. `LVP`, `LIVE`, `LIBRES`, `CLUB`), l'IA :
1. Lit `./outils/daily-publisher/variables.md`, `./outils/daily-publisher/specificites.md` et `./outils/daily-publisher/erreurs-connues.md` du dépôt partenaire.
2. Vérifie que le champ `sfmc_folder_status` de la liste ne commence pas par `"TEMPORIZED"` (`sfmc_folder_status.startsWith("TEMPORIZED")`). Toute liste temporisée (ex. `"TEMPORIZED_SINCE_2026_09_12"`) est bloquée en fail-closed sauf déverrouillage explicite demandé par l'utilisateur (`--force-temporized`).
3. Génère le Studio visuel local en 2 étapes (`preview-dual.html`) ainsi que les fichiers éditables (`editable-email.html`, `editable-article.html`, `editable-meta.json`) et le manifeste scellé (`manifest.json`), sans jargon technique (aucun hash, aucun ID de dossier, aucune commande shell ni code HTML brut exposés dans l'interface).

---

## 2. Étape 1 — Studio Visuel Local en 2 Étapes & Scellement SHA-256 Anti-TOCTOU

1. **Parcours Éditeur en 2 Étapes (`preview-dual.html`)** :
   - **① Daily (Email)** : édition directe WYSIWYG (`contenteditable="true"`) de l'objet (`data-field="daily.subjectline"`), du pré-header (`data-field="daily.preheader"`), de l'en-tête (`data-field="daily.email_header"`), du corps du mail (`data-field="daily.email_body"`) et du pied de page (`data-field="daily.email_footer"`).
   - **② Article sur le blog** : édition directe WYSIWYG du titre (`data-field="daily.article_title"`) et du corps de l'article (`data-field="daily.article_body"`).
2. **Squelette Blanc & Tokens DTCG** :
   - Balise racine `<html lang="fr" data-mode="skeleton" data-partner="<aws_slug>">` et cascade `@layer skeleton, theme;` utilisant les custom properties `--daily-primary`, `--daily-accent`, `--daily-bg`, `--daily-text`, `--daily-muted` (contraste WCAG AA $\ge 4.5:1$ obligatoire).
3. **Double Contrôle Fail-Closed Anti-TOCTOU avant Publication** :
   - Toute retouche (via le bouton **Enregistrer les retouches** du Studio ou par l'IA sur `editable-email.html`, `editable-article.html`, `editable-meta.json`) met à jour `manifest.json` et recalcule l'empreinte `previewHash` via `computePreviewSealHash({ listId, assetName, site, salesforce, meta, emailHtml, webHtml, images })`.
   - Au moment du `OUI` de publication, le publieur vérifie en fail-closed :
     1. que le `computePreviewSealHash` recalculé est **strictement égal** à `manifest.previewHash`, et
     2. que le contenu sur disque de `editable-email.html` et `editable-article.html` est **strictement égal** octet par octet à `manifest.emailHtml` et `manifest.webHtml`. En cas d'écart, la publication est immédiatement avortée (`FAIL-CLOSED ANTI-TOCTOU`).

---

## 3. Étape 2 — Publication Email via API REST Marketing Cloud (Blocs 195, Email 207 & Vérification GET)

1. **Authentification OAuth2 S2S** :
   ```bash
   curl -sS -X POST "https://${SFMC_SUBDOMAIN}.auth.marketingcloudapis.com/v2/token" \
     -H "Content-Type: application/json" \
     -d "{
       \"grant_type\": \"client_credentials\",
       \"client_id\": \"${SFMC_CLIENT_ID}\",
       \"client_secret\": \"${SFMC_CLIENT_SECRET}\",
       \"account_id\": \"${SFMC_ACCOUNT_ID}\"
     }"
   ```
   Vérifier que la réponse contient les scopes `saved_content_write` et `documents_and_images_write`.
2. **Sauvegarde Pré-Écriture & Images Inline (`#628882`)** :
   - Si le bloc `#195` ou l'email `#207` cible existe déjà, sauvegarder son JSON complet dans `backups/sfmc-<assetId>.json`.
   - Pour chaque image inline `{{IMG_<hash>}}`, uploader l'asset dans `sfmc_images_folder_id` via `POST https://${SFMC_SUBDOMAIN}.rest.marketingcloudapis.com/asset/v1/content/assets` et remplacer `{{IMG_<hash>}}` par `fileProperties.publishedURL`.
3. **Création / Mise à jour du Bloc `freeformblock` (`195`) & de l'Email `templatebasedemail` (`207`)** :
   - Créer ou mettre à jour le bloc `assetType: { "id": 195, "name": "freeformblock" }` dans `sfmc_content_folder_id` via `POST` / `PATCH https://${SFMC_SUBDOMAIN}.rest.marketingcloudapis.com/asset/v1/content/assets`.
   - Cloner la structure du modèle `sfmc_reference_email_id` (`assetType.id: 207`), injecter le HTML du bloc `195` dans le slot dédié, renseigner `views.subjectline.content` et `views.preheader.content`, puis créer ou mettre à jour l'email dans `sfmc_brand_folder_id`.
4. **Vérification Post-Écriture Obligatoire (`GET`) & Rollback** :
   - Appeler `GET https://${SFMC_SUBDOMAIN}.rest.marketingcloudapis.com/asset/v1/content/assets/${EMAIL_ASSET_ID}` et vérifier que `views.subjectline.content` et le condensat `SHA-256` du HTML injecté dans le slot `195` correspondent au payload validé. En cas d'écart, restaurer immédiatement `backups/sfmc-<assetId>.json` via `PATCH`.

---

## 4. Étape 3A — Publication Article sur Blog WordPress (`type: "BLOG"`) via WP REST API

1. **Identifiants par Liste (`.env`)** :
   - Utiliser `WP_APP_USER_<LISTE>` et `WP_APP_PASSWORD_<LISTE>` (avec repli sur `WP_APP_USER` et `WP_APP_PASSWORD`).
2. **Contrôle Pré-Vol d'Idempotence & Sauvegarde** :
   - Appeler `GET https://${WP_ADMIN_DOMAIN}/wp-json/wp/v2/posts?slug=${SLUG}&status=any` avec `-u "${WP_USER}:${WP_PASS}"`.
   - Si un article existe déjà (`id`), sauvegarder son JSON complet dans `backups/wp-post-${POST_ID}.json`.
3. **Upload des Médias & Publication de l'Article** :
   - Uploader chaque image inline via `POST https://${WP_ADMIN_DOMAIN}/wp-json/wp/v2/media` et remplacer `{{IMG_<hash>}}` par `source_url`.
   - Créer (`POST /wp-json/wp/v2/posts`) ou mettre à jour (`POST /wp-json/wp/v2/posts/${POST_ID}`) l'article avec `{"title": "...", "slug": "...", "status": "publish", "content": "...", "excerpt": "..."}`.
4. **Purge CloudFront & Vérification Anonyme Post-Publication** :
   - Appeler `POST https://${WP_ADMIN_DOMAIN}/wp-json/Core/v1/cloudfront-flush`.
   - Vérifier en anonyme `curl -sS "https://${DOMAIN_NAME}/${SLUG}/"` (`HTTP 200` + présence du `<h1` attendu). En cas d'échec, restaurer `backups/wp-post-${POST_ID}.json`.

---

## 5. Étape 3B — Publication Article sur Site Statique (`type: "STATIC"`) via Pro Web API

1. **Contrôle Pré-Vol & Scripts Obligatoires** :
   - Appeler `GET https://api-pro-web.propulse-lab.com/objects/list/${WEBSITE_ID}` avec headers `x-api-key: ${PRO_WEB_API_KEY}` et `x-partner-id: ${PARTNER_ID}`. Si `<slug>/index.html` existe déjà, sauvegarder la page publique actuelle dans `backups/${SLUG}.html`.
   - Toute page d'article statique générée doit inclure dans `<head>` :
     ```html
     <script src="https://cdn.info-contenu.io/assets/headerTools.js" type="text/javascript"></script>
     <script src="https://cdn.info-contenu.io/assets/preserveParamsV2.js" type="text/javascript"></script>
     ```
2. **Upload des Images (`DOCUMENT`) & de l'Article en Double Arborescence (`PAGE`)** :
   - Pour chaque image : `POST https://api-pro-web.propulse-lab.com/objects/signed-url` $\rightarrow$ `PUT <signedUrl>` $\rightarrow$ `POST https://api-pro-web.propulse-lab.com/objects/upsert` avec `type: "DOCUMENT"`, `subtype: "DOCUMENT:IMAGE"` et `key: "assets/images/daily/<slug>/img_<hash>.<ext>"`.
   - Pour l'article HTML, exécuter la séquence `signed-url` $\rightarrow$ `PUT` $\rightarrow$ `upsert` (`type: "PAGE"`, `subtype: "PAGE:OTHER"`) sur les **2 clés** (chacune contenant un `/`) :
     1. `key: "<slug>/index.html"`
     2. `key: "articles/<slug>"`
3. **Vérification Anonyme & Rollback** :
   - Vérifier `curl -sS "https://${DOMAIN_NAME}/${SLUG}/"` (`HTTP 200` + `<h1` attendu). En cas d'anomalie, ré-uploader `backups/${SLUG}.html`.

---

## 6. Retouche Collaborative (Pull & PATCH) & Procédure de Rollback

- Tout collaborateur disposant du dépôt partenaire peut rapatrier un Daily existant depuis Marketing Cloud (`GET /asset/v1/content/assets/${ASSET_ID}`) et le site web (`GET /wp-json/wp/v2/posts?slug=${SLUG}` ou `https://${DOMAIN_NAME}/${SLUG}/`) dans le Studio 2 étapes local, effectuer ses retouches, resceller `manifest.json` et mettre à jour en place (`PATCH` Marketing Cloud + `POST` WordPress / `upsert` Pro Web).
