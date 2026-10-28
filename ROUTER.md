# Routeur Atomique Pro-Pilot (`ROUTER.md`)

Ce fichier est le point d'entrée de l'assistant IA à chaque demande du partenaire.
Les pages de Pro-Pilot sont articulées de manière **atomique** : ne charge jamais l'ensemble des fichiers d'un coup, descends uniquement dans la ou les branches nécessaires au besoin exprimé.

---

## Étape 1 — Lecture du Profil Local

1. Lis `.pro-pilot/profile.md` sur l'ordinateur de l'utilisateur.
   - *Si le fichier est absent ou incomplet* : ouvre immédiatement [`getting-started/onboarding.md`](./getting-started/onboarding.md) pour créer la fiche avec l'utilisateur.
2. Applique la règle de langage correspondant à son `niveau_technique` via [`regles/calibration-niveau-tech.md`](./regles/calibration-niveau-tech.md).
3. Consulte [`regles/glossaire.md`](./regles/glossaire.md) si la demande utilise un acronyme métier (LP, BDC, PSOU, PCOU, GTM, Salle).

---

## Étape 2 — Arbre de Routage selon le Besoin

Identifie l'intention du partenaire et descends dans les branches correspondantes (dans le **Repo Partenaire** puis dans ce **Repo Socle Propulse Lab**) :

| Besoin exprimé par le partenaire | 1. Branche à lire dans le **Repo Partenaire** (`pro-pilot-<slug>`) | 2. Branche à lire dans le **Repo Propulse Lab** (`pro-pilot-propulse`) | 3. Script `/pro-tools` à utiliser |
|---|---|---|---|
| **Créer ou refondre une Landing Page (LP) / page statique** (ex. depuis un Google Doc) | `donnees-business/<bu>/<produit>/fiche-produit.md`<br>`donnees-business/<bu>/<produit>/design-system.md`<br>`outils/pro-web-page-creator/variables.md`<br>`outils/pro-web-page-creator/specificites.md`<br>`outils/pro-web-page-creator/erreurs-connues.md` | [`outils/pro-web-page-creator/README.md`](./outils/pro-web-page-creator/README.md)<br>[`regles/clarification-avant-action.md`](./regles/clarification-avant-action.md)<br>[`regles/checklist-pre-livraison.md`](./regles/checklist-pre-livraison.md) | `python3 tools/ppl.py static` |
| **Publier ou mettre à jour une page sur Pro Web** | `outils/pro-web-uploader/specificites.md`<br>`outils/pro-web-uploader/erreurs-connues.md` | [`outils/pro-web-uploader/README.md`](./outils/pro-web-uploader/README.md)<br>[`regles/garde-fous-execution.md`](./regles/garde-fous-execution.md)<br>[`regles/anti-collision.md`](./regles/anti-collision.md) | `python3 tools/ppl.py static` (`pull`, `preview`, `push --go`) |
| **Créer une page d'inscription Webinaire ou configurer une salle** | `donnees-business/<bu>/<produit>/fiche-produit.md`<br>`outils/pro-webinaire/variables.md`<br>`outils/pro-webinaire/specificites.md`<br>`outils/pro-webinaire/erreurs-connues.md` | [`outils/pro-webinaire/README.md`](./outils/pro-webinaire/README.md)<br>[`outils/pro-web-page-creator/README.md`](./outils/pro-web-page-creator/README.md) | `python3 tools/ppl.py webinar` + `static` |
| **Créer ou modifier un Bon de Commande (BDC) / Formulaire d'acquisition** | `donnees-business/<bu>/<produit>/fiche-produit.md`<br>`outils/pro-acquisition/variables.md`<br>`outils/pro-acquisition/specificites.md`<br>`outils/pro-acquisition/erreurs-connues.md` | [`outils/pro-acquisition/README.md`](./outils/pro-acquisition/README.md)<br>[`regles/garde-fous-execution.md`](./regles/garde-fous-execution.md) | `python3 tools/ppl.py bdc` (`pull`, `audit`, `preview`, `push --go`) |
| **Consulter ou vérifier des règles CRM Salesforce** | `outils/salesforce/specificites.md` (si présent) | [`outils/salesforce/README.md`](./outils/salesforce/README.md) | Lecture documentaire |
| **Analyser des données / KPIs via Bi-Brother (DATA)** | `outils/bi-brother/specificites.md` (si présent) | [`outils/bi-brother/README.md`](./outils/bi-brother/README.md) | Lecture / requête guidée |
| **Créer ou suivre une demande ClickUp** | `outils/clickup/specificites.md` (si présent) | [`outils/clickup/README.md`](./outils/clickup/README.md) | Modèle structuré |

---

## Étape 3 — Interaction ou Action

1. **Si une information essentielle manque** dans la demande du partenaire (ex. produit concerné, date d'événement, offre tarifaire non précisée dans `fiche-produit.md`) : applique [`regles/clarification-avant-action.md`](./regles/clarification-avant-action.md) et pose la question avant de générer.
2. **Si toutes les informations sont réunies** : génère le livrable en respectant scrupuleusement `erreurs-connues.md` du partenaire et [`regles/checklist-pre-livraison.md`](./regles/checklist-pre-livraison.md), puis lance l'aperçu local (`preview`) via `/pro-tools`.

---

## Étape 4 — Détection de Correction & Boucle d'Amélioration Continue

Dès que le partenaire te corrige (sur un style, une règle métier, un bloc HTML, un GTM ou une erreur d'outil) :
- Applique immédiatement [`regles/amelioration-continue-letta.md`](./regles/amelioration-continue-letta.md) pour proposer la remontée du retour sur le dépôt du partenaire via le formulaire `.github/ISSUE_TEMPLATE/feedback.yml`.
