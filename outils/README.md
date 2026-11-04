# Catalogue des Outils Autorisés — Pro-Pilot

Ce répertoire contient les spécifications et guides des 2 outils Pro Web mis à disposition des partenaires :

1. **`pro-web-uploader`** : Création, prévisualisation locale et publication d'**objets** (`PAGE` HTML ou `DOCUMENT` PDF/image) sur Pro Web via le flow `signed-url` $\rightarrow$ `PUT S3` $\rightarrow$ `upsert` (avec invalidation CloudFront automatique).
2. **`pro-web-page-creator`** : Scraping et import d'une URL externe (`originalUrl`, ex. Leadpages) vers Pro Web en tant qu'objet `PAGE` (`upload-page` / `reload-page` : minification HTML, nettoyage des scripts tiers, rapatriement des images `<img>` vers S3 `_assets/img/`).
