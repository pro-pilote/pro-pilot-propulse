# Pro-Pilot — Socle Propulse Lab (`pro-pilot-propulse`)

Socle central de connaissances, de routage et d'outillage `/pro-tools` pour accompagner les équipes partenaires dans la création et la publication de contenus (Landing Pages, Webinaires, Acquisition, CRM, Data).

## Architecture du Dépôt

```text
pro-pilot-propulse/
├── VERSION                           # Version courante du socle
├── ROUTER.md                         # Routeur arborescent atomique (Point d'entrée IA)
├── getting-started/                  # Starter pack & questionnaire d'onboarding local
│   ├── README.md                     # Guide d'installation rapide
│   ├── onboarding.md                 # Protocole d'entretien initial (4 questions)
│   └── profile.template.md           # Modèle de la fiche mémoire locale (.pro-pilot/profile.md)
├── regles/                           # // REGLES (Socle de fonctionnement IA)
│   ├── glossaire.md                  # Terminologie métier unifiée
│   ├── amelioration-continue-letta.md# Boucle d'apprentissage sur retour partenaire
│   ├── calibration-niveau-tech.md    # Adaptation du vocabulaire au profil utilisateur
│   ├── clarification-avant-action.md # Collecte des informations manquantes avant génération
│   ├── checklist-pre-livraison.md    # Contrôles qualité obligatoires avant présentation
│   ├── garde-fous-execution.md       # Zones protégées, aperçu local et confirmation humaine
│   └── anti-collision.md             # Vérification de non-écrasement avant publication
├── outils/                           # // OUTILS (Guides atomiques par outil)
│   ├── pro-web-uploader/README.md
│   ├── pro-web-page-creator/README.md
│   ├── pro-webinaire/README.md
│   ├── pro-acquisition/README.md
│   ├── salesforce/README.md
│   ├── bi-brother/README.md
│   └── clickup/README.md
└── tools/                            # Scripts d'exécution locale /pro-tools (CLI ppl)
```
