# Guide Pas à Pas — Pro Web Page Creator (Import d'URL externe via API)

`pro-web-page-creator` permet de **scraper une URL externe** (`originalUrl`, ex. une page Leadpages `https://<account>.lpages.co/<slug>/`) pour l'importer chez nous sur Pro Web en tant qu'objet `type: "PAGE"` (`key: "pages/<slug>"`) via l'API publique (`https://api-pro-web.propulse-lab.com` avec `x-api-key: $PRO_WEB_API_KEY`).

## 1. Appels API (`x-api-key`)

Lire `ppl.website_id` et `ppl.partner_id` dans `outils/pro-web-page-creator/variables.md` et demander confirmation à l'utilisateur avant d'exécuter :

### A. Scraper et importer une URL externe (`POST /objects/upload-page`)
```bash
curl -sS -X POST "https://api-pro-web.propulse-lab.com/objects/upload-page" \
  -H "x-api-key: $PRO_WEB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "websiteId": "<WEBSITE_ID>",
    "partnerId": <PARTNER_ID>,
    "key": "pages/<slug>",
    "type": "PAGE",
    "subtype": "PAGE:LEADGEN",
    "originalUrl": "https://<account>.lpages.co/<slug>/",
    "hasIndexing": false
  }'
```

### B. Recharger uniquement le HTML d'un objet existant (`POST /objects/{objectId}/reload-page`)
```bash
curl -sS -X POST "https://api-pro-web.propulse-lab.com/objects/<OBJECT_ID>/reload-page" \
  -H "x-api-key: $PRO_WEB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "partnerId": <PARTNER_ID>
  }'
```

## 2. Fonctionnement du Pipeline (`upload-page` vs `reload-page`)
1. **Scraping & Nettoyage** : Récupère le HTML de `originalUrl`, nettoie les scripts tiers (analytics Leadpages, meta `leadpages-*`), passe `<html lang="en">` en `<html lang="fr">` et minifie le HTML.
2. **Rapatriement des images (`getImages`, uniquement sur `upload-page`)** : Télécharge les balises `<img src="...">`, génère les variantes responsive (`320` à `2500px`) et les héberge sur S3 sous `<key>_assets/img/` avec `srcset`.
3. **Injection & Publication** : Injecte le `customDom` du site (GTM, scripts) et crée/met à jour l'objet `PAGE` sur S3 et MongoDB (`s3objects`).

## 3. Garde-fous & Contraintes Techniques
- **URL strictement ASCII et HTTP 200 direct** : `originalUrl` ne doit contenir aucun caractère accentué (ex. pas de `é`) et ne doit pas renvoyer de redirection `302`, sinon l'import échoue en HTTP 500.
- **Images de fond CSS** : Seules les balises `<img>` sont rapatriées automatiquement ; les `background-image: url(...)` CSS relatives ne sont pas réécrites.
- **Protection des PDF** : Ne jamais lancer `reload-page` sur un objet `type: "PAGE"` qui sert en réalité un PDF (`application/pdf`), sous peine d'écraser le PDF par un wrapper HTML.
