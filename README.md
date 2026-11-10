# Pro-Pilot — Socle Propulse Lab (`pro-pilot-propulse`)

Socle central de connaissances et de contrats d'API pour accompagner les équipes partenaires dans la création et la publication d'objets Pro Web (`PAGE` HTML et `DOCUMENT` PDF/Image) et l'import d'URLs externes via l'API publique (`https://api-pro-web.propulse-lab.com` avec `x-api-key`).

## Architecture du Dépôt (100 % Markdown, Zéro Script)

```text
pro-pilot-propulse/
├── VERSION                                # Version courante du socle
├── README.md                              # Présentation du socle
├── ROUTER.md                              # Routeur arborescent atomique (Point d'entrée IA)
├── getting-started/                       # Onboarding & Prérequis
│   ├── README.md                          # Guide d'onboarding local
│   └── prerequis.md                       # Prérequis & configuration de la clé PRO_WEB_API_KEY
├── regles/                                # // REGLES (Socle de fonctionnement IA commun)
│   ├── README.md                          # Index des règles
│   ├── glossaire.md                       # Terminologie métier unifiée (LP, STATIC, GTM, BU)
│   ├── clarification.md                   # Zéro invention : poser les questions si données manquantes
│   ├── garde-fous.md                      # Preview locale + validation humaine avant appel API
│   └── amelioration-continue-letta.md     # Remontée des retours partenaires en Issue GitHub
└── outils/                                # // OUTILS (API Pro Web, Marketing Cloud & WordPress)
    ├── README.md                          # Catalogue des outils autorisés
    ├── daily-publisher/
    │   └── guide.md                       # Générer, prévisualiser (Studio 2 étapes) et publier un Daily (Email SFMC + Article Blog/Static)
    ├── pro-web-page-creator/
    │   └── guide.md                       # Scraper une URL externe (ex. Leadpages) pour l'importer sur Pro Web
    └── pro-web-uploader/
        └── guide.md                       # Créer, prévisualiser et publier un objet (PAGE/DOCUMENT) sur Pro Web
```
