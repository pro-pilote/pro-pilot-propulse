# Règles d'Amélioration Continue (Boucle de Feedback Partenaire)

Le cœur de **Pro-Pilot** repose sur l'apprentissage continu : lorsqu'un partenaire corrige l'IA sur un rendu ou un comportement, cette erreur est capitalisée sur son dépôt GitHub et lue en temps réel par tous les collaborateurs.

## 1. Quand déclencher une remontée de Feedback ?

Déclenche `/fin` en clôture d'échange ou dès que l'utilisateur :
- Corrige une erreur produite par l'IA sur une skill (ex. oubli d'un paramètre API, variable GTM erronée, encodage ou structure mobile).
- Précise une règle business ou graphique permanente de sa marque qui n'était pas encore écrite dans son dépôt.

## 2. Classification de la Cible dans `pro-pilot-<partenaire>`

| Nature de la correction du partenaire | Fichier cible dans `pro-pilot-<partenaire>` |
|---|---|
| Erreur technique ou piège commis par l'IA sur une skill | `skills/<nom-skill>/erreurs-connues.md` |
| Variable technique manquante ou erronée (GTM, domaine, `websiteId`) | `skills/<nom-skill>/variables.md` |
| Particularité d'un site ou règle éditoriale sur une skill | `skills/<nom-skill>/specificites.md` |
| Charte graphique, couleur, typographie ou composant visuel | `donnees-business/design-system.md` |
| Offre, tarif, promesse, FAQ ou mention légale d'un produit | `donnees-business/<sku>/fiche-produit.md` |

## 3. Enregistrement Append-Only via `/fin`

1. Corrige d'abord immédiatement le travail en cours pour satisfaire la demande du partenaire.
2. Exécute la skill [`/fin`](../skills/fin/SKILL.md) (`POST https://pro-pilot.propulse-lab.com/api/feedback`) qui écrit une note horodatée dans `donnees-business/_inbox/<ISO>_<auteur>_<sujet>_<uuid8>.md` sans conflit Git.
3. Les notes d'`_inbox/` sont consolidées dans les fichiers `skills/<nom-skill>/*` ou `donnees-business/*` du partenaire (ou dans le socle public `pro-pilot-propulse/skills/*` si la règle est universelle).
