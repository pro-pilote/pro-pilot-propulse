# Guide Propulse Lab — Pro Web Page Creator ([[ppl.partner_name]])

## 1. Objectif & Paramètres Pré-remplis
Générer des pages web de haute qualité (Landing Pages d'acquisition, pages éditoriales) pour **[[ppl.partner_name]]** (`partner_id: [[ppl.partner_id]]`), prêtes à être publiées sur `https://[[ppl.main_domain]]`.

- **Partenaire** : [[ppl.partner_name]] (`[[ppl.partner_id]]`)
- **Domaine Principal** : `[[ppl.main_domain]]`
- **Conteneur GTM obligatoire** : `[[ppl.gtm_id]]`

## 2. Fichiers à consulter dans ce dépôt avant génération
1. `donnees-business/<sku>/fiche-produit.md` (promesse, arguments, intervenant/auteur, mentions légales).
2. `donnees-business/design-system.md` (palette de couleurs, typographies, style des boutons CTA).
3. [`specificites.md`](./specificites.md) et [`erreurs-connues.md`](./erreurs-connues.md).

## 3. Règles d'Or de Structure HTML/CSS
- **Zones protégées** : conserver les marqueurs de formulaire et de mentions légales (`<!-- PPL:FORM -->`, `<!-- PPL:BLOC:mentions-legales -->`).
- **Tracking GTM** : toujours conserver le conteneur `[[ppl.gtm_id]]` intact (`<!-- PPL:GTM -->`).
- **Responsive Mobile-First** : tester systématiquement l'affichage mobile (`375px`) et desktop (`1280px`).

## 4. Prévisualisation et Publication
Consulter `guide.md` et `outils/pro-web-uploader/README.md` pour lancer l'aperçu local (`http://127.0.0.1:8080`) puis publier sur `[[ppl.main_domain]]`.
