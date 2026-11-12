# Matrice de Décision — Router d'Actions Pro-Pilot

## Étape 1 — Détection de l'Intention

1. **Création ou modification directe d'une page HTML ou d'un document PDF/image** $ightarrow$ [Action B — Pro Web Uploader](.claude/commands/pro-web.md#action-b--creer-retoucher-et-publier-un-objet-page-html-ou-document)
2. **Import et aspiration d'une page externe (ex. Leadpages)** $ightarrow$ [Action A — Import d'URL externe](.claude/commands/pro-web.md#action-a--importer-une-url-externe-ex-leadpages-vers-pro-web)
3. **Rechargement d'une page externe existante modifiée à la source** $ightarrow$ [Action C — Reload Page](.claude/commands/pro-web.md#action-c--recharger-une-page-externe-existante-reload-page)
4. **Inspection / inventaire des objets d'un site** $ightarrow$ [Action D — Liste des objets](.claude/commands/pro-web.md#action-d--lister-ou-inspecter-les-objets-dun-site)
5. **Suppression d'un objet en ligne** $ightarrow$ [Action E — Supprimer un objet](.claude/commands/pro-web.md#action-e--supprimer-un-objet-sur-pro-web)

---

## Étape 2 — Chargement du Contexte Métier & Validation des Types

1. Charge les variables d'environnement (`set -a; source .env; set +a`).
2. Identifie le domaine cible et résous le `websiteId` correspondant dans [`outils/pro-web-uploader/variables.md`](./outils/pro-web-uploader/variables.md).
3. Consulte [`donnees-business/design-system.md`](./donnees-business/design-system.md) et la fiche produit dans `donnees-business/<sku>/fiche-produit.md`.
4. Respecte les 5 sous-types valides pour `PAGE` : `PAGE:LEADGEN` (acquisition/opt-in), `PAGE:CONFIRMATION` (merci), `PAGE:VIDEO` (vidéo), `PAGE:PAID` (copie de vente), `PAGE:OTHER` (divers).

---

## Étape 3 — Interaction et Action

1. **Si une information essentielle manque** : pose 1 à 3 questions précises avant de générer ou d'appeler l'API.
2. **Si toutes les informations sont réunies** : génère le fichier HTML complet dans le dossier éphémère `.tmp/` en respectant `erreurs-connues.md` (aucun fichier HTML ne doit être committé sur Git), ouvre l'aperçu local dans le navigateur et attends la validation explicite de l'utilisateur avant tout appel d'écriture sur `https://api-pro-web.propulse-lab.com`.

---

## Étape 4 — Boucle d'Amélioration Continue

Dès que l'utilisateur corrige l'IA sur une règle, un style ou une spécificité :
- Applique immédiatement [`.claude/commands/feedback.md`](./.claude/commands/feedback.md) (ou la commande `/feedback`) pour enregistrer la règle dans `specificites.md`, `erreurs-connues.md` ou `donnees-business/` et synchroniser le dépôt en tâche de fond via le portail Pro-Pilot.
