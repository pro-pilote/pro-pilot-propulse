# Guide d'Exécution — Pro Web Uploader (API Publique `x-api-key`)

## 1. Périmètre & Contrat Métier
- **Rôle** : Créer, prévisualiser localement et publier un **objet** (`PAGE` HTML ou `DOCUMENT` PDF/image) sur un site Pro Web (`STATIC`, `BLOG`, `PREMIUM` ou `PREMIUM_CONNECT`) via l'API publique **`https://api-pro-web.propulse-lab.com`**.
- **Authentification** : Header HTTP `x-api-key: $PRO_WEB_API_KEY` (chargé depuis `.env` via `set -a; source .env; set +a`).
- **Contexte obligatoire avant génération HTML** :
  - Lire `donnees-business/<sku>/fiche-produit.md` et `donnees-business/design-system.md`.
  - Lire `outils/pro-web-uploader/variables.md`, `specificites.md` et `erreurs-connues.md`.
  - **En-tête obligatoire sur toute Landing Page de conversion (`PAGE`)** : inclure `<script src="https://scripts.propulse-lab.com/headerTools.js" defer></script>` dans `<head>` afin de propager automatiquement les paramètres d'acquisition (`utm_*`, `leadcode`, `salescode`) vers le bon de commande.
- **Convention de clé (`key`)** :
  - Le chemin de l'objet dans le bucket S3 du site est défini par `key` (sans slash initial, ex. `pages/mon-dossier`, `leads/inscription`, `cadeau/guide.pdf`).
  - L'URL publique finale de l'objet est `https://<domainName>/<key>`.

---

## 2. Workflow Complet en 5 Étapes (Appels HTTP Directs)

### Étape 1 — Contrôle pré-vol & Détection de collision (`GET /objects/list/{websiteId}`)
Prendre le `websiteId` et le `partnerId` du domaine cible dans `outils/pro-web-uploader/variables.md`, puis lister les objets existants sur ce site :
```bash
set -a; source .env; set +a
curl -sS "https://api-pro-web.propulse-lab.com/objects/list/${WEBSITE_ID}?limit=500" \
  -H "x-api-key: ${PRO_WEB_API_KEY}" \
  -H "x-partner-id: ${PARTNER_ID}"
```
- **Si la `key` cible existe déjà** : avertir l'utilisateur qu'il s'agit d'une **mise à jour (écrasement)** et sauvegarder la version en ligne dans `backups/<key>` (`curl -sS "<urlPublic>" -o "backups/..."`) avant toute écriture.

### Étape 2 — Prévisualisation locale & Validation Humaine (Obligatoire)
1. Ouvrir le fichier HTML local dans le navigateur (`open page.html` sur macOS) ou lancer un serveur HTTP local (`python3 -m http.server 8080`).
2. **STOP** : Demander la confirmation explicite de l'utilisateur dans le chat (*« L'aperçu local sur `<domaine>/<key>` est-il validé pour publication en production ? »*) avant d'exécuter les étapes 3 et 4.

### Étape 3 — Obtenir une URL S3 présignée et téléverser le fichier (`signed-url` → `PUT S3`)
1. Demander une URL présignée (`POST /objects/signed-url`, valide `3600` secondes) :
   ```bash
   set -a; source .env; set +a
   curl -sS -X POST "https://api-pro-web.propulse-lab.com/objects/signed-url" \
     -H "x-api-key: ${PRO_WEB_API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{
       "websiteId": "<websiteId>",
       "partnerId": <partnerId>,
       "key": "pages/mon-slug",
       "contentType": "text/html"
     }'
   ```
   > La réponse JSON est de la forme `{"url": "https://s3.eu-west-1.amazonaws.com/...", "data": "https://s3.eu-west-1.amazonaws.com/..."}`.
2. Téléverser le fichier binaire ou HTML sur l'URL présignée (`PUT <url>`) :
   ```bash
   curl -sS -i -X PUT "<url_presignee_s3>" \
     -H "Content-Type: text/html" \
     --data-binary "@page.html"
   ```
   > **Piège S3 critique** : L'ACL `bucket-owner-full-control` est déjà signée dans la query-string de l'URL présignée. **Ne jamais ajouter le header `x-amz-acl` lors du `PUT`** (sinon S3 refuse avec `403 AccessDenied`). N'envoyer que le header `Content-Type` strictement identique à celui demandé à `signed-url`.

### Étape 4 — Enregistrer l'objet dans Pro Web & Invalider CloudFront (`POST /objects/upsert`)
```bash
set -a; source .env; set +a
curl -sS -X POST "https://api-pro-web.propulse-lab.com/objects/upsert" \
  -H "x-api-key: ${PRO_WEB_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "websiteId": "<websiteId>",
    "partnerId": <partnerId>,
    "key": "pages/mon-slug",
    "type": "PAGE",
    "subtype": "PAGE:OTHER",
    "originalFileName": "page.html",
    "hasIndexing": false
  }'
```
- **Valeurs autorisées pour `type` et `subtype`** :
  - `type: "PAGE"` → `subtype` : `"PAGE:OTHER"` *(défaut recommandé)*, `"PAGE:LEADGEN"`, `"PAGE:VSL"`, `"PAGE:OPTIN"`, `"PAGE:SALES"`, `"PAGE:THANKYOU"`.
  - `type: "DOCUMENT"` → `subtype` : `"DOCUMENT:PDF"`, `"DOCUMENT:IMAGE"`, `"DOCUMENT:OTHER"`.
- Cet appel crée ou met à jour l'enregistrement MongoDB (`s3objects`), déclenche l'invalidation CloudFront (`/<key>` et `/<key>_assets/*`) et retourne l'objet avec son `urlPublic`.

### Étape 5 — Vérification Post-Publication (Obligatoire)
Vérifier systématiquement que l'URL publique répond en `HTTP 200` avec le bon `content-type` :
```bash
curl -sI "https://<domainName>/pages/mon-slug" | head -n 10
```
- En cas d'erreur `500` transitoire sur `signed-url` ou `upsert`, patienter 2 secondes et réessayer au maximum 2 fois. En cas d'erreur `400` / `403` / `404`, vérifier `websiteId`, `partnerId` et `key` dans `outils/pro-web-uploader/variables.md` sans boucler.
