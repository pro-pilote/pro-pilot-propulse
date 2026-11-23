# Pro-Pilot — Socle Propulse Lab (`pro-pilot-propulse`)

Socle public central des **Skills** et des règles d'exécution Pro-Pilot pour accompagner les équipes partenaires et internes dans la création, la prévisualisation et la publication d'objets Pro Web (`PAGE` HTML et `DOCUMENT` PDF/Image) et de la structure des espaces membres (`pro-blocks`).

## Architecture du Dépôt (100 % Skills, Lecture Live)

```text
pro-pilot-propulse/
├── VERSION                                # Version courante du socle (2.0.0)
├── README.md                              # Présentation du socle
├── ROUTER.md                              # Routeur d'actions IA (point d'entrée live)
├── regles/                                # Règles transverses d'exécution IA
│   ├── README.md                          # Index des règles
│   ├── glossaire.md                       # Terminologie métier unifiée (LP, STATIC, GTM, BU)
│   ├── clarification.md                   # Zéro invention : poser les questions si données manquantes
│   ├── garde-fous.md                      # Preview locale + validation humaine avant appel API
│   └── amelioration-continue-letta.md     # Boucle de feedback partenaire append-only (_inbox)
└── skills/                                # Catalogue unifié des Skills (remplace outils/)
    ├── README.md                          # Catalogue des skills disponibles
    ├── _loaders/                          # Lanceurs légers installés sur le poste client
    │   ├── pro-web.md                     # Chargeur live /pro-web
    │   ├── pro-blocks.md                  # Chargeur live /pro-blocks
    │   ├── pro-daily.md                   # Chargeur live /pro-daily (interne)
    │   └── learn.md                       # Chargeur live /learn
    ├── pro-web/
    │   └── SKILL.md                       # Création, retouche et publication d'objets Pro Web
    ├── pro-blocks/
    │   └── SKILL.md                       # Blocs et configuration des espaces membres
    ├── pro-daily/
    │   └── SKILL.md                       # Studio 2 étapes Email SFMC + Article Blog/Static (Interne WIP)
    └── learn/
        └── SKILL.md                       # Apprentissage continu et bilan rétrospectif vers donnees-business/_inbox/
```

## Fonctionnement Sans Copie Obsolète

1. Le poste utilisateur ne clone aucun dépôt : il conserve uniquement son fichier `.env` local (`chmod 600`) et les lanceurs légers `skills/_loaders/*.md` dans `.claude/commands/`.
2. À chaque appel (`/pro-web`, `/pro-blocks`, `/learn`), le lanceur récupère en direct la dernière version de `skills/<nom-skill>/SKILL.md` sur `main` (mise à jour instantanée pour tous les utilisateurs).
3. Les données métier et les paramètres propres au partenaire (`donnees-business/` et `skills/<nom-skill>/{variables,specificites,erreurs-connues}.md`) résident dans le dépôt privé `pro-pilot-<partner>` et sont lus en temps réel via `GET https://pro-pilot.propulse-lab.com/api/repo?path=...` authentifié par `$PRO_PILOT_WRITE_TOKEN`.
