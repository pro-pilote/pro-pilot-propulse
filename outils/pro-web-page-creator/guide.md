# Guide Pas à Pas — Pro Web Page Creator (Import d'URL externe)

`pro-web-page-creator` permet de **scraper une URL externe** (`originalUrl`, ex. une page Leadpages `https://<account>.lpages.co/<slug>/`) pour l'importer chez nous sur Pro Web en tant qu'objet `type: "PAGE"` (`key: "pages/<slug>"`).

## 1. Fonctionnement du Pipeline (`upload-page`)
Lors d'un appel à `POST /api/objects/upload-page` :
1. **Scraping & Nettoyage** : Récupère le HTML de `originalUrl`, nettoie les scripts tiers (analytics Leadpages, meta `leadpages-*`), passe `<html lang="en">` en `<html lang="fr">` et minifie le HTML.
2. **Rapatriement des images (`getImages`)** : Télécharge les balises `<img src="...">`, génère les variantes responsive (`320` à `2500px`) et les héberge sur S3 sous `<key>_assets/img/` avec `srcset`.
3. **Injection & Publication** : Injecte le `customDom` du site (GTM, scripts) et crée/met à jour l'objet `PAGE` sur S3 et MongoDB (`s3objects`).

## 2. Différence entre `upload-page` et `reload-page`
- **`POST /api/objects/upload-page`** : Exécute le pipeline complet (HTML + rapatriement des images `<img>` vers S3).
- **`GET /api/objects/{objectId}/reload-page`** : Re-fetche uniquement le HTML brut depuis `originalUrl` **sans** rapatrier les images. Si des images manquent ou ont changé, utiliser obligatoirement `upload-page`.

## 3. Garde-fous & Contraintes Techniques
- **URL strictement ASCII et HTTP 200 direct** : `originalUrl` ne doit contenir aucun caractère accentué (ex. pas de `é`) et ne doit pas renvoyer de redirection `302`, sinon l'import échoue en HTTP 500.
- **Images de fond CSS** : Seules les balises `<img>` sont rapatriées automatiquement ; les `background-image: url(...)` CSS relatives ne sont pas réécrites.
- **Protection des PDF** : Ne jamais lancer `reload-page` sur un objet `type: "PAGE"` qui sert en réalité un PDF (`application/pdf`), sous peine d'écraser le PDF par un wrapper HTML.
