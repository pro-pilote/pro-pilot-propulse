# Guide Propulse Lab — Pro Web Page Creator ([[ppl.partner_name]])

## 1. Objectif
Scraper une URL externe (`originalUrl`, ex. une page Leadpages `https://<account>.lpages.co/<slug>/`) pour l'importer chez nous sur Pro Web (`https://[[ppl.main_domain]]`) en tant qu'objet `type: "PAGE"` (`key: "pages/<slug>"`).

- **Partenaire** : [[ppl.partner_name]] (`[[ppl.partner_id]]`)
- **Domaine Principal** : `[[ppl.main_domain]]` (`websiteId: [[ppl.website_id]]`)
- **Conteneur GTM injecté** : `[[ppl.gtm_id]]`

## 2. Fonctionnement (`upload-page` vs `reload-page`)
1. **`POST /api/objects/upload-page`** : Scrape le HTML de `originalUrl`, nettoie les scripts Leadpages, rapatrie et redimensionne les images `<img>` sur S3 (`<key>_assets/img/`), et enregistre l'objet `PAGE` (`subtype: "PAGE:OTHER"` par défaut).
2. **`GET /api/objects/{objectId}/reload-page`** : Re-fetche uniquement le HTML brut depuis `originalUrl` **sans** rapatrier les images `<img>`.

## 3. Garde-Fous Obligatoires
- **`originalUrl` ASCII & HTTP 200** : L'URL source ne doit contenir aucun caractère accentué et ne doit pas faire de redirection `302`.
- **Images de fond CSS** : Seules les balises `<img>` sont rapatriées ; les `background-image: url(...)` relatives ne sont pas réécrites.
- **Protection des PDF** : Toujours vérifier le type MIME avant un `reload-page` pour ne jamais écraser un PDF par du HTML.
- Consulter [`guide.md`](./guide.md), [`specificites.md`](./specificites.md) et [`erreurs-connues.md`](./erreurs-connues.md).
