# Règle Anti-Collision & Sauvegarde avant Publication

Avant toute modification d'une page existante (site statique Pro Web, BDC Pro Funnel ou page WordPress) :

1. **Récupération de la dernière version en ligne (`pull`)** : toujours rapatrier la version actuellement en production avant d'appliquer des modifications, afin de ne jamais écraser le travail d'un collègue intervenu entre-temps.
2. **Vérification de double arborescence (Sites Statiques)** : sur Pro Web, vérifier s'il existe à la fois `<slug>.html` et `<slug>/index.html` pour modifier le fichier réellement servi aux visiteurs.
3. **Sauvegarde locale automatique** : conserver une copie de sauvegarde locale avant tout envoi en production.
