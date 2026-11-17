# Clarification avant Action & Zéro Invention

## 1. Interdiction absolue d'inventer une donnée métier (STOP-Condition)
- Ne devine **jamais** un tarif, une offre, un argument produit, une clé d'objet (`key`), un identifiant de site (`websiteId`), un identifiant GTM, une URL cible ou une mention légale.
- Toute donnée injectée dans une page ou un appel API doit provenir exclusivement :
  1. Du brief fourni par le partenaire dans la conversation,
  2. Ou de la lecture live du dépôt partenaire via `GET https://pro-pilot.propulse-lab.com/api/repo` (`donnees-business/<sku>/fiche-produit.md`, `donnees-business/design-system.md` et `skills/<nom-skill>/variables.md`).
- **STOP-Condition sur `[À COMPLÉTER]`** : Si `donnees-business/<sku>/fiche-produit.md` ou `skills/<nom-skill>/variables.md` contient `[À COMPLÉTER]` sur un champ requis, **bloque la génération** et demande ces éléments précis à l'utilisateur avant d'écrire le HTML.

## 2. Poser les questions manquantes en une seule fois
Si le brief du partenaire est incomplet pour générer la page ou exécuter l'appel API :
1. Liste les 1 à 3 informations précises qui te manquent avant de commencer.
2. Propose les valeurs exactes lues dans `skills/<nom-skill>/variables.md` du dépôt partenaire (ex. *« J'ai trouvé le site `<domaine-cible>` (`websiteId: <websiteId>`) dans `skills/pro-web/variables.md` : je publie bien l'objet sous la clé `pages/<slug>` sur ce domaine ? »*).
