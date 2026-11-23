---
name: pro-web
version: "2.1.3"
description: Creation, retouche et publication d'objets web sur Pro Web via l'API officielle et lecture live du depot partenaire sur GitHub.
---

# Skill `/pro-web` — Création, Retouche et Publication d'Objets Web

Cette skill standardise toutes les opérations sur l'infrastructure Pro Web (`${PRO_WEB_PUBLIC_API_URL:-https://api-pro-web.propulse-lab.com}`). Elle lit en temps réel les données et paramètres du dépôt GitHub du partenaire via le portail Pro-Pilot afin d'éliminer toute copie locale obsolète.

---

## 0. Contrôle de Version Ultra-Rapide (< 100 ms) & Nouveaux Skills

À chaque appel de `/pro-web`, exécute ce snippet Python compact borné à 2 secondes (dégradation gracieuse hors-ligne sans bloquer l'action) :
```bash
python3 - <<'PY'
import json, os, urllib.request

MANIFEST_URL = "https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/manifest.json"
SKILL_NAME = "pro-web"
LOCAL_PATH = f".claude/commands/{SKILL_NAME}.md"
CURRENT_VERSION = "2.1.3"

try:
    req = urllib.request.Request(MANIFEST_URL, headers={"User-Agent": "Pro-Pilot-CLI/2.1"})
    with urllib.request.urlopen(req, timeout=2) as resp:
        manifest = json.loads(resp.read().decode("utf-8"))

    # 1. Vérification auto-MAJ du skill courant
    remote_skill = manifest.get("skills", {}).get(SKILL_NAME, {})
    remote_ver = remote_skill.get("version", CURRENT_VERSION)
    if remote_ver != CURRENT_VERSION and remote_skill.get("path"):
        skill_url = f"https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/{remote_skill['path']}"
        with urllib.request.urlopen(urllib.request.Request(skill_url, headers={"User-Agent": "Pro-Pilot-CLI/2.1"}), timeout=2) as s_resp:
            new_code = s_resp.read().decode("utf-8")
        if new_code.strip():
            tmp_path = f"{LOCAL_PATH}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(new_code)
            os.replace(tmp_path, LOCAL_PATH)
            print(f"[PRO_PILOT_UPDATE] Skill /{SKILL_NAME} mis à jour automatiquement vers v{remote_ver}.")

    # 2. Détection de nouveaux skills disponibles (stables ou scoped éligibles au partenaire)
    local_pid = None
    if os.path.exists(".env"):
        try:
            with open(".env") as f:
                for line in f:
                    if line.startswith("PARTNER_ID="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        local_pid = int(val) if val.isdigit() else None
        except Exception:
            pass

    for name, data in manifest.get("skills", {}).items():
        is_scoped_ok = (data.get("status") == "partner_scoped" and local_pid in data.get("eligible_partner_ids", []))
        if data.get("status") == "stable" or is_scoped_ok:
            target_cmd = f".claude/commands/{name}.md"
            if not os.path.exists(target_cmd):
                print(f"[PRO_PILOT_NEW_SKILL] Nouveau skill disponible : /{name} — {data.get('summary', '')}")
except Exception:
    pass
PY
```
- Si une mise à jour est signalée, elle est appliquée immédiatement de façon atomique.
- Si un nouveau skill disponible est détecté, signale-le sobrement à l'utilisateur et propose-lui de le télécharger.

---

## 1. Contexte & Lecture Live du Dépôt Partenaire (`GET /api/repo`)

Avant toute génération ou publication :

1. **Variables d'environnement (`.env`) & Résolution Non-Régressive des Clés** :
   - Charger la configuration locale (`.env`). Si `.env` est absent du dossier courant, vérifier la présence d'un sous-dossier `pro-pilot-*/.env` (dossier parent ouvert par erreur) et indiquer à l'utilisateur d'ouvrir ce dossier dans son IA.
   - `PRO_WEB_PUBLIC_API_URL` : URL de l'API Pro Web (`https://api-pro-web.propulse-lab.com` par défaut, ou `https://pro-pilot.propulse-lab.com/api/pro-web` si le Broker est activé dans `.env`).
   - **Résolution ordonnée de la clé Pro Web (`EFFECTIVE_PRO_WEB_KEY`)** :
     1. `PRO_WEB_API_KEY` (défini dans `.env` pour tout partenaire mono-organisation ou mutualisé `others`, ou en mode Broker) ;
     2. sinon, en mode multi-partenaires, la variable d'environnement du poste `PRO_WEB_API_KEY_${PARTNER_ID}` (avec repli sur `PRO_WEB_API_KEY_9` si `PARTNER_ID` fait partie du périmètre mutualisé `6, 8, 9, 13, 16, 18, 19, 22`).
     - **Ne jamais demander à l'utilisateur de fournir ou coller une clé API à la main** : si aucune clé Pro Web n'est disponible après ces 2 niveaux (ex. organisation sans clé dédiée encore ouverte comme Innovia/Nutriorigines), conserver 100 % de la lecture GitHub (`/api/repo`), de la rédaction HTML et de l'aperçu local `.tmp/` sans prétendre que le `.env` est invalide. Uniquement si `.env` est introuvable, si `PRO_PILOT_WRITE_TOKEN` est vide, ou si `/api/repo` renvoie **`HTTP 401`**, inviter l'utilisateur à se reconnecter une fois sur `https://pro-pilot.propulse-lab.com/` pour actualiser son espace.
   - `PARTNER_ID` : identifiant numérique du partenaire. S'il est absent de `.env` (mode multi-partenaires ou dépôt mutualisé multi-organisations), le résoudre obligatoirement depuis la colonne `partnerId` du domaine cible dans `skills/pro-web/variables.md`.
   - `PARTNER_NAME` : nom officiel de l'organisation (ex. `Éditions Biosanté`). Toujours utiliser ce nom réel dans les échanges avec l'utilisateur au lieu du terme générique « organisation » (ne jamais employer le mot « marque »).
   - `PRO_PILOT_WRITE_TOKEN` : jeton signé permettant de lire en direct le dépôt privé du partenaire (`/api/repo`) et d'enregistrer les retours (`/api/feedback`).

2. **Lecture en direct sur GitHub via `GET https://pro-pilot.propulse-lab.com/api/repo`** :
   - En mode mono-partenaire (y compris sur un dépôt mutualisé multi-organisations) :
     ```bash
     curl -fsSL -m 15 -H "Authorization: Bearer ${PRO_PILOT_WRITE_TOKEN}" \
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
3. **Conteneur Google Tag Manager (`GTM-XXXXXXX`) — Préremplissage automatique SSOT** :
   - Snippet `<script>` dans `<head>` et `<noscript>` juste après `<body>` selon l'identifiant GTM de `skills/pro-web/variables.md` (ou celui déjà présent sur la page modifiée).
   - **GTM est prérempli** : l'identifiant GTM est documenté dans `variables.md` pour chaque site ou au niveau du partenaire. **Ne jamais demander l'identifiant GTM à l'utilisateur** : l'IA l'injecte directement et silencieusement dans le code généré.
4. **Formulaires d'opt-in & Pro Acquisitions (`leadBox-v1.0.0.js`)** :
   - **Création du `leadcode`** : Le partenaire crée et gère lui-même ses leadcodes de liste directement sur la plateforme **Pro Acquisitions** (`https://pro-acquisitions.propulse-lab.com`). **Ne jamais renvoyer l'utilisateur vers Salesforce ni vers une équipe CRM externe.**
   - **Endpoint d'inscription LeadBox officiel** : `POST https://lead.<domaine-partenaire>/api/lead/signup` (documenté dans `skills/pro-web/variables.md`).
   - **Hiérarchie d'attribution du Leadcode (Override dynamique SSOT)** :
     1. **Source prioritaire** : Le paramètre d'URL `?leadcode=...` provenant des campagnes marketing (Ads, newsletters, affiliation).
     2. **Override automatique** : Le script du formulaire lit `leadcode` dans `location.search` et **écrase systématiquement** toute valeur par défaut lors de la soumission.
     3. **Valeur en dur = filet de sécurité (fallback)** : La valeur inscrite en dur dans le formulaire (`<input type="hidden" name="leadcode" value="...">`) n'est qu'un repli pour les visites directes sans paramètre d'URL.
     4. **Zéro blocage de mise en ligne** : **Ne jamais bloquer la publication d'un site pour attendre un leadcode**. Utiliser le leadcode de repli par défaut de l'organisation (documenté dans `variables.md`) et déployer sans attendre.
   - Scripts de formulaires existants à préserver intacts s'ils sont présents : `leadBox-v1.0.0.js`, `email-autocomplete.js`, `eventTriggerV1.js`, `redirect-v1.0.0.js`, `lead/assets/tel-input/js/intlTelInput.js`.

---

## 4. Nomenclature des Types et Sous-Types Pro Web (SSOT)

- `type: "PAGE"` $\rightarrow$ `subtype` : `PAGE:LEADGEN` (opt-in/lead), `PAGE:CONFIRMATION` (merci), `PAGE:VIDEO` (VSL/replay), `PAGE:PAID` (copie de vente), `PAGE:OTHER` (mentions légales, CGV, article).
- `type: "DOCUMENT"` $\rightarrow$ `subtype` : `DOCUMENT:PDF`, `DOCUMENT:IMAGE`, `DOCUMENT:TEXT`, `DOCUMENT:OTHER`.

---

## 5. Catalogue des Actions

### Action A — Créer, retoucher et publier un objet (`PAGE` ou `DOCUMENT`)

1. **Résolution de `EFFECTIVE_PRO_WEB_KEY` & Contrôle pré-vol (`GET /objects/list/{websiteId}`)** :
   ```bash
   EFFECTIVE_PRO_WEB_KEY="${PRO_WEB_API_KEY:-}"
   if [ -z "$EFFECTIVE_PRO_WEB_KEY" ] && [ -n "${PARTNER_ID:-}" ]; then
     EFFECTIVE_PRO_WEB_KEY="$(printenv "PRO_WEB_API_KEY_${PARTNER_ID}" 2>/dev/null || true)"
     case "$PARTNER_ID" in 6|8|9|13|16|18|19|22) [ -n "$EFFECTIVE_PRO_WEB_KEY" ] || EFFECTIVE_PRO_WEB_KEY="${PRO_WEB_API_KEY_9:-}" ;; esac
   fi
   curl -sS "${PRO_WEB_PUBLIC_API_URL:-https://api-pro-web.propulse-lab.com}/objects/list/${WEBSITE_ID}?partnerId=${PARTNER_ID}&limit=1000" \
     -H "x-api-key: ${EFFECTIVE_PRO_WEB_KEY}"
   ```
   - La réponse peut être doublement encodée en JSON (`d = json.loads(body); d = json.loads(d) if isinstance(d, str) else d`).
   - Le listing étant plafonné (`limit` max `1000`, `500` par défaut, paramètre `skip` ignoré), si le résultat atteint `>= 1000` entrées, vérifier également l'existence de la clé via `curl -sI "https://${DOMAIN_NAME}/${KEY}"` (sur `STATIC` hors `/`, `200`/`301`/`302` = clé occupée, `404`/`500` sans slash final suggère absente en vérifiant aussi `<key>/index.html` si historique ; sur `BLOG`/`PREMIUM`, seul `404` = libre et `500` = erreur serveur → STOP).
   - Si la `key` existe déjà, avertir l'utilisateur qu'il s'agit d'une mise à jour (prévenir en cas de cache CloudFront actif sur la même `key`) et sauvegarder la version en ligne dans `.tmp/backups/` avant toute écriture.

2. **Aperçu local éphémère & Validation Humaine (STOP obligatoire)** :
   - Produire le HTML complet (`<!DOCTYPE html>` à `</html>`, zéro troncature) dans `.tmp/preview-${SLUG}.html`.
   - Faire valider le rendu par l'utilisateur et obtenir son accord explicite dans l'échange en rappelant `(domainName, websiteId, key)`.

3. **Étape 1/3 API — Obtention de l'URL signée S3 (`partnerId` numérique obligatoire)** :
   ```bash
   curl -sS -X POST "${PRO_WEB_PUBLIC_API_URL:-https://api-pro-web.propulse-lab.com}/objects/signed-url" \
     -H "x-api-key: ${EFFECTIVE_PRO_WEB_KEY}" \
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
   curl -sS -X POST "${PRO_WEB_PUBLIC_API_URL:-https://api-pro-web.propulse-lab.com}/objects/upsert" \
     -H "x-api-key: ${EFFECTIVE_PRO_WEB_KEY}" \
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
curl -sS "${PRO_WEB_PUBLIC_API_URL:-https://api-pro-web.propulse-lab.com}/objects/list/${WEBSITE_ID}?partnerId=${PARTNER_ID}&limit=1000" \
  -H "x-api-key: ${EFFECTIVE_PRO_WEB_KEY}"
```
*(Décoder de manière sûre : `d = json.loads(body); d = json.loads(d) if isinstance(d, str) else d`).*

### Action C — Publier des images ou assets liés (`DOCUMENT:IMAGE`)
Utiliser la convention de clé `<page_key>_assets/img/<fichier>` (ex. `pages/<slug>_assets/img/<fichier>` ou `webinaire/<slug>_assets/img/<fichier>` pour rester aligné sur la purge CloudFront `/<key>_assets/*`) avec `"type": "DOCUMENT"`, `"subtype": "DOCUMENT:IMAGE"` et le MIME exact (`image/png`, `image/jpeg`, `image/webp`) sur `signed-url` + `PUT S3` + `upsert`, puis référencer l'URL absolue `https://${DOMAIN_NAME}/${KEY}` dans le HTML.

### Action D — Déployer un site statique multi-pages (Mode Batch)
Quand un projet comporte plusieurs pages HTML liées (ex. `index.html`, `carte.html`, `super-retraite.html`, `mentions-legales.html`) :
1. **Validation globale en aperçu local** : générer l'ensemble des pages dans `.tmp/<projet>/site/` et faire valider la navigation locale à l'utilisateur.
2. **Garde-fou Leadcode & Déploiement Immédiat (Zéro Blocage)** :
   - Historiquement et par design, le `leadcode` est véhiculé dynamiquement dans les paramètres d'URL (`?leadcode=...`) des campagnes marketing et **écrase automatiquement** (`override`) la valeur du formulaire.
   - La valeur inscrite en dur dans le formulaire (`<input type="hidden" name="leadcode">`) n'est qu'un **fallback de secours** pour les visites directes sans paramètre d'URL.
   - **En aucun cas l'IA ne doit bloquer ou différer le déploiement** : inscrire le leadcode de repli du partenaire (ex. `GP18EXTPTFSIWGEN1GENALL` ou le code global de `variables.md`) et déployer immédiatement. Le trafic des campagnes sera automatiquement attribué via l'URL.
3. **Boucle séquentielle de publication** : pour chaque fichier du lot, exécuter la séquence :
   - `POST /objects/signed-url` avec `key: <nom-du-fichier>` (ex. `index.html`, `carte.html`, `super-retraite.html`, `mentions-legales.html`).
   - `PUT ${SIGNED_URL}` avec le contenu HTML binaire UTF-8 (`--data-binary @"path/to/file.html"`).
   - `POST /objects/upsert` avec `"type": "PAGE"`, `"subtype": "PAGE:OTHER"` (ou `PAGE:LEADGEN`), `"originalFileName": "<nom-du-fichier>"`.
4. **Vérification HTTP de chaque URL** :
   ```bash
   for page in index.html carte.html super-retraite.html mentions-legales.html; do
     curl -sI -m 10 "https://${DOMAIN_NAME}/${page}" | head -n 1
   done
   ```

### Action E — Pattern Blog Vibecodé (Consommation de `articles.json` & `/articles/<slug>.json`)
Quand l'utilisateur souhaite créer ou vibecoder un blog, un flux d'actualités ou une section dépêches/daily sur un site Pro Web :
1. **Source de Vérité des Articles (`Atomic OS`)** :
   - Les articles sont automatiquement publiés par la brique `/pro-daily` sous forme d'objets statiques déposés sur le bucket S3 du site :
     - **Index global** : `https://${DOMAIN_NAME}/articles.json` (liste ordonnée, extraits, dates, auteurs, tags, `html_url` sans slash final).
     - **Fiche unitaire** : `https://${DOMAIN_NAME}/articles/<slug>.json` (corps HTML assaini `content_html`, CTA, mentions).
     - **Page HTML statique** : `https://${DOMAIN_NAME}/<cleanHtmlKey>` (clé propre **sans slash final ni `/index.html`**, ex. `/<slug>` ou `/articles/<slug>` selon `articles_dir`, générée automatiquement pour le SEO/OpenGraph).
2. **Contrat d'intégration Frontend sécurisé (DOM API sans XSS + Tokens DTCG `@layer theme`)** :
   - Déclarer les jetons du blog dans `@layer theme` à partir de `donnees-business/design-system.md` du partenaire (contraste WCAG AA $\ge 4.5:1$, zéro couleur en dur hors `@layer theme`) :
     ```css
     @layer theme {
       :root {
         --blog-surface: var(--color-surface, #ffffff);
         --blog-border: var(--color-border, #e5e7eb);
         --blog-text: var(--color-text, #111827);
         --blog-muted: var(--color-text-muted, #4b5563);
         --blog-primary: var(--color-primary, #111827);
       }
     }
     ```
   - Afficher la grille d'articles via construction DOM pure (`createElement` + `textContent` + validation d'URL `safeUrl` — **ne jamais interpoler `innerHTML`**) :
     ```javascript
     const safeUrl = (u) => (typeof u === 'string' && (/^\/[a-zA-Z0-9]/.test(u) || u.startsWith('https://'))) ? u : '#';
     fetch('/articles.json')
       .then((r) => { if (!r.ok) throw new Error(String(r.status)); return r.json(); })
       .then((data) => {
         const grid = document.getElementById('articles-grid');
         if (!grid || !Array.isArray(data.articles)) return;
         grid.replaceChildren(...data.articles.map((art) => {
           const card = document.createElement('article');
           card.style.cssText = 'background:var(--blog-surface);border:1px solid var(--blog-border);color:var(--blog-text);border-radius:0.75rem;padding:1.5rem;';
           if (art.featured_image && safeUrl(art.featured_image) !== '#') {
             const img = document.createElement('img');
             img.src = safeUrl(art.featured_image);
             img.alt = String(art.title || '');
             img.loading = 'lazy';
             card.appendChild(img);
           }
           const meta = document.createElement('div');
           meta.style.color = 'var(--blog-muted)';
           meta.textContent = `${art.date_formatted || art.date || ''} • ${Number(art.reading_time_minutes) || 1} min`;
           const h3 = document.createElement('h3');
           const link = document.createElement('a');
           link.href = safeUrl(art.html_url);
           link.style.color = 'var(--blog-primary)';
           link.textContent = String(art.title || '');
           h3.appendChild(link);
           const p = document.createElement('p');
           p.style.color = 'var(--blog-muted)';
           p.textContent = String(art.excerpt || '');
           card.append(meta, h3, p);
           return card;
         }));
       })
       .catch((err) => console.error('Erreur chargement articles.json:', err));
     ```
3. **Zéro CMS requis** : ne jamais proposer de déployer WordPress ou une base de données MySQL pour un simple blog sur un site vitrine Pro Web. Utiliser exclusivement ce standard `articles.json` alimenté par `/pro-daily`.

---

## 6. Garde-fous & Rétro-Alimentation (`/learn`)

1. **Suppression non autorisée en v1** : aucune route `DELETE` n'est ouverte sur l'API publique ; toute suppression définitive s'effectue manuellement sur l'interface web Pro Web.
2. **Sécurité des secrets** : ne jamais afficher `PRO_WEB_API_KEY` ni `PRO_PILOT_WRITE_TOKEN` en clair.
3. **Apprentissage continu** : dès que l'utilisateur formule une correction, une préférence graphique ou une nouvelle règle (ou en clôture via `/learn`), l'appliquer immédiatement puis proposer de l'enregistrer via la skill `/learn` (alias `/fin`) (`POST https://pro-pilot.propulse-lab.com/api/feedback` $\rightarrow$ `donnees-business/_inbox/`).
