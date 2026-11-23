# Catalogue des Skills — Pro-Pilot

Ce répertoire regroupe l'ensemble des **Skills** mises à disposition des partenaires et équipes internes (vocabulaire unifié `skills/` dans le socle public et dans les dépôts privés partenaires) :

1. **[`pro-web`](./pro-web/SKILL.md)** : Création, retouche, prévisualisation locale (`.tmp/`) et publication d'objets (`PAGE` HTML ou `DOCUMENT` PDF/image) sur Pro Web via le flow `signed-url` $\rightarrow$ `PUT S3` $\rightarrow$ `upsert`. Lit en direct `skills/pro-web/{variables,specificites,erreurs-connues}.md` et `donnees-business/` dans le dépôt partenaire.
2. **[`pro-blocks`](./pro-blocks/SKILL.md)** : Lecture, validation dry-run et publication sécurisée (CAS `baseVersion`, `overrides` uniquement) de la structure et des blocs des espaces membres abonnés via le portail Pro-Pilot (`/api/ai-child/*`).
3. **[`learn`](./learn/SKILL.md)** : Apprentissage continu, enregistrement immédiat de règles et bilan rétrospectif de session sans conflit dans `donnees-business/_inbox/` via `POST https://pro-pilot.propulse-lab.com/api/feedback`.
4. **[`_loaders/`](./_loaders/)** : Lanceurs immuables installés dans `.claude/commands/` sur le poste de l'utilisateur pour charger dynamiquement la dernière version de chaque `SKILL.md` sur `main`.
