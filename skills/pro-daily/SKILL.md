---
name: pro-daily
description: Preparation, Studio visuel 2 etapes scelle SHA-256 et publication coordonnee d'un Daily dans Salesforce Marketing Cloud et sur Blog WordPress ou Site Statique Pro Web.
---

# Skill `/pro-daily` — Email Marketing Cloud & Article Blog / Statique

> **Statut : Non exposé aux partenaires — En cours de développement actif (Interne)**
> Cette skill est en cours d'intégration (Salesforce Marketing Cloud + Blog / Statique). Elle n'est pas encore activée sur les espaces partenaires.

Cette skill définit le protocole universel de génération, de prévisualisation locale en **2 étapes non-techniques** (**① Daily Email** $\rightarrow$ **② Article sur le blog**) et de publication multi-canal via l'**API REST Salesforce Marketing Cloud**, l'**API REST WordPress** (`type: "BLOG"`) ou l'**API Pro Web** (`type: "STATIC"`).

---

## 1. Contexte & Lecture Live du Dépôt Partenaire (`GET /api/repo`)

Lorsqu'un éditeur dépose son document source (Google Doc ou fichier `.docx` / `.html`) et indique la liste cible (ex. `LISTE_A`, `LISTE_B`) :
1. Charger `.env` (`[ -f .env ] && { set -a; source .env; set +a; }`) et lire en direct via `GET https://pro-pilot.propulse-lab.com/api/repo?path=...` (`Authorization: Bearer ${PRO_PILOT_WRITE_TOKEN}`, avec `&partner=<slug>` si mode multi-partenaires) :
   - `skills/pro-daily/variables.md`
   - `skills/pro-daily/specificites.md`
   - `skills/pro-daily/erreurs-connues.md`
2. Vérifier que `sfmc_folder_status` de la liste ne commence pas par `"TEMPORIZED"` (`sfmc_folder_status.startsWith("TEMPORIZED")`). Toute liste temporisée est bloquée en fail-closed sauf déverrouillage explicite demandé par l'utilisateur (`--force-temporized`).
3. Générer dans `.tmp/daily-<slug>/` le Studio visuel local en 2 étapes (`preview-dual.html`), les fichiers éditables (`editable-email.html`, `editable-article.html`, `editable-meta.json`) et le manifeste scellé (`manifest.json`), sans jargon technique dans l'interface.

---

## 2. Étape 1 — Studio Visuel Local en 2 Étapes & Scellement SHA-256 Anti-TOCTOU

1. **Parcours Éditeur en 2 Étapes (`preview-dual.html`)** :
   - **① Daily (Email)** : édition directe WYSIWYG (`contenteditable="true"`) de `daily.subjectline`, `daily.preheader`, `daily.email_header`, `daily.email_body`, `daily.email_footer`.
   - **② Article sur le blog** : édition directe WYSIWYG de `daily.article_title` et `daily.article_body`.
2. **Squelette Blanc & Tokens DTCG** :
   - `<html lang="fr" data-mode="skeleton" data-partner="<aws_slug>">` et `@layer skeleton, theme;` avec `--daily-primary`, `--daily-accent`, `--daily-bg`, `--daily-text`, `--daily-muted` (WCAG AA $\ge 4.5:1$).
3. **Double Contrôle Fail-Closed Anti-TOCTOU avant Publication** :
   - Toute retouche met à jour `manifest.json` et recalcule `previewHash` (`computePreviewSealHash`).
   - Au `OUI` de publication, vérifier en fail-closed : (1) égalité stricte du `computePreviewSealHash` recalculé avec `manifest.previewHash`, et (2) égalité octet par octet de `editable-email.html` et `editable-article.html` avec `manifest.emailHtml` et `manifest.webHtml`.

---

## 3. Étape 2 — Publication Email via API REST Marketing Cloud (`#195` + `#207`)

1. **Authentification OAuth2 S2S** : `POST https://${SFMC_SUBDOMAIN}.auth.marketingcloudapis.com/v2/token` (`client_credentials`), vérifier les scopes `saved_content_write` et `documents_and_images_write`.
2. **Sauvegarde Pré-Écriture & Images Inline** :
   - Si le bloc `#195` ou l'email `#207` existe déjà, sauvegarder son JSON complet dans `.tmp/backups/sfmc-<assetId>.json`.
   - Uploader chaque image inline `{{IMG_<hash>}}` dans `sfmc_images_folder_id` (`POST /asset/v1/content/assets`) et remplacer par `fileProperties.publishedURL`.
3. **Création / Mise à jour du Bloc `freeformblock` (`195`) & de l'Email `templatebasedemail` (`207`)** :
   - Créer/mettre à jour le bloc `195` dans `sfmc_content_folder_id`, cloner `sfmc_reference_email_id` (`207`), injecter le HTML du slot `195`, `views.subjectline.content` et `views.preheader.content` dans `sfmc_brand_folder_id`.
4. **Vérification Post-Écriture (`GET`) & Rollback** :
   - Vérifier en `GET /asset/v1/content/assets/${EMAIL_ASSET_ID}` l'objet et le `SHA-256` du HTML injecté ; restaurer `.tmp/backups/sfmc-<assetId>.json` via `PATCH` en cas d'écart.

---

## 4. Étape 3A — Publication Article sur Blog WordPress (`type: "BLOG"`)

1. Utiliser `WP_APP_USER_<LISTE>` / `WP_APP_PASSWORD_<LISTE>` (repli `WP_APP_USER` / `WP_APP_PASSWORD`).
2. Contrôler l'existant via `GET https://${WP_ADMIN_DOMAIN}/wp-json/wp/v2/posts?slug=${SLUG}&status=any` (sauvegarde `.tmp/backups/wp-post-${POST_ID}.json` si existant).
3. Uploader les médias (`POST /wp-json/wp/v2/media`), publier l'article (`POST /wp-json/wp/v2/posts`), purger CloudFront (`POST /wp-json/Core/v1/cloudfront-flush`) et vérifier `curl -sS "https://${DOMAIN_NAME}/${SLUG}/"` (`HTTP 200` + `<h1`).

---

## 5. Étape 3B — Publication Article sur Site Statique (`type: "STATIC"`) via Pro Web API

1. Vérifier `GET https://api-pro-web.propulse-lab.com/objects/list/${WEBSITE_ID}?partnerId=${PARTNER_ID}` (`x-api-key: ${PRO_WEB_API_KEY}`), sauvegarder l'existant dans `.tmp/backups/${SLUG}.html` et inclure `headerTools.js` + `preserveParamsV2.js`.
2. Uploader les images (`DOCUMENT:IMAGE`, `key: "assets/images/daily/<slug>/img_<hash>.<ext>"`) puis l'article HTML (`PAGE:OTHER`) sur la clé propre sans slash final : `key: "articles/<slug>"` (ne jamais utiliser `<slug>/index.html` qui provoque un `500` sur `/<slug>/`).
3. Vérifier `curl -sS "https://${DOMAIN_NAME}/articles/${SLUG}"` (`HTTP 200` + `<h1`) sans slash final.
