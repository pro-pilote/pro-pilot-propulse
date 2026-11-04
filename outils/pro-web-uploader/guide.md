# Guide Pas à Pas — Pro Web Uploader (Objets PAGE & DOCUMENT)

`pro-web-uploader` permet de **créer, prévisualiser en local et publier un objet** (`PAGE` HTML ou `DOCUMENT` PDF/image) sur Pro Web via le flow `signed-url` $\rightarrow$ `PUT S3` $\rightarrow$ `upsert` (avec invalidation CloudFront automatique).

## 1. Création ou Modification d'un Objet HTML (LP, page de capture)
1. **Données & Charte** : Lire `donnees-business/<sku>/fiche-produit.md` et `donnees-business/design-system.md`.
2. **Garde-fous HTML** : Fournir le fichier HTML complet (`<!DOCTYPE html>` à `</html>`), conserver `<!-- PPL:FORM -->` et `<!-- PPL:GTM -->`.
3. **Périmètre des clés (`key`)** :
   - Sur un site non-STATIC (`WORDPRESS`, etc.), seuls les objets sous `pages/<slug>`, `leads/<slug>` et `cadeau/<slug>` sont autorisés.
   - Sur un site `STATIC`, tous les chemins d'objets sont autorisés (hors vidéos, max 20 Mo).

## 2. Commandes d'Exécution (`./ppl static`)
1. **Lister les objets d'un site** : `./ppl static ls <domaine>` (`GET /objects/list/{websiteId}`).
2. **Rapatrier les objets en local** : `./ppl static pull <domaine>` crée le miroir dans `sites/<domaine>/`.
3. **Prévisualiser en local** : `./ppl static preview <domaine>` lance un serveur HTTP local sur `http://127.0.0.1:8080`.
4. **Contrôle pré-vol (Dry-Run)** : `./ppl static push <domaine>` (ou `./ppl static add <domaine> <fichier> --key pages/<slug>`) affiche les objets à publier sans modifier la production.
5. **Publier l'objet en production** : `./ppl static push <domaine> --go` (ou `add ... --go`) exige la confirmation interactive `"OUI"`, pousse sur S3 (`signed-url` + `PUT` avec `Content-Type` seul) et met à jour MongoDB (`upsert`) en invalidant le cache CloudFront.
