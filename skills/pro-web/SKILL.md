---
name: pro-web
description: Creation, retouche et publication d'objets web sur Pro Web via l'API officielle et lecture live du depot partenaire sur GitHub.
---

# Skill `/pro-web` — Création, Retouche et Publication d'Objets Web

Cette skill standardise toutes les opérations sur l'infrastructure Pro Web via son API publique officielle (`https://api-pro-web.propulse-lab.com`). Elle lit en temps réel les données et paramètres du dépôt GitHub du partenaire via le portail Pro-Pilot afin d'éliminer toute copie locale obsolète.

---

## 1. Contexte & Lecture Live du Dépôt Partenaire (`GET /api/repo`)

Avant toute génération ou publication :

1. **Variables d'environnement (`.env`)** :
   - Charger `.env` : `[ -f .env ] && { set -a; source .env; set +a; }`.
   - `PRO_WEB_API_KEY` : clé d'accès à l'API publique Pro Web (header `x-api-key`). Si absente ou vide, se limiter à la rédaction et à l'aperçu local `.tmp/` sans appeler l'API Pro Web.
   - `PARTNER_ID` : identifiant numérique du partenaire. S'il est absent de `.env` (mode multi-partenaires ou dépôt mutualisé multi-organisations), le résoudre obligatoirement depuis la colonne `partnerId` du domaine cible dans `skills/pro-web/variables.md`.
   - `PRO_PILOT_WRITE_TOKEN` : jeton signé permettant de lire en direct le dépôt privé du partenaire (`/api/repo`) et d'enregistrer les retours (`/api/feedback`).

2. **Lecture en direct sur GitHub via `GET https://pro-pilot.propulse-lab.com/api/repo`** :
   - En mode mono-partenaire (y compris sur un dépôt mutualisé multi-organisations) :
     ```bash
     set -a; source .env; set +a
     curl -fsSL -H "Authorization: Bearer ${PRO_PILOT_WRITE_TOKEN}" \
       "https://pro-pilot.propulse-lab.com/api/repo?path=skills/pro-web/variables.md"
     ```
   - En mode multi-partenaires (compte d'équipe transverse), ajouter `&partner=<slug>` (résolu dynamiquement selon l'organisation cible, ex. `mon-partenaire`).
   - Fichiers à lire systématiquement avant de produire du HTML :
     - `skills/pro-web/variables.md` : table `(domainName, websiteId)`, `partnerId`, conteneur GTM et URL BDC.
     - `skills/pro-web/specificites.md` et `skills/pro-web/erreurs-connues.md` : règles éditoriales, tracking et pièges mesurés chez ce partenaire.
     - `donnees-business/design-system.md` : charte visuelle (couleurs, typographies, composants).
     - `donnees-business` (listing dossier) puis `donnees-business/<sku>/fiche-produit.md` : titre, promesse, tarifs, mentions légales. Si un champ requis porte `[À COMPLÉTER]`, poser la question à l'utilisateur avant toute génération.

---

## 2. Règle de Stockage & Encodage UTF-8

- **Zéro HTML / Zéro Binaire dans Git** : Pro Web S3 est l'unique stockage des pages et documents. Tout aperçu ou sauvegarde transite uniquement par `.tmp/` (ex. `.tmp/preview-${SLUG}.html` et `.tmp/backups/`).
- **Encodage UTF-8 strict (anti-mojibake)** : Toujours inclure `lang="fr"` sur `<html>` et `<meta charset="UTF-8">` en tout premier dans `<head>`, contrôler l'absence de mojibake (`Ã©`…) sur toute page reprise depuis Leadpages, enregistrer le fichier en UTF-8 sans BOM et passer `contentType: "text/html; charset=utf-8"` à `signed-url` puis `--data-binary` avec le même header `Content-Type: text/html; charset=utf-8` sur le `PUT` S3.

---

## 3. Scripts CDN Pro Web Obligatoires (`cdn.info-contenu.io`)

Toute page HTML (`PAGE`) publiée sur Pro Web doit inclure ou conserver intacts :

1. **Dans `<head>`, juste avant `</head>`** :
   ```html
   <script src="https://cdn.info-contenu.io/assets/headerTools.js" type="text/javascript"></script>
   ```
2. **Dans `<head>`, juste après `headerTools.js` — Propagation des paramètres vers les liens et BDC** :
   ```html
   <script async="" src="https://cdn.info-contenu.io/assets/preserveParamsV2.js" type="text/javascript"></script>
   ```
   Propage automatiquement `utm_*`, `leadcode`, `salescode`, `bdc`, `url2`/`bdc2`, `urlBdc`. Les liens génériques `https://secure.bdc.com` ne sont réécrits par ce script que si l'URL de visite contient `url2` et `bdc2` : préférer le lien direct du bon de commande (+ `salescode`) dès qu'il est connu.
3. **Conteneur Google Tag Manager (`GTM-XXXXXXX`)** :
   - Snippet `<script>` dans `<head>` et `<noscript>` juste après `<body>` selon l'identifiant GTM de `skills/pro-web/variables.md` (ou celui déjà présent sur la page modifiée).
4. **Scripts de formulaires existants à préserver intacts s'ils sont présents** :
   - `leadBox-v1.0.0.js`, `email-autocomplete.js`, `eventTriggerV1.js`, `redirect-v1.0.0.js`, `lead/assets/tel-input/js/intlTelInput.js`.

---

## 4. Nomenclature des Types et Sous-Types Pro Web (SSOT)

- `type: "PAGE"` $\rightarrow$ `subtype` : `PAGE:LEADGEN` (opt-in/lead), `PAGE:CONFIRMATION` (merci), `PAGE:VIDEO` (VSL/replay), `PAGE:PAID` (copie de vente), `PAGE:OTHER` (mentions légales, CGV, article).
- `type: "DOCUMENT"` $\rightarrow$ `subtype` : `DOCUMENT:PDF`, `DOCUMENT:IMAGE`, `DOCUMENT:TEXT`, `DOCUMENT:OTHER`.

---

## 5. Catalogue des Actions

### Action A — Créer, retoucher et publier un objet (`PAGE` ou `DOCUMENT`)

1. **Contrôle pré-vol & sauvegarde anti-écrasement (`GET /objects/list/{websiteId}`)** :
   ```bash
   set -a; source .env; set +a
   curl -sS "https://api-pro-web.propulse-lab.com/objects/list/${WEBSITE_ID}?partnerId=${PARTNER_ID}&limit=1000" \
     -H "x-api-key: ${PRO_WEB_API_KEY}"
   ```
   - La réponse peut être doublement encodée en JSON (`d = json.loads(body); d = json.loads(d) if isinstance(d, str) else d`).
   - Le listing étant plafonné (`limit` max `1000`, `500` par défaut, paramètre `skip` ignoré), si le résultat atteint `>= 1000` entrées, vérifier également l'existence de la clé via `curl -sI "https://${DOMAIN_NAME}/${KEY}"` (sur `STATIC` hors `/`, `200`/`301`/`302` = clé occupée, `404`/`500` sans slash final suggère absente en vérifiant aussi `<key>/index.html` si historique ; sur `BLOG`/`PREMIUM`, seul `404` = libre et `500` = erreur serveur → STOP).
   - Si la `key` existe déjà, avertir l'utilisateur qu'il s'agit d'une mise à jour (prévenir en cas de cache CloudFront actif sur la même `key`) et sauvegarder la version en ligne dans `.tmp/backups/` avant toute écriture.

2. **Aperçu local éphémère & Validation Humaine (STOP obligatoire)** :
   - Produire le HTML complet (`<!DOCTYPE html>` à `</html>`, zéro troncature) dans `.tmp/preview-${SLUG}.html`.
   - Faire valider le rendu par l'utilisateur et obtenir son accord explicite dans l'échange en rappelant `(domainName, websiteId, key)`.

3. **Étape 1/3 API — Obtention de l'URL signée S3 (`partnerId` numérique obligatoire)** :
   ```bash
   set -a; source .env; set +a
   curl -sS -X POST "https://api-pro-web.propulse-lab.com/objects/signed-url" \
     -H "x-api-key: ${PRO_WEB_API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{
       "websiteId": "'"${WEBSITE_ID}"'",
       "partnerId": '"${PARTNER_ID}"',
       "key": "'"${KEY}"'",
       "contentType": "text/html; charset=utf-8"
     }'
   ```
   La réponse peut être une chaîne JSON doublement encodée contenant `{"url": "<signedUrl S3>", "data": "<signedUrl S3>"}` (`d = json.loads(body); d = json.loads(d) if isinstance(d, str) else d`).

4. **Étape 2/3 API — Téléversement binaire direct vers S3 (sans `x-amz-acl`)** :
   ```bash
   curl -sS -X PUT "${SIGNED_URL}" \
     -H "Content-Type: text/html; charset=utf-8" \
     --data-binary @".tmp/preview-${SLUG}.html"
   ```
   Le header `Content-Type` doit correspondre exactement au `contentType` passé à `signed-url`. Ne jamais ajouter `x-amz-acl` (déjà signé dans la query-string S3, sinon `403 AccessDenied`).

5. **Étape 3/3 API — Enregistrement en base & invalidation (`upsert`)** :
   ```bash
   set -a; source .env; set +a
   curl -sS -X POST "https://api-pro-web.propulse-lab.com/objects/upsert" \
     -H "x-api-key: ${PRO_WEB_API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{
       "websiteId": "'"${WEBSITE_ID}"'",
       "partnerId": '"${PARTNER_ID}"',
       "key": "'"${KEY}"'",
       "type": "PAGE",
       "subtype": "'"${SUBTYPE:-PAGE:PAID}"'",
       "originalFileName": "page.html",
       "hasIndexing": false
     }'
   ```
   *(Pour un document ou média, adapter `"type": "DOCUMENT"`, `"subtype"` et `"originalFileName"`)*
   - Après un `upsert` manuel, `leadpageEditUrl` passe à `null` : ne jamais relancer `reload-page` sur une page retouchée manuellement.
   - Sur les sites `STATIC`, utiliser une `key` sans slash final ni `/index.html` (ex. `pages/mon-slug` ou `articles/mon-slug`), car `/<slug>/` renvoie `500`.

6. **Contrôle final HTTP & contenu servi post-publication** :
   ```bash
   curl -sI "https://${DOMAIN_NAME}/${KEY}" | head -n 10
   curl -sS "https://${DOMAIN_NAME}/${KEY}" | grep -E "charset|<title"
   ```
   Vérifier `HTTP/2 200` sans slash final **et** contrôler que le contenu servi correspond bien à la nouvelle version (pas uniquement un `200` en cache). En cas de cache CloudFront bloqué (`x-cache: Hit from cloudfront` sur l'ancienne version, car `?v=…` ne contourne pas le cache), proposer une nouvelle `key` vierge ou demander une invalidation CloudFront à Propulse Lab.

### Action B — Lister ou inspecter les objets d'un site
```bash
set -a; source .env; set +a
curl -sS "https://api-pro-web.propulse-lab.com/objects/list/${WEBSITE_ID}?partnerId=${PARTNER_ID}&limit=1000" \
  -H "x-api-key: ${PRO_WEB_API_KEY}"
```
*(Décoder de manière sûre : `d = json.loads(body); d = json.loads(d) if isinstance(d, str) else d`).*

### Action C — Publier des images ou assets liés (`DOCUMENT:IMAGE`)
Utiliser la convention de clé `<page_key>_assets/img/<fichier>` (ex. `pages/<slug>_assets/img/<fichier>` ou `webinaire/<slug>_assets/img/<fichier>` pour rester aligné sur la purge CloudFront `/<key>_assets/*`) avec `"type": "DOCUMENT"`, `"subtype": "DOCUMENT:IMAGE"` et le MIME exact (`image/png`, `image/jpeg`, `image/webp`) sur `signed-url` + `PUT S3` + `upsert`, puis référencer l'URL absolue `https://${DOMAIN_NAME}/${KEY}` dans le HTML.

---

## 6. Garde-fous & Rétro-Alimentation (`/fin`)

1. **Suppression non autorisée en v1** : aucune route `DELETE` n'est ouverte sur l'API publique ; toute suppression définitive s'effectue manuellement sur l'interface web Pro Web.
2. **Sécurité des secrets** : ne jamais afficher `PRO_WEB_API_KEY` ni `PRO_PILOT_WRITE_TOKEN` en clair.
3. **Apprentissage continu** : dès que l'utilisateur formule une correction, une préférence graphique ou une nouvelle règle (ou en clôture via `/fin`), l'appliquer immédiatement puis proposer de l'enregistrer via la skill `/fin` (`POST https://pro-pilot.propulse-lab.com/api/feedback` $\rightarrow$ `donnees-business/_inbox/`).
