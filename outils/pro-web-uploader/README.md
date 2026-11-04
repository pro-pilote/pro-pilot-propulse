# Guide Propulse Lab — Pro Web Uploader ([[ppl.partner_name]])

## 1. Objectif
Créer, prévisualiser en local et publier **un objet** (`PAGE` HTML ou `DOCUMENT` PDF/image) de **[[ppl.partner_name]]** sur `[[ppl.main_domain]]` en toute sécurité via le flow `signed-url` $\rightarrow$ `PUT S3` $\rightarrow$ `upsert`.

## 2. Commandes d'Exécution (`./ppl static`)

```bash
# 1. Lister ou rapatrier les objets Pro Web du site
./ppl static ls [[ppl.main_domain]]
./ppl static pull [[ppl.main_domain]]

# 2. Prévisualiser l'objet en local (http://127.0.0.1:8080)
./ppl static preview [[ppl.main_domain]]

# 3. Simuler la publication d'un objet (Dry-Run sans modification en ligne)
./ppl static push [[ppl.main_domain]]
./ppl static add [[ppl.main_domain]] fichier.html --key pages/mon-slug

# 4. Publier l'objet en production (exige la confirmation humaine "OUI" dans le terminal)
./ppl static push [[ppl.main_domain]] --go
./ppl static add [[ppl.main_domain]] fichier.html --key pages/mon-slug --go
```

## 3. Points de Vigilance
- Lors de la création ou modification d'une page HTML, consulter `donnees-business/<sku>/fiche-produit.md` et `donnees-business/design-system.md`.
- Consulter systématiquement [`specificites.md`](./specificites.md) et [`erreurs-connues.md`](./erreurs-connues.md) avant de publier.
- **Double arborescence HTML** : si le dépôt contient à la fois `page.html` et `page/index.html`, le script signale le doublon afin de mettre à jour les deux objets.
