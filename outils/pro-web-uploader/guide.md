# Guide Pas à Pas — Pro Web Uploader

Ce guide détaille les étapes de déploiement et d'invalidation de cache :

1. **Rapatriement initial** : `python3 tools/ppl.py static pull <domaine>` crée le miroir local dans `sites/<domaine>/`.
2. **Prévisualisation locale** : `python3 tools/ppl.py static preview <domaine>` lance un serveur HTTP local sur le port 8080.
3. **Contrôle pré-vol (Dry-Run)** : `python3 tools/ppl.py static push <domaine>` calcule le diff exact entre local et S3.
4. **Déploiement en production** : `python3 tools/ppl.py static push <domaine> --go` exige la confirmation exacte "OUI" et téléverse les fichiers modifiés vers S3 puis MongoDB.
5. **Restauration de sécurité** : En cas d'anomalie, ré-exécuter `push` depuis le snapshot automatique `backups/<domaine>-<timestamp>/`.
