# Guide Propulse Lab — Pro Web Page Creator ([[ppl.partner_name]])

## 1. Objectif & Paramètres Pré-remplis
Générer des pages web de haute qualité (Landing Pages d'acquisition, pages d'inscription webinaire, pages éditoriales) pour **[[ppl.partner_name]]** (`partner_id: [[ppl.partner_id]]`), prêtes à être publiées sur `https://[[ppl.main_domain]]`.

- **Partenaire** : [[ppl.partner_name]] (`[[ppl.partner_id]]`)
- **Domaine Principal** : `[[ppl.main_domain]]`
- **Conteneur GTM obligatoire** : `[[ppl.gtm_id]]`

## 2. Fichiers à consulter dans ce dépôt avant génération
1. `donnees-business/<bu>/<produit>/fiche-produit.md` (promesse, arguments, intervenant/auteur, mentions légales).
2. `donnees-business/<bu>/<produit>/design-system.md` (palette de couleurs, typographies, style des boutons CTA).
3. [`specificites.md`](./specificites.md) et [`erreurs-connues.md`](./erreurs-connues.md).

## 3. Règles d'Or de Structure HTML/CSS
- **Zones protégées** : ne jamais inventer ou modifier à la main un script de formulaire d'acquisition ou d'inscription webinaire. Utiliser exclusivement le snippet officiel pré-rempli dans `outils/pro-webinaire/guide-propulse.md` ou `outils/pro-acquisition/guide-propulse.md`.
- **Tracking GTM** : toujours conserver le conteneur `[[ppl.gtm_id]]` intact.
- **Responsive Mobile-First** : tester systématiquement l'affichage mobile (`375px`) et desktop (`1280px`).

## 4. Prévisualisation et Publication
Utiliser `outils/pro-web-uploader/guide-propulse.md` pour lancer l'aperçu local (`http://127.0.0.1`) puis publier sur `[[ppl.main_domain]]`.
