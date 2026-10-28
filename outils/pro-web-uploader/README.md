# Guide Propulse Lab — Pro Web Uploader ([[ppl.partner_name]])

## 1. Objectif
Télécharger une page statique de **[[ppl.partner_name]]**, la prévisualiser en local sur l'ordinateur et publier les mises à jour sur `[[ppl.main_domain]]` en toute sécurité.

## 2. Commandes `/pro-tools` (`tools/ppl.py static`)

```bash
# 1. Rapatrier le site statique depuis Pro Web
python3 tools/ppl.py static pull [[ppl.main_domain]]

# 2. Lancer le serveur d'aperçu local (http://127.0.0.1:8080)
python3 tools/ppl.py static preview [[ppl.main_domain]]

# 3. Simuler le déploiement (Dry-Run sans modification en ligne)
python3 tools/ppl.py static push [[ppl.main_domain]]

# 4. Publier en production (exige la confirmation humaine dans le terminal)
python3 tools/ppl.py static push [[ppl.main_domain]] --go
```

## 3. Points de Vigilance
- Consulter systématiquement [`specificites.md`](./specificites.md) et [`erreurs-connues.md`](./erreurs-connues.md) avant de publier.
- **Double arborescence HTML** : si le dépôt contient à la fois `page.html` et `page/index.html`, le script signale le doublon afin de mettre à jour le bon fichier.
