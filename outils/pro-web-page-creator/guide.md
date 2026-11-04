# Guide Pas à Pas — Pro Web Page Creator (Import d'URL externe)

`pro-web-page-creator` permet de **scraper une URL externe** (`originalUrl`, ex. une page Leadpages `https://<account>.lpages.co/<slug>/`) pour l'importer chez nous sur Pro Web en tant qu'objet `type: "PAGE"` (`key: "pages/<slug>"`) via l'API publique (`x-api-key`).

## 1. Commandes CLI (`./ppl static`)
1. **Scraper et importer une URL externe (`upload-page`)** :
   - Dry-run : `./ppl static import-url <domaine> <originalUrl> --key pages/<slug>`
   - Publication : `./ppl static import-url <domaine> <originalUrl> --key pages/<slug> --go` (confirmation interactive `"OUI"`)
2. **Recharger uniquement le HTML d'un objet existant (`reload-page`)** :
   - Dry-run : `./ppl static reload-page <domaine> <objectId>`
   - Publication : `./ppl static reload-page <domaine> <objectId> --go`

## 2. Fonctionnement du Pipeline (`POST /objects/upload-page`)
Lors d'un appel à `POST /objects/upload-page` :
1. **Scraping & Nettoyage** : Récupère le HTML de `originalUrl`, nettoie les scripts tiers (analytics Leadpages, meta `leadpages-*`), passe `<html lang="en">` en `<html lang="fr">` et minifie le HTML.
2. **Rapatriement des images (`getImages`)** : Télécharge les balises `<img src="...">`, génère les variantes responsive (`320` à `2500px`) et les héberge sur S3 sous `<key>_assets/img/` avec `srcset`.
3. **Injection & Publication** : Injecte le `customDom` du site (GTM, scripts) et crée/met à jour l'objet `PAGE` sur S3 et MongoDB (`s3objects`).

## 3. Garde-fous & Contraintes Techniques
- **URL strictement ASCII et HTTP 200 direct** : `originalUrl` ne doit contenir aucun caractère accentué (ex. pas de `é`) et ne doit pas renvoyer de redirection `302`, sinon l'import échoue en HTTP 500.
- **Images de fond CSS** : Seules les balises `<img>` sont rapatriées automatiquement ; les `background-image: url(...)` CSS relatives ne sont pas réécrites.
- **Protection des PDF** : Ne jamais lancer `reload-page` sur un objet `type: "PAGE"` qui sert en réalité un PDF (`application/pdf`), sous peine d'écraser le PDF par un wrapper HTML.
