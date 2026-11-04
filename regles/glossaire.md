# Glossaire Métier Propulse Lab

Ce glossaire définit les termes utilisés par les équipes Édito, Acquisition et Tech afin que l'IA comprenne immédiatement le vocabulaire du partenaire.

| Terme / Acronyme | Définition | Outil associé |
|---|---|---|
| **Objet Pro Web (`PAGE` / `DOCUMENT`)** | Entité hébergée sur un site Pro Web et identifiée par sa `key` (ex. `pages/<slug>`, `leads/<slug>`, `cadeau/<slug>`). Un objet `PAGE` est une page HTML ; un objet `DOCUMENT` est un fichier binaire (PDF, image). | `Pro Web Uploader` / `Pro Web Page Creator` |
| **LP (Landing Page)** | Page d'atterrissage HTML (`type: "PAGE"`) dédiée à la conversion (inscription newsletter, présentation d'offre, téléchargement de dossier). | `Pro Web Uploader` / `Pro Web Page Creator` |
| **Site Statique (`STATIC`)** | Site Pro Web (`type: "STATIC"`) sur lequel sont publiés les objets `PAGE` et `DOCUMENT` via l'API publique `https://api-pro-web.propulse-lab.com`. | `Pro Web Uploader` |
| **GTM (Google Tag Manager)** | Conteneur de suivi analytics propre à chaque partenaire (`GTM-XXXXXXX`). Ne doit jamais être altéré ni supprimé d'une page. | `Pro Web Uploader` |
| **Business Unit (BU)** | Marque ou pôle éditorial au sein d'un partenaire (ex. *Alternative Santé*, *Citadelle Suisse*, *IA Visionnaire*), référencé dans la fiche de chaque produit (`sku`). | `donnees-business/<sku>/fiche-produit.md` |
| **Design System / Brandkit** | Charte graphique d'un partenaire et de ses publications : palette de couleurs, typographies, boutons (CTA) et composants visuels autorisés. | `donnees-business/design-system.md` |
