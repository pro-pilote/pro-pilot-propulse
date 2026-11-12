# Commande /pro-web — Creation, Retouche et Publication d'Objets Web

Cette commande standardise et automatise toutes les operations sur l'infrastructure Pro Web via son API publique officielle (`https://api-pro-web.propulse-lab.com`). Elle fonctionne de maniere universelle sans aucune donnee codee en dur.

---

## 1. Contexte & Resolution Dynamique

Avant toute operation, lis le contexte du depot local :

1. **Variables d'environnement** :
   - Chargees automatiquement via `set -a; source .env; set +a`.
   - `PRO_WEB_API_KEY` : Cle d'acces API Pro Web (transmise via le header `x-api-key`).

2. **Table des sites, domaines et identifiants partenaires** :
   - Fichier source : `outils/pro-web-uploader/variables.md`.
   - Resolution du triplet `(partnerId, websiteId, domainName)` selon le domaine cible.
   - Attention : `partnerId=9` correspond uniquement aux sites internes Propulse Lab. Les sites des autres partenaires utilisent leur propre `partnerId` specifie dans la table (Biosante=2, VivaSante=4, Pantheon=12, Optima=21, Tao=23, APS=24, Inse=25, LFP=26).

3. **Donnees business et design system** :
   - Charte visuelle : `donnees-business/design-system.md` (couleurs primaires, polices, espacements).
   - Informations produit : `donnees-business/<sku>/fiche-produit.md` (titre, promesse, prix, mentions).
   - Regle de completude : Si une mention ou information est manquante (`[A COMPLETER]`), poser la question a l'utilisateur avant toute generation.

4. **Pieges et regles specifiques du partenaire** :
   - Fichiers sources : `outils/pro-web-uploader/erreurs-connues.md` et `outils/pro-web-uploader/specificites.md`.
   - Verifier les pre-requis de tracking, conteneurs GTM et scripts CDN.

---

## 2. Regle Fondamentale de Stockage : Zero HTML / Zero Binaire dans Git

- **Pro Web S3 est l'unique espace de stockage des pages et binaires** :
  - Les pages HTML et les fichiers PDF/images ne sont jamais committes dans le depot Git.
  - Le depot Git est exclusivement reserve a la connaissance metier (`donnees-business/`), aux regles (`specificites.md`, `erreurs-connues.md`) et aux variables (`variables.md`).
- **Cycle de vie ephemere local (`.tmp/`)** :
  - Tout apercu HTML local ou retouche est genere dans le dossier local ephemere `.tmp/` (ex. `.tmp/preview-mon-slug.html`).
  - Le dossier `.tmp/` et les extensions `*.html`, `*.htm`, `*.pdf` sont strictement ignores par Git via `.gitignore`.
  - La publication s'effectue directement de `.tmp/` vers le bucket S3 via URL pre-signee.

---

## 3. Scripts CDN Pro Web Obligatoires

Toute page HTML (`PAGE`) publiee directement sur Pro Web doit contenir les scripts de l'infrastructure `cdn.info-contenu.io` :

1. **Dans `<head>`, juste avant `</head>`** :
   ```html
   <script src="https://cdn.info-contenu.io/assets/headerTools.js" type="text/javascript"></script>
   ```

2. **Propagation des parametres de tracking (liens de commande)** :
   ```html
   <script src="https://cdn.info-contenu.io/assets/preserveParamsV2.js" type="text/javascript"></script>
   ```
   Ce script assure la transmission de `utm_*`, `leadcode`, `salescode`, `bdc`, `url2`/`bdc2` vers les liens d'achat.

3. **Conteneur Google Tag Manager (GTM)** :
   - Snippet `<head>` et balise `<noscript>` en debut de `<body>` selon l'identifiant GTM indique dans `variables.md` ou extrait de la page source.

---

## 4. Nomenclature des Types et Sous-Types Pro Web (SSOT)

Lors des appels `POST /objects/upsert`, utiliser exclusivement les valeurs d'enumeration conformes au backend :

### Types (`type`)
- `PAGE` : Page web HTML.
- `DOCUMENT` : Document ou actif binaire (PDF, image, texte).

### Sous-types valides pour `PAGE` (`subtype`)
- `PAGE:LEADGEN` : Page d'acquisition (opt-in, formulaire, inscription webinaire ou newsletter, quizz).
- `PAGE:CONFIRMATION` : Page de remerciement et confirmation (fin de parcours d'inscription ou d'achat).
- `PAGE:VIDEO` : Page video (VDT / VSL, replay de webinaire).
- `PAGE:PAID` : Copie de vente ou page produit payante.
- `PAGE:OTHER` : Page diverse non categorisee (mentions legales, conditions generales).

### Sous-types valides pour `DOCUMENT` (`subtype`)
- `DOCUMENT:PDF` : Fichier PDF.
- `DOCUMENT:IMAGE` : Image web (PNG, JPEG, WebP, SVG).
- `DOCUMENT:TEXT` : Fichier texte, CSS, JavaScript, JSON.
- `DOCUMENT:OTHER` : Autre document binaire.

---

## 5. Catalogue des Actions

### Action A — Creer, retoucher et publier un objet (PAGE HTML ou DOCUMENT)

Cette action s'applique pour publier une nouvelle page creee de toutes pieces, pour retoucher le HTML d'une page existante ou pour televerser un document PDF.

1. **Preparation et conformite du contenu** :
   - Integrer les variables produit et les styles du design system.
   - Integrer `headerTools.js`, `preserveParamsV2.js` et GTM.
   - Regle de zero troncature : produire le document HTML complet de `<!DOCTYPE html>` a `</html>`.

2. **Apercu local ephemere dans `.tmp/`** :
   - Creer le dossier ephemere : `mkdir -p .tmp`
   - Enregistrer le fichier HTML localement : `.tmp/preview-${SLUG}.html`
   - Inviter l'utilisateur a verifier le rendu visuel dans son navigateur.
   - Obtenir sa validation explicite avant tout envoi API. Ne jamais committer ce fichier dans Git.

3. **Etape 1 sur 3 API : Obtention de l'URL signee S3** :
   ```bash
   set -a; source .env; set +a
   curl -sS -X POST "https://api-pro-web.propulse-lab.com/objects/signed-url" \
     -H "x-api-key: ${PRO_WEB_API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{
       "websiteId": "'"${WEBSITE_ID}"'",
       "key": "'"${KEY}"'",
       "contentType": "text/html"
     }'
   ```
   La reponse fournit l'URL pre-signee S3 dans le champ `data` (ou `url`).

4. **Etape 2 sur 3 API : Televersement binaire direct vers S3** :
   ```bash
   curl -sS -X PUT "${SIGNED_URL}" \
     -H "Content-Type: text/html" \
     --data-binary @".tmp/preview-${SLUG}.html"
   ```
   Remarque de securite S3 : ne pas ajouter de header `x-amz-acl`, l'autorisation est signee dans la query string.

5. **Etape 3 sur 3 API : Enregistrement de l'objet en base (`upsert`)** :
   ```bash
   set -a; source .env; set +a
   curl -sS -X POST "https://api-pro-web.propulse-lab.com/objects/upsert" \
     -H "x-api-key: ${PRO_WEB_API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{
       "websiteId": "'"${WEBSITE_ID}"'",
       "key": "'"${KEY}"'",
       "type": "PAGE",
       "subtype": "'"${SUBTYPE:-PAGE:PAID}"'",
       "originalFileName": "page.html",
       "hasIndexing": false
     }'
   ```

6. **Controle final de l'URL publique** :
   ```bash
   curl -sI "https://${DOMAIN_NAME}/${KEY}" | head -n 10
   ```
   La reponse doit afficher `HTTP/2 200` et `content-type: text/html`.

7. **Nettoyage ephemere** :
   - Le fichier `.tmp/preview-${SLUG}.html` peut etre supprime ou conserve dans `.tmp/` sans risque pour Git.

---

### Action B — Lister ou inspecter les objets d'un site

Pour retrouver un `objectId`, une cle ou une date de mise a jour :
```bash
set -a; source .env; set +a
curl -sS "https://api-pro-web.propulse-lab.com/objects/list/${WEBSITE_ID}?partnerId=${PARTNER_ID}&limit=200" \
  -H "x-api-key: ${PRO_WEB_API_KEY}"
```

---

### Action C — Supprimer un objet sur Pro Web

Operation destructive soumise a validation humaine formelle prealable :
```bash
set -a; source .env; set +a
curl -sS -X DELETE "https://api-pro-web.propulse-lab.com/objects/${OBJECT_ID}?partnerId=${PARTNER_ID}" \
  -H "x-api-key: ${PRO_WEB_API_KEY}"
```

---

## 6. Boucle de Retro-Alimentation Continue (`/feedback`)

A chaque fois qu'un utilisateur apporte une correction, une precision de design, une nouvelle regle editoriale ou une nouvelle fiche produit :

1. **Application immediate** sur la page en cours.
2. **Proposition d'apprentissage** : Proposer a l'utilisateur d'enregistrer la preference dans le depot :
   - Charte et styles : `donnees-business/design-system.md`
   - Produits : `donnees-business/<sku>/fiche-produit.md`
   - Regles editoriales : `outils/pro-web-uploader/specificites.md`
   - Erreurs et pieges : `outils/pro-web-uploader/erreurs-connues.md`
3. **Commit et push silencieux via le portail** : Si l'utilisateur confirme, Claude met a jour le fichier Markdown et appelle l'API `/api/feedback` de facon transparente sans toucher au terminal ni a Git (voir `/feedback`).

---

## 7. Garde-fous et Principes d'Execution

1. **Zero invention** : Toujours demander confirmation si une donnee business ou technique manque.
2. **Validation humaine obligatoire** : Aucun appel d'ecriture (`signed-url` + `PUT`, `upsert`, `DELETE`) ne doit etre execute sans accord explicite de l'utilisateur dans l'echange en cours.
3. **Securite des identifiants** : Ne jamais afficher la cle `PRO_WEB_API_KEY` dans les messages ou dans des fichiers versionnes.
4. **Verification systematique** : Toujours verifier la reponse HTTP reelle (`curl -sI`) avant d'affirmer qu'une page est publiee.
