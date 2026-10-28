# Outil : Pro Web Page Creator (Création de Landing Pages & Pages Web)

## 1. Objectif
Générer des pages web de haute qualité (Landing Pages d'acquisition, pages d'inscription webinaire, pages éditoriales) à partir d'un brief partenaire (ex. Google Doc), prêtes à être publiées sur Pro Web.

## 2. Fichiers à consulter dans le Repo Partenaire avant génération
1. `donnees-business/<bu>/<produit>/fiche-produit.md` (promesse, arguments, intervenant/auteur, mentions légales).
2. `donnees-business/<bu>/<produit>/design-system.md` (palette de couleurs, typographies, style des boutons CTA, mise en page).
3. `outils/pro-web-page-creator/variables.md` (ID GTM, domaine cible, scripts obligatoires).
4. `outils/pro-web-page-creator/specificites.md` et `erreurs-connues.md`.

## 3. Règles d'Or de Structure HTML/CSS
- **Zones protégées** : ne jamais inventer ou modifier à la main un script de formulaire d'acquisition ou d'inscription webinaire. Utiliser exclusivement le snippet officiel issu de `outils/pro-webinaire/` ou `outils/pro-acquisition/`.
- **Responsive Mobile-First** : utiliser des grilles flex/grid fluides, tester systématiquement l'affichage mobile (375px) et desktop (1280px).
- **Chemins des ressources** : utiliser des chemins relatifs propres ou les URLs CDN validées du partenaire.

## 4. Prévisualisation et Publication
Une fois la page générée, utiliser [`outils/pro-web-uploader/README.md`](../pro-web-uploader/README.md) pour lancer l'aperçu local (`127.0.0.1`) puis publier sur Pro Web.
