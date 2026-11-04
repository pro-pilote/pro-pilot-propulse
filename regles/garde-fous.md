# Garde-Fous d'Exécution & Sécurité de Publication

## 1. Aucune mise en production sans validation humaine
- Toute action qui publie ou modifie un objet en ligne sur l'API Pro Web (`POST /objects/upsert`, `POST /objects/upload-page`, `POST /objects/{id}/reload-page`, `DELETE /objects`) exige :
  1. Une prévisualisation locale préalable validée par le partenaire (pour toute création/modification HTML),
  2. Un accord explicite de l'utilisateur dans le chat avant d'exécuter l'appel API de publication.

## 2. Protection des identifiants et secrets
- Ne jamais écrire la clé `PRO_WEB_API_KEY` dans un fichier suivi par Git ou dans une Issue GitHub.
- La clé `PRO_WEB_API_KEY` reste exclusivement dans le fichier `.env` local (ignoré par `.gitignore`).

## 3. Cloisonnement du socle `.pro-pilot/`
- Ne jamais modifier les fichiers situés dans `.pro-pilot/`. Pour proposer une amélioration ou signaler une erreur, ouvrir une Issue GitHub conformément à `regles/amelioration-continue-letta.md`.
