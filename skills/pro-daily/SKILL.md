---
name: pro-daily
version: "0.9.0"
description: Preparation, Studio visuel 2 etapes scelle SHA-256 et publication coordonnee d'un Daily dans Salesforce Marketing Cloud et sur Blog WordPress ou Site Statique Pro Web.
---

# Skill `/pro-daily` — Email Marketing Cloud & Article Blog / Statique

> **Statut : Non exposé aux partenaires — En cours de développement actif (Interne)**
> Cette skill est en cours d'intégration (Salesforce Marketing Cloud + Blog / Statique). Elle n'est pas encore activée sur les espaces partenaires.

Cette skill définit le protocole universel de génération, de prévisualisation locale en **2 étapes non-techniques** (**① Daily Email** $\rightarrow$ **② Article sur le blog**) et de publication multi-canal via l'**API REST Salesforce Marketing Cloud**, l'**API REST WordPress** (`type: "wp-blog"`) ou l'**API publique Pro Web** (`type: "static"`).

---

## 1. Contexte, Lecture Live & Résolution Déclarative RFC 7396 (`GET /api/repo`)

Lorsqu'un éditeur dépose son document source (Google Doc ou fichier `.docx` / `.html`) et indique la liste cible (ex. `LISTE_A`, `LISTE_B`) :
1. Charger la configuration locale (`.env`) et lire en direct via `GET https://pro-pilot.propulse-lab.com/api/repo?path=...` (`Authorization: Bearer ${PRO_PILOT_WRITE_TOKEN}`, avec `&partner=<slug>` si mode multi-partenaires) :
   - `skills/pro-daily/variables.md` *(contient le bloc JSON clôturé `daily_lists` fusionné en RFC 7396 sur les défauts locaux par `resolveListConfig` — zéro `if (partner)` en dur et zéro `websiteId` dans le socle public)*
   - `skills/pro-daily/specificites.md`
   - `skills/pro-daily/erreurs-connues.md`
2. **Format déclaratif du bloc `daily_lists` dans `skills/pro-daily/variables.md` du dépôt privé partenaire** :
   ````markdown
   ```json daily_lists
   {
     "CODE_LISTE": {
       "list_id": "CODE_LISTE",
       "label": "Nom de la Publication",
       "partner_id": 12,
       "partner_slug": "mon-partenaire",
       "site": {
         "type": "static",
         "domain": "www.exemple-partenaire.com",
         "website_id": "<OBJECT_ID_24_HEX_DANS_DEPOT_PRIVE>",
         "partner_id": 12,
         "articles_dir": "/",
         "design": {
           "brand_name": "Nom de la Publication",
           "primary_color": "#1B2A4A",
           "accent_color": "#8A6200",
           "bg_color": "#FAF8F5"
         }
       }
     }
   }
   ```
   ````
3. Vérifier en fail-closed qu'aucun statut de la liste (`status`, `site.status`, `site.publication_status`, `salesforce.sfmc_folder_status`) ne commence par `"TEMPORIZED"`, `"PAUSED"` ou `"DISABLED"`, **quelle que soit la cible (`all`, `web` ou `sfmc`)**, sauf déverrouillage explicite demandé par l'utilisateur (`--force-temporized`).
4. Générer dans `.tmp/daily-<slug>/` (après validation stricte du slug `/^[a-z0-9]+(?:-[a-z0-9]+)*$/`) le Studio visuel local en 2 étapes (`preview-dual.html`), les fichiers éditables (`editable-email.html`, `editable-article.html`, `editable-meta.json`) et le manifeste scellé (`manifest.json`), sans jargon technique dans l'interface.

---

## 2. Étape 1 — Studio Visuel Local en 2 Étapes & Scellement HMAC-SHA256 Anti-TOCTOU

1. **Parcours Éditeur en 2 Étapes (`preview-dual.html`)** :
   - **① Daily (Email)** : édition directe WYSIWYG (`contenteditable="true"`) de `daily.subjectline`, `daily.preheader`, `daily.email_header`, `daily.email_body`, `daily.email_footer`.
   - **② Article sur le blog** : édition directe WYSIWYG de `daily.article_title` et `daily.article_body`.
2. **Squelette Blanc & Tokens DTCG** :
   - `<html lang="fr" data-mode="skeleton" data-partner="<aws_slug>">` en preview (`data-mode="live"` en production) et `@layer skeleton, theme;` avec `--daily-primary`, `--daily-on-primary`, `--daily-accent`, `--daily-bg`, `--daily-surface`, `--daily-border`, `--daily-text`, `--daily-muted` (WCAG AA $\ge 4.5:1$).
3. **Double Contrôle Fail-Closed Anti-TOCTOU avant Publication** :
   - Toute retouche met à jour `manifest.json` et recalcule `previewHash` (`computePreviewSealHash` signant par HMAC local le contenu texte, les métadonnées et le `SHA-256` réel du `base64` de chaque image).
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

## 4. Étape 3A — Publication Article sur Blog WordPress (`type: "wp-blog"`)

1. Résoudre l'authentification Application Password par ordre de priorité : `WP_APP_USER_<LISTE>` / `WP_APP_PASSWORD_<LISTE>` $\rightarrow$ `WP_APP_USER` / `WP_APP_PASSWORD` (uniquement si `PARTNER_ID === site.partner_id`) $\rightarrow$ `~/.pro-web-static/wp-apps.json`.
2. Exécuter le pre-flight réel `GET https://${WP_ADMIN_DOMAIN}/wp-json/wp/v2/users/me?context=edit` (cloisonnement `PARTNER_ID` fail-closed + discrimination `200`, `401/403` et `500 server: AmazonS3` en cas de filtrage WAF `pro-ips`), puis contrôler l'existant via `GET /wp-json/wp/v2/posts?slug=${SLUG}&status=any&context=edit` (sauvegarde `.tmp/backups/wp-post-${POST_ID}.json` et préservation du statut existant sauf `--wp-status` explicite).
3. Uploader les médias (`POST /wp-json/wp/v2/media`, nettoyés par `DELETE ?force=true` si l'écriture du post échoue), renseigner `featured_media` avec la 1re image téléversée, publier l'article gratuit (`POST /wp-json/wp/v2/posts` avec `categories` éventuelles), purger CloudFront (`POST /wp-json/Core/v1/cloudfront-flush`) et vérifier `curl -sS -m 10 "https://${DOMAIN_NAME}/${SLUG}/"` (`HTTP 200` + `<h1`).

---

## 5. Étape 3B — Publication Article sur Site Statique / Vibecodé (`type: "static"`)

1. **Génération Hybride Sécurisée (JSON + Clé HTML sans slash final)** :
   - Clé HTML calculée dynamiquement sans slash final : `articlesPrefix = (site.articles_dir || '/').replace(/^\/+|\/+$/g, '')` $\rightarrow$ `cleanHtmlKey = articlesPrefix ? "${articlesPrefix}/${slug}" : slug` $\rightarrow$ `urls.html = "/${cleanHtmlKey}"` (jamais `/index.html` ni slash final, qui renvoient `500` sur CloudFront `STATIC`).
   - Sanitisation whitelist par tokenizer (`sanitizeArticleHtml`) appliquée en amont sur **la page HTML `<cleanHtmlKey>` ET la fiche `/articles/<slug>.json`** (autorise uniquement les balises éditoriales saines, décode les entités avant validation des URLs `https:`, `mailto:`, `/`).
   - `/articles.json` : index chronologique prenant l'index distant comme unique source de vérité en mode push (`GET https://${DOMAIN_NAME}/articles.json?v=${TS}` avec `Cache-Control: no-cache`, fail-closed s'il existe dans `/objects/list` mais échoue à la lecture).
2. **Déploiement Atomique S3 / CloudFront via l'API publique Pro Web** :
   - Vérifier en fail-closed `website_id` (24-hex), `PARTNER_ID` obligatoire via la source unique `partner-isolation.mjs` (`PARTNER_ID === site.partner_id`, ou `PARTNER_ID=multi` avec `ALLOWED_PARTNER_IDS`), et la propriété distante réelle via `GET /websites?partnerId=` (`domain ↔ partnerId` ET `type === "STATIC"` obligatoire) + `GET /objects/list/<websiteId>` (`partnerId` + `urlPublic ↔ domain`), poser un verrou local par `website_id` (avec contrôle `process.kill(pid, 0)`) et sauvegarder l'existant dans `.tmp/backups/`.
   - Téléverser via `POST /objects/signed-url` $\rightarrow$ `PUT S3` (sans `x-amz-acl`) $\rightarrow$ `POST /objects/upsert` dans l'**ordre atomique strict** :
     1. Images `assets/images/daily/<slug>/img_<hash>.<ext>` (`DOCUMENT:IMAGE`),
     2. Page HTML `<cleanHtmlKey>` (`PAGE:OTHER`),
     3. Fiche `/articles/<slug>.json` (`DOCUMENT:TEXT`, `application/json`),
     4. Index `/articles.json` en dernier (en cas d'erreur : restauration des copies `.before-*`, ou neutralisation en tombstone `noindex, nofollow` pour les clés nouvelles puisque `DELETE /objects` n'existe pas sur l'API publique Pro Web).
3. **Vérification HTTP Post-Publication Automatique & Rollback (`postPublishHttpCheck`)** :
   - Exécutée automatiquement immédiatement après la publication Web (**avant** l'étape SFMC en mode `--target all`) sur `https://${DOMAIN_NAME}/articles.json` (`HTTP 200`) et `https://${DOMAIN_NAME}/${CLEAN_HTML_KEY}` (`HTTP 200`, sans slash final). En cas d'échec post-publication, déclenche automatiquement le rollback (`articles.json` + copies `.before-*` ou tombstones `noindex, nofollow` sur S3 ; restauration backup ou passage en `draft` + purge CloudFront sur WordPress), n'envoie rien sur SFMC et renvoie **`HTTP 502`** dans le Studio.

---

## 6. Options de Découplage CLI (`--target`, `--local-only`, `--allow-empty-site`)

Par défaut, `push --go` publie de façon coordonnée sur le Web puis sur Salesforce après un pre-flight complet de toutes les cibles demandées :
- `--target all` (défaut) : publication coordonnée atomique (Article Web + `postPublishHttpCheck` $\rightarrow$ Email SFMC #195/#207 ; si SFMC échoue après la publication Web, le rollback Web `results.site.rollback()` est automatiquement exécuté).
- `--target web` (alias `site`) : publication exclusive sur le site (Statique Vibecodé ou WordPress), sans appel Salesforce.
- `--target sfmc` : génération et envoi exclusif vers Salesforce Marketing Cloud.
- `--local-only` : écrit uniquement les fichiers locaux sur disque sans aucun appel d'écriture réseau.
- `--allow-empty-site` (**garde-fou d'amorçage**) : réservé exclusivement à la toute première publication sur un bucket S3 vierge (`0` objet existant, où `GET /objects/list/<websiteId>` ne peut pas encore exposer `urlPublic`). Refusé en fail-closed dès que `existingObjects.length > 0` ; exige une double vérification manuelle du `website_id` dans `variables.md` avant l'amorçage initial.

---

## 7. Observabilité & Télémétrie Native

Chaque exécution `push --go` consigne `lastPushReport` dans `manifest.json` (hors empreinte `computePreviewSealHash`) et émet un événement `daily_push` (`partner_slug`, `list_id`, `target`, `site_type`, `slug`, `status`, `duration_ms`, `error_reason`) dans `~/.gemini/antigravity/state/telemetry/briques_metrics.jsonl`, lu par `python3 ~/Outils/harnais/os_status.py`.
