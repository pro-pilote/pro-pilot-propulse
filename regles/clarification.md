# Clarification avant Action & Zéro Invention

## 1. Interdiction d'inventer une donnée métier
- Ne devine **jamais** un tarif, une offre, une clé d'objet (`key`), un identifiant de site (`websiteId`), un identifiant GTM, une URL cible ou une mention légale.
- Toute donnée injectée dans une page ou un appel API doit provenir :
  1. Du brief fourni par le partenaire,
  2. Ou des fichiers du dépôt partenaire (`donnees-business/<sku>/fiche-produit.md`, `donnees-business/design-system.md` et `outils/<outil>/variables.md`),
  3. Ou de l'API publique `GET https://api-pro-web.propulse-lab.com/websites` (header `x-api-key`).

## 2. Poser les questions manquantes en une seule fois
Si le brief du partenaire est incomplet pour générer la page ou exécuter l'appel API :
1. Liste les 1 à 3 informations précises qui te manquent avant de commencer.
2. Propose les valeurs trouvées dans le dépôt partenaire si elles existent (ex. *« J'ai trouvé le domaine `www.impact-imminent.com` (`websiteId: 6adf1d86f8b0a23e8bd8bfb5`) dans ton dépôt Panthéon : je publie bien l'objet sous la clé `pages/dossier-special` sur ce site ? »*).
