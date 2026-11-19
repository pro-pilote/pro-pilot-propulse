# Catalogue des Skills — Pro-Pilot

Ce répertoire regroupe l'ensemble des **Skills** mises à disposition des partenaires et équipes internes (vocabulaire unifié `skills/` dans le socle public et dans les dépôts privés partenaires) :

1. **[`pro-web`](./pro-web/SKILL.md)** : Création, retouche, prévisualisation locale (`.tmp/`) et publication d'objets (`PAGE` HTML ou `DOCUMENT` PDF/image) sur Pro Web via le flow `signed-url` $\rightarrow$ `PUT S3` $\rightarrow$ `upsert`. Lit en direct `skills/pro-web/{variables,specificites,erreurs-connues}.md` et `donnees-business/` dans le dépôt partenaire.
2. **[`sites-fulfi`](./sites-fulfi/SKILL.md)** : Lecture, validation dry-run et publication sécurisée (CAS `baseVersion`, `overrides` uniquement) de la configuration des sites Fulfi via le portail Pro-Pilot (`/api/ai-child/*`).
3. **[`daily-publisher`](./daily-publisher/SKILL.md)** *(Work in Progress)* : Préparation, prévisualisation locale en 2 étapes (**① Daily Email** $\rightarrow$ **② Article sur le blog**) scellée SHA-256 et publication coordonnée dans **Salesforce Marketing Cloud** (`freeformblock #195` + `templatebasedemail #207`) et sur le site éditorial (`BLOG` WordPress ou `STATIC` Pro Web). Lit en direct `skills/daily-publisher/{variables,specificites,erreurs-connues}.md`.
4. **[`fin`](./fin/SKILL.md)** : Enregistrement append-only sans conflit des retours, corrections et règles d'équipe dans `donnees-business/_inbox/` via `POST https://pro-pilot.propulse-lab.com/api/feedback`.
5. **[`_loaders/`](./_loaders/)** : Lanceurs immuables installés dans `.claude/commands/` sur le poste de l'utilisateur pour charger dynamiquement la dernière version de chaque `SKILL.md` sur `main`.
