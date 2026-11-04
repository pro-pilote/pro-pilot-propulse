# Routeur Atomique Pro-Pilot (`ROUTER.md`)

Ce fichier est le point d'entrée de l'assistant IA pour l'orientation et l'exécution des demandes Pro Web.
Les pages de Pro-Pilot sont articulées de manière **atomique** : ne charge jamais l'ensemble des fichiers d'un coup, descends uniquement dans la ou les branches nécessaires au besoin exprimé.

---

## Étape 1 — Prise en Main & Profil Utilisateur

1. Consulte [`getting-started/README.md`](./getting-started/README.md) pour les instructions de mise en route et le questionnaire initial.
2. Consulte [`regles/glossaire.md`](./regles/glossaire.md) pour la terminologie métier (LP, STATIC, GTM, BU, Design System).

---

## Étape 2 — Arbre de Routage Pro Web

Identifie l'intention et consulte uniquement les fichiers correspondants :

| Besoin exprimé | 1. Données Business | 2. Spécifications & Guides | 3. Règles & Commandes |
|---|---|---|---|
| **Créer ou modifier une Landing Page (LP)** (ex. depuis un Google Doc) | `donnees-business/<sku>/fiche-produit.md`<br>`donnees-business/design-system.md` | [`outils/pro-web-page-creator/guide.md`](./outils/pro-web-page-creator/guide.md)<br>`outils/pro-web-page-creator/specificites.md`<br>`outils/pro-web-page-creator/erreurs-connues.md` | [`regles/clarification.md`](./regles/clarification.md)<br>Tester avec `./ppl static preview <domaine>` |
| **Publier ou prévisualiser un site sur Pro Web** | — | [`outils/pro-web-uploader/guide.md`](./outils/pro-web-uploader/guide.md)<br>`outils/pro-web-uploader/specificites.md`<br>`outils/pro-web-uploader/variables.md` | [`regles/garde-fous.md`](./regles/garde-fous.md)<br>Déployer avec `./ppl static push <domaine>` |

---

## Étape 3 — Interaction ou Action

1. **Si une information essentielle manque** (ex. produit concerné, GTM ou slug) : applique [`regles/clarification.md`](./regles/clarification.md) et pose 1 à 3 questions précises avant de générer.
2. **Si toutes les informations sont réunies** : génère le code HTML en respectant `erreurs-connues.md`, puis propose la prévisualisation locale (`./ppl static preview <domaine>`).

---

## Étape 4 — Boucle d'Amélioration Continue

Dès que l'utilisateur corrige l'IA sur une règle, un style ou une spécificité :
- Applique [`regles/amelioration-continue-letta.md`](./regles/amelioration-continue-letta.md) pour consigner la règle dans `erreurs-connues.md` ou ouvrir une Issue via `.github/ISSUE_TEMPLATE/feedback.yml`.
