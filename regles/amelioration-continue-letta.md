# Règles d'Amélioration Continue (Boucle de Feedback Partenaire)

Le cœur de **Pro-Pilot** repose sur l'apprentissage continu : lorsqu'un partenaire corrige l'IA sur un rendu ou un comportement, cette erreur ne doit plus jamais se reproduire chez ce partenaire.

## 1. Quand déclencher une remontée de Feedback ?

Déclenche cette procédure dès que l'utilisateur :
- Corrige une erreur produite par l'IA sur un outil (ex. mauvais emplacement d'un script, oubli d'une variable GTM, structure mobile cassée).
- Précise une règle business ou graphique permanente de sa marque qui n'était pas encore écrite dans son dépôt (ex. *« Chez nous, le bandeau auteur doit toujours être fond bleu marine »*).

## 2. Comment classer le retour (Dossier cible dans le Repo Partenaire)

| Nature de la correction du partenaire | Fichier cible dans `pro-pilot-<partenaire>` |
|---|---|
| Erreur technique ou piège commis par l'IA sur un outil | `outils/<nom-outil>/erreurs-connues.md` |
| Variable technique manquante ou erronée (GTM, domaine, `websiteId`) | `outils/<nom-outil>/variables.md` |
| Particularité d'un site ou règle métier sur un outil | `outils/<nom-outil>/specificites.md` |
| Charte graphique, couleur, typographie ou composant visuel | `donnees-business/design-system.md` |
| Offre, tarif, promesse, FAQ ou mention légale d'un produit | `donnees-business/<sku>/fiche-produit.md` |

## 3. Remontée sur le dépôt du partenaire (Issue GitHub)

1. Corrige d'abord immédiatement le travail en cours pour satisfaire la demande du partenaire.
2. Propose ensuite au partenaire d'enregistrer cette règle dans la mémoire de son dépôt en ouvrant une **Issue GitHub** formatée selon `.github/ISSUE_TEMPLATE/feedback.yml` :
   - **Titre** : `[FEEDBACK][<outil ou produit>] Résumé court de la règle`
   - **Label** : `statut:à-trier`
   - **Contenu** :
     - Contexte / Demande initiale
     - Ce que l'IA avait généré par erreur
     - La règle exacte à retenir
     - Le chemin du fichier cible (ex. `outils/pro-web-uploader/erreurs-connues.md`)
     - Le bloc Markdown exact prêt à être ajouté dans ce fichier.

> **Traitement par Propulse Lab** : Les retours sont relus et intégrés dans le dépôt du partenaire (ou dans le socle commun `pro-pilot-propulse` lorsqu'ils concernent tous les partenaires).
