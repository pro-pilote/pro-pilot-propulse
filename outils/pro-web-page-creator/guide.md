# Guide d'Exécution — Pro Web Page Creator (API Publique `x-api-key`)

## 1. Périmètre & Contrat Métier
- **Rôle** : **Scraper une URL externe** (`originalUrl`, ex. une page Leadpages `https://<account>.lpages.co/<slug>/`) afin de l'importer automatiquement sur un site Pro Web en tant qu'objet `type: "PAGE"` (`key: "pages/<slug>"`).
- **Ce que fait le backend Pro Web lors de l'import (`objects/pageCreator.ts`)** :
  1. Télécharge le HTML de `originalUrl` (`minifyPage`), passe `<html lang="en">` en `<html lang="fr">`, supprime les metas/scripts analytics Leadpages et exécute `cleanScripts` (qui injecte `headerTools.js`).
  2. Injecte le `customDom` du site (`website.pagesCustomDom` : `head`, `body`, `footer`) s'il est configuré.
  3. **Images (`getImages`)** : supprime le dossier S3 `<key>_assets/img`, télécharge chaque balise `<img src="...">` (hors SVG data-URI), génère les variantes redimensionnées (`320, 460, 720, 910, 1200, 2500 px`), les pousse sur S3 dans `<key>_assets/img/` et réécrit les attributs `src` et `srcset`. *(Les `background-image: url(...)` CSS ne sont pas rapatriées).*
  4. Téléverse le HTML final sur S3 (`uploadHtmlPage`), met à jour MongoDB (`upsertObject`) et purge CloudFront (`/<key>` et `/<key>_assets/*`).
- **Nature asynchrone (`InvocationType: Event`)** :
  - `POST /objects/upload-page` et `POST /objects/{objectId}/reload-page` déclenchent la Lambda `page-creator` de manière **asynchrone**.
  - La réponse HTTP `200 {"status": true}` signifie uniquement que **la tâche est acceptée en file d'attente**, et **non** que la page est déjà publiée. Il est donc obligatoire d'exécuter l'Étape 1 (contrôle de `originalUrl`) avant l'appel et l'Étape 4 (polling & vérification) après l'appel.

---

## 2. Workflow Complet en 4 Étapes

### Étape 1 — Contrôle pré-vol de `originalUrl` et de collision (Obligatoire)
1. Vérifier que `originalUrl` est strictement ASCII (`https://`), ne pointe pas vers un PDF et répond en **HTTP 200 direct** (sans redirection `301`/`302`) :
   ```bash
   curl -sI "<originalUrl>" | head -n 10
   ```
2. Vérifier dans `GET /objects/list/{websiteId}` si la `key` cible existe déjà :
   ```bash
   set -a; source .env; set +a
   curl -sS "https://api-pro-web.propulse-lab.com/objects/list/${WEBSITE_ID}?limit=500" \
     -H "x-api-key: ${PRO_WEB_API_KEY}" \
     -H "x-partner-id: ${PARTNER_ID}"
   ```
3. **STOP** : Demander la confirmation explicite de l'utilisateur avant de lancer l'import ou le rechargement.

### Étape 2 — Importer une URL externe (`POST /objects/upload-page`)
```bash
set -a; source .env; set +a
curl -sS -X POST "https://api-pro-web.propulse-lab.com/objects/upload-page" \
  -H "x-api-key: ${PRO_WEB_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "websiteId": "<websiteId>",
    "partnerId": <partnerId>,
    "key": "pages/mon-slug",
    "type": "PAGE",
    "subtype": "PAGE:OTHER",
    "originalUrl": "https://mon-compte.lpages.co/ma-page/",
    "hasIndexing": false
  }'
```

### Étape 3 — Recharger une page existante depuis son `originalUrl` (`POST /objects/{objectId}/reload-page`)
Si l'objet `PAGE` existe déjà (identifié par son `_id` MongoDB `objectId` dans `GET /objects/list/{websiteId}`) et que son `originalUrl` a été modifiée à la source :
```bash
set -a; source .env; set +a
curl -sS -X POST "https://api-pro-web.propulse-lab.com/objects/${OBJECT_ID}/reload-page" \
  -H "x-api-key: ${PRO_WEB_API_KEY}" \
  -H "x-partner-id: ${PARTNER_ID}"
```
> **Attention** : `reload-page` ré-exécute le pipeline complet `page-creator` (y compris la purge et le re-téléchargement de `<key>_assets/img`) à partir de `originalUrl`. Ne jamais appeler `reload-page` sur une page qui a été éditée manuellement via `pro-web-uploader` (ses modifications manuelles seraient écrasées par `originalUrl`), ni sur un objet servant un PDF.

### Étape 4 — Polling de fin de traitement & Vérification URL publique (Obligatoire)
Puisque `page-creator` s'exécute de façon asynchrone (5 à 30 secondes selon le nombre d'images `<img>`), attendre quelques secondes puis vérifier dans `GET /objects/list/{websiteId}` que l'objet apparaît avec un `updatedAt` récent, et contrôler l'URL publique :
```bash
curl -sI "https://<domainName>/pages/mon-slug" | head -n 10
```
- Ne confirmer la publication à l'utilisateur qu'après avoir observé `HTTP/2 200` et `content-type: text/html` sur l'URL publique.
