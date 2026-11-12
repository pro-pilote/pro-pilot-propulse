# Catalogue des Outils Autorisés — Pro-Pilot

Ce répertoire contient les spécifications et guides des 2 outils mis à disposition des partenaires :

1. **`pro-web-uploader`** : Création, prévisualisation locale et publication d'**objets** (`PAGE` HTML ou `DOCUMENT` PDF/image) sur Pro Web via le flow `signed-url` $\rightarrow$ `PUT S3` $\rightarrow$ `upsert` (avec invalidation CloudFront automatique).
2. **`daily-publisher`** *(Work in Progress)* : Préparation, prévisualisation locale en **2 étapes** (**① Daily Email** $\rightarrow$ **② Article sur le blog**) et publication coordonnée d'une newsletter quotidienne dans **Salesforce Marketing Cloud** (`freeformblock #195` + `templatebasedemail #207`) et sur le **site éditorial** (via l'API REST WordPress `/wp-json/wp/v2/posts` ou l'API Pro Web Static en double arborescence `<slug>/index.html` + `articles/<slug>`).
