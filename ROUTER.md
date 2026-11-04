# Routeur Atomique Pro-Pilot (`ROUTER.md`)

Ce fichier est le point d'entrée de l'assistant IA à chaque demande de **[[ppl.partner_name]]**.
Les pages de Pro-Pilot sont articulées de manière **atomique** : ne charge jamais l'ensemble des fichiers d'un coup, descends uniquement dans la ou les branches nécessaires au besoin exprimé.

---

## Étape 1 — Lecture du Profil Local

1. Lis `.pro-pilot/profile.md` sur l'ordinateur de l'utilisateur.
   - *Si le fichier est absent ou incomplet* : ouvre immédiatement [`getting-started/onboarding.md`](./getting-started/onboarding.md) pour créer la fiche avec l'utilisateur.
2. Applique la règle de langage correspondant à son `niveau_technique` via [`regles/calibration-niveau-tech.md`](./regles/calibration-niveau-tech.md).
3. Consulte [`regles/glossaire.md`](./regles/glossaire.md) si la demande utilise un acronyme métier (LP, BDC, PSOU, PCOU, GTM, Salle).

---

## Étape 2 — Arbre de Routage selon le Besoin

Identifie l'intention du partenaire et descends uniquement dans les branches correspondantes de ce dépôt :

| Besoin exprimé par le partenaire | 1. Données Business à lire | 2. Guides & Spécificités Outils à lire (déjà pré-remplis) | 3. Règles & Script `/pro-tools` |
|---|---|---|---|
| **Créer ou refondre une Landing Page (LP) / page statique** (ex. depuis un Google Doc) | `donnees-business/<sku>/fiche-produit.md`<br>`donnees-business/<sku>/design-system.md` | `outils/pro-web-page-creator/guide-propulse.md`<br>`outils/pro-web-page-creator/specificites.md`<br>`outils/pro-web-page-creator/erreurs-connues.md` | [`regles/clarification-avant-action.md`](./regles/clarification-avant-action.md)<br>[`regles/checklist-pre-livraison.md`](./regles/checklist-pre-livraison.md)<br>`python3 tools/ppl.py static` |
| **Publier ou mettre à jour une page sur Pro Web** | — | `outils/pro-web-uploader/guide-propulse.md`<br>`outils/pro-web-uploader/specificites.md`<br>`outils/pro-web-uploader/erreurs-connues.md` | [`regles/garde-fous-execution.md`](./regles/garde-fous-execution.md)<br>[`regles/anti-collision.md`](./regles/anti-collision.md)<br>`python3 tools/ppl.py static` |
| **Créer une page d'inscription Webinaire ou configurer une salle** | `donnees-business/<sku>/fiche-produit.md`<br>`donnees-business/<sku>/design-system.md` | `outils/pro-webinaire/guide-propulse.md`<br>`outils/pro-webinaire/specificites.md`<br>`outils/pro-webinaire/erreurs-connues.md`<br>`outils/pro-web-page-creator/guide-propulse.md` | `python3 tools/ppl.py webinar` + `static` |
| **Créer ou modifier un Bon de Commande (BDC) / Opt-in** | `donnees-business/<sku>/fiche-produit.md` | `outils/pro-acquisition/guide-propulse.md`<br>`outils/pro-acquisition/specificites.md`<br>`outils/pro-acquisition/erreurs-connues.md` | [`regles/garde-fous-execution.md`](./regles/garde-fous-execution.md)<br>`python3 tools/ppl.py bdc` |

---

## Étape 3 — Interaction ou Action

1. **Si une information essentielle manque** dans la demande du partenaire (ex. produit concerné, date d'événement, `<SALLE_SLUG>`) : applique [`regles/clarification-avant-action.md`](./regles/clarification-avant-action.md) et pose la question avant de générer.
2. **Si toutes les informations sont réunies** : génère le livrable en respectant scrupuleusement `erreurs-connues.md` et [`regles/checklist-pre-livraison.md`](./regles/checklist-pre-livraison.md), puis lance l'aperçu local (`preview`) via `/pro-tools`.

---

## Étape 4 — Détection de Correction & Boucle d'Amélioration Continue

Dès que le partenaire te corrige (sur un style, une règle métier, un bloc HTML, un GTM ou une erreur d'outil) :
- Applique immédiatement [`regles/amelioration-continue-letta.md`](./regles/amelioration-continue-letta.md) pour proposer la remontée du retour sur ce dépôt via le formulaire [`.github/ISSUE_TEMPLATE/feedback.yml`](./.github/ISSUE_TEMPLATE/feedback.yml).
