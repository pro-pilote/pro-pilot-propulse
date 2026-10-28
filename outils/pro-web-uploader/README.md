# Outil : Pro Web Uploader (Sites Statiques & Publication Pro Web)

## 1. Objectif
Télécharger une page statique existante, la prévisualiser en local sur l'ordinateur du partenaire et publier les mises à jour sur Pro Web en toute sécurité.

## 2. Commandes `/pro-tools` (`tools/ppl.py static`)

```bash
# 1. Rapatrier le site statique depuis Pro Web
python3 tools/ppl.py static pull <domaine>

# 2. Lancer le serveur d'aperçu local (http://127.0.0.1:8080)
python3 tools/ppl.py static preview <domaine>

# 3. Simuler le déploiement (Dry-Run sans modification en ligne)
python3 tools/ppl.py static push <domaine>

# 4. Publier en production (exige la confirmation humaine dans le terminal)
python3 tools/ppl.py static push <domaine> --go
```

## 3. Points de Vigilance
- **Double arborescence HTML** : si le dépôt contient à la fois `page.html` et `page/index.html`, le script signale le doublon afin de mettre à jour le bon fichier.
- **Encodage** : les fins de ligne sont automatiquement normalisées en `LF` (UTF-8) avant envoi.
