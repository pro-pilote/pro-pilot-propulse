# Pro-Pilot — Socle Propulse Lab (`pro-pilot-propulse`)

Socle central de connaissances, de routage et d'outillage pour accompagner les équipes partenaires dans la création et la publication d'objets Pro Web (Landing Pages, PDF, Images et Sites Statiques).

## Architecture du Dépôt

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
│   ├── garde-fous.md                      # Preview locale + confirmation "OUI" avant publication
│   └── amelioration-continue-letta.md     # Remontée des retours partenaires en Issue GitHub
├── outils/                                # // OUTILS (Focus 100% Pro Web)
│   ├── README.md                          # Catalogue des outils autorisés
│   ├── pro-web-page-creator/
│   │   └── guide.md                       # Scraper une URL externe (ex. Leadpages) pour l'importer sur Pro Web
│   └── pro-web-uploader/
│       └── guide.md                       # Créer, prévisualiser et publier un objet (PAGE/DOCUMENT) sur Pro Web
└── tools/                                 # Moteur d'exécution local (CLI ppl — 100% API Key)
    ├── .claude/
    │   └── settings.json                  # Règles deny de sécurité Claude
    ├── bootstrap.template.py              # Template du script bootstrap partenaire
    ├── ppl                                # Lanceur macOS / Linux
    ├── ppl.cmd                            # Lanceur Windows
    ├── ppl.py                             # CLI unifié (static, doctor, render)
    ├── ppl_static.py                      # Déploiement S3/CloudFront & API Publique Pro Web
    └── proweb_env.py                      # Détection d'environnement & lecture PRO_WEB_API_KEY
```
