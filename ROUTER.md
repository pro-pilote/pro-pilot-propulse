# Matrice de Décision — Router d'Actions Pro-Pilot

## Étape 1 — Détection de l'Intention

1. **Création ou modification directe d'une page HTML ou d'un document PDF/image** $\rightarrow$ [Action A — Pro Web Uploader](.claude/commands/pro-web.md#action-a--creer-retoucher-et-publier-un-objet-page-html-ou-document)
2. **Inspection / inventaire des objets d'un site** $\rightarrow$ [Action B — Liste des objets](.claude/commands/pro-web.md#action-b--lister-ou-inspecter-les-objets-dun-site)

*(Rappel de sécurité : La suppression d'objets n'est pas autorisée par API en v1. Toute suppression définitive doit être effectuée manuellement par un opérateur humain depuis l'interface web Pro Web).*

---

## Étape 2 — Chargement du Contexte Métier & Validation des Types

1. Charge les variables d'environnement (`set -a; source .env; set +a`).
2. Identifie le domaine cible et résous le `websiteId` correspondant dans [`outils/pro-web-uploader/variables.md`](./outils/pro-web-uploader/variables.md).
3. Consulte [`donnees-business/design-system.md`](./donnees-business/design-system.md) et la fiche produit dans `donnees-business/<sku>/fiche-produit.md`.
4. Respecte les 5 sous-types valides pour `PAGE` : `PAGE:LEADGEN` (acquisition/opt-in), `PAGE:CONFIRMATION` (merci), `PAGE:VIDEO` (vidéo), `PAGE:PAID` (copie de vente), `PAGE:OTHER` (divers).

---

## Étape 3 — Interaction et Action

1. **Si une information essentielle manque** : pose 1 à 3 questions précises avant de générer ou d'appeler l'API.
2. **Si toutes les informations sont réunies** : génère le fichier HTML complet dans le dossier éphémère `.tmp/` en respectant `erreurs-connues.md` (aucun fichier HTML ne doit être committé sur Git), ouvre l'aperçu local dans le navigateur ou Claude Artifacts et attends la validation explicite de l'utilisateur avant tout appel d'écriture sur `https://api-pro-web.propulse-lab.com`.

---

## Étape 4 — Boucle d'Amélioration Continue

Dès que l'utilisateur corrige l'IA sur une règle, un style ou une spécificité :
- Applique immédiatement [`.claude/commands/feedback.md`](./.claude/commands/feedback.md) (ou la commande `/feedback`) pour enregistrer la règle dans `specificites.md`, `erreurs-connues.md` ou `donnees-business/` et synchroniser le dépôt en tâche de fond via le portail Pro-Pilot.
