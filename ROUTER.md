# Routeur Atomique Pro-Pilot (`ROUTER.md`)

Ce fichier est le point d'entrée de l'assistant IA pour l'orientation et l'exécution des demandes Pro Web.
Les pages de Pro-Pilot sont articulées de manière **atomique** : ne charge jamais l'ensemble des fichiers d'un coup, descends uniquement dans la ou les branches nécessaires au besoin exprimé.

---

## Étape 1 — Prise en Main & Profil Utilisateur

1. Consulte [`getting-started/README.md`](./getting-started/README.md) pour les instructions de mise en route et le questionnaire initial.
2. Consulte [`regles/glossaire.md`](./regles/glossaire.md) pour la terminologie métier (Objet Pro Web `PAGE`/`DOCUMENT`, LP, STATIC, GTM, BU, Design System).

---

## Étape 2 — Arbre de Routage Pro-Pilot : API Pro Web, Marketing Cloud & WordPress

Identifie l'intention et consulte uniquement les fichiers correspondants :

| Besoin exprimé | 1. Données Business | 2. Spécifications & Guides | 3. Règles & Appels API |
|---|---|---|---|
| **Créer, prévisualiser ou publier un objet sur Pro Web** (`PAGE` HTML/LP ou `DOCUMENT` PDF/image) | `donnees-business/<sku>/fiche-produit.md`<br>`donnees-business/design-system.md` | [`outils/pro-web-uploader/guide.md`](./outils/pro-web-uploader/guide.md)<br>`outils/pro-web-uploader/specificites.md`<br>`outils/pro-web-uploader/erreurs-connues.md`<br>`outils/pro-web-uploader/variables.md` | [`regles/clarification.md`](./regles/clarification.md)<br>[`regles/garde-fous.md`](./regles/garde-fous.md)<br>Faire valider l'aperçu local HTML<br>Publier via `POST /objects/signed-url` → `PUT S3` → `POST /objects/upsert` |
| **Scraper une URL externe (ex. Leadpages) pour l'importer sur Pro Web** (`upload-page` / `reload-page`) | — | [`outils/pro-web-page-creator/guide.md`](./outils/pro-web-page-creator/guide.md)<br>`outils/pro-web-page-creator/specificites.md`<br>`outils/pro-web-page-creator/erreurs-connues.md`<br>`outils/pro-web-page-creator/variables.md` | [`regles/garde-fous.md`](./regles/garde-fous.md)<br>Vérifier que l'`originalUrl` est ASCII (HTTP 200 sans 302)<br>Appeler `POST /objects/upload-page` ou `POST /objects/{objectId}/reload-page` |
| **Préparer, retoucher ou publier une newsletter quotidienne (Daily)** (① Email Marketing Cloud + ② Article sur le blog WordPress ou site statique) | `donnees-business/design-system.md` | [`outils/daily-publisher/guide.md`](./outils/daily-publisher/guide.md)<br>`outils/daily-publisher/specificites.md`<br>`outils/daily-publisher/erreurs-connues.md`<br>`outils/daily-publisher/variables.md` | [`regles/clarification.md`](./regles/clarification.md)<br>[`regles/garde-fous.md`](./regles/garde-fous.md)<br>Faire valider le Studio 2 étapes scellé (`SHA-256`)<br>Publier via API REST Marketing Cloud (`195` + `207`) et WP REST API / Pro Web API |

---

## Étape 3 — Interaction ou Action

1. **Si une information essentielle manque** (ex. produit concerné, `websiteId`, `key` de l'objet ou `originalUrl`) : applique [`regles/clarification.md`](./regles/clarification.md) et pose 1 à 3 questions précises avant de générer ou d'appeler l'API.
2. **Si toutes les informations sont réunies** : génère le fichier HTML complet en respectant `erreurs-connues.md`, ouvre l'aperçu local dans le navigateur et attends la validation explicite de l'utilisateur avant tout appel d'écriture sur `https://api-pro-web.propulse-lab.com`.

---

## Étape 4 — Boucle d'Amélioration Continue

Dès que l'utilisateur corrige l'IA sur une règle, un style ou une spécificité :
- Applique [`regles/amelioration-continue-letta.md`](./regles/amelioration-continue-letta.md) pour consigner la règle dans `erreurs-connues.md` ou ouvrir une Issue via `.github/ISSUE_TEMPLATE/feedback.yml`.
