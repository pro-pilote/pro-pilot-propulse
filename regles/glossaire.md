# Glossaire Métier Propulse Lab

Ce glossaire définit les termes utilisés par les équipes Édito, Acquisition et Tech afin que l'IA comprenne immédiatement le vocabulaire du partenaire.

| Terme / Acronyme | Définition | Outil associé |
|---|---|---|
| **Objet Pro Web (`PAGE` / `DOCUMENT`)** | Entité hébergée sur un site Pro Web et identifiée par sa `key` (ex. `pages/<slug>`, `leads/<slug>`, `cadeau/<slug>`). Un objet `PAGE` est une page HTML ; un objet `DOCUMENT` est un fichier binaire (PDF, image). | `Pro Web Uploader` / `Pro Web Page Creator` |
| **LP (Landing Page)** | Page d'atterrissage HTML (`type: "PAGE"`) dédiée à la conversion (inscription newsletter, présentation d'offre, téléchargement de dossier), embarquant `headerTools.js`, `preserveParamsV2.js` et le conteneur GTM. | `Pro Web Uploader` / `Pro Web Page Creator` |
| **`headerTools.js` & `preserveParamsV2.js`** | Scripts officiels Pro Web hébergés sur `https://cdn.info-contenu.io/assets/` : `headerTools.js` expose `getParameterByName(name)` et `preserveParamsV2.js` propage automatiquement les paramètres d'URL (`utm_*`, `leadcode`, `salescode`, `bdc`, `urlBdc`) sur tous les liens `<a href>` vers le bon de commande. | `Pro Web Uploader` / `Pro Web Page Creator` |
| **Types de Sites Pro Web** | Catégorie d'hébergement d'un site dans Pro Web : `STATIC` (site statique dédié aux LPs/objets), `BLOG` (site éditorial), `PREMIUM` ou `PREMIUM_CONNECT` (espace membre / publication). | `Pro Web Uploader` / `Pro Web Page Creator` |
| **GTM (Google Tag Manager)** | Conteneur de suivi analytics propre à chaque partenaire (`GTM-XXXXXXX`). Ne doit jamais être altéré ni supprimé d'une page existante. | `Pro Web Uploader` |
| **Business Unit (BU)** | Marque ou pôle éditorial au sein d'un partenaire, référencé dans la fiche de chaque produit (`donnees-business/<sku>/fiche-produit.md`). | `donnees-business/<sku>/fiche-produit.md` |
| **Design System / Brandkit** | Charte graphique d'un partenaire et de ses publications : palette de couleurs, typographies, boutons (CTA) et composants visuels autorisés. | `donnees-business/design-system.md` |
| **Daily (Newsletter Quotidienne)** | Édition quotidienne déclinée en 2 volets coordonnés : **① Daily (Email)** dans Marketing Cloud (`freeformblock #195` + `templatebasedemail #207`) et **② Article sur le blog** (`BLOG` WordPress ou `STATIC` Pro Web). | `Daily Publisher` |
