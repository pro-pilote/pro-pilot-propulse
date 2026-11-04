# Guide Pas à Pas — Pro Web Uploader (Objets PAGE & DOCUMENT via API)

`pro-web-uploader` permet de **créer, prévisualiser en local et publier un objet** (`PAGE` HTML ou `DOCUMENT` PDF/image) sur Pro Web via l'API publique (`https://api-pro-web.propulse-lab.com` avec le header `x-api-key: $PRO_WEB_API_KEY`).

## 1. Préparation & Prévisualisation Locale d'un Objet HTML
1. **Données & Charte** : Lire `donnees-business/<sku>/fiche-produit.md`, `donnees-business/design-system.md` et les identifiants `ppl.website_id` / `ppl.partner_id` dans `outils/pro-web-uploader/variables.md`.
2. **Garde-fous HTML** : Fournir le fichier HTML complet (`<!DOCTYPE html>` à `</html>`, zéro troncature), conserver `<!-- PPL:FORM -->` et `<!-- PPL:GTM -->`.
3. **Périmètre des clés (`key`)** :
   - Sur un site non-STATIC (`WORDPRESS`, `BLOG`, `PREMIUM`), seuls les objets sous `pages/<slug>`, `leads/<slug>` et `cadeau/<slug>` sont autorisés.
   - Sur un site `STATIC`, tous les chemins d'objets sont autorisés (hors vidéos, max 20 Mo).
4. **Prévisualisation locale obligatoire** : Ouvrir le fichier HTML localement ou démarrer un serveur local (`npx serve` / `python3 -m http.server 8080`) et attendre la validation explicite de l'utilisateur avant de publier.

## 2. Publication de l'Objet via l'API Publique (`x-api-key`)

### Étape A — Obtenir l'URL S3 présignée (`POST /objects/signed-url`)
```bash
curl -sS -X POST "https://api-pro-web.propulse-lab.com/objects/signed-url" \
  -H "x-api-key: $PRO_WEB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "websiteId": "<WEBSITE_ID>",
    "partnerId": <PARTNER_ID>,
    "key": "pages/<slug>",
    "contentType": "text/html"
  }'
```
> La réponse JSON contient `{"url": "https://...", "data": "https://..."}`.

### Étape B — Téléverser le fichier sur S3 (`PUT <SIGNED_URL>`)
```bash
curl -sS -X PUT "<SIGNED_URL>" \
  -H "Content-Type: text/html" \
  --data-binary @page.html
```
> ⚠️ **Important** : N'envoyer **que** le header `Content-Type` (identique à celui demandé à l'étape A). Ne jamais ajouter `x-amz-acl` en header (déjà signé dans l'URL).

### Étape C — Enregistrer l'objet et purger CloudFront (`POST /objects/upsert`)
```bash
curl -sS -X POST "https://api-pro-web.propulse-lab.com/objects/upsert" \
  -H "x-api-key: $PRO_WEB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "websiteId": "<WEBSITE_ID>",
    "partnerId": <PARTNER_ID>,
    "key": "pages/<slug>",
    "type": "PAGE",
    "subtype": "PAGE:LEADGEN",
    "originalFileName": "page.html"
  }'
```
> Pour un PDF ou une image, utiliser `"type": "DOCUMENT"` et `"subtype": "DOCUMENT:PDF"` (ou `"DOCUMENT:IMAGE"`).

## 3. Lister les Objets Existants d'un Site (`GET /objects/list/{websiteId}`)
```bash
curl -sS -X GET "https://api-pro-web.propulse-lab.com/objects/list/<WEBSITE_ID>?partnerId=<PARTNER_ID>&limit=500" \
  -H "x-api-key: $PRO_WEB_API_KEY"
```
