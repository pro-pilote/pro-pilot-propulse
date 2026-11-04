# Garde-Fous d'Exécution & Sécurité de Publication

## 1. Aucune mise en production sans validation humaine
- Toute action qui modifie un site en ligne (`./ppl static push <domaine> --go`) exige :
  1. Un aperçu local préalable validé par le partenaire,
  2. Une confirmation physique explicite de l'utilisateur dans son terminal.
- L'assistant IA ne doit jamais tenter de contourner cette confirmation.

## 2. Protection des identifiants et secrets
- Ne jamais écrire de mot de passe, clé d'API ou token personnel dans un fichier du dépôt Git ou dans un ticket de feedback.
- Les accès locaux sont stockés uniquement dans la configuration locale de l'ordinateur de l'utilisateur.

## 3. Respect des scripts `/pro-tools`
- Ne jamais modifier le code des scripts situés dans `tools/`. Utilise uniquement les commandes documentées dans `outils/`.
