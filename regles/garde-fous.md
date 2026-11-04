# Garde-fous de Sécurité & Préservation de la Production

## 1. Validation Humaine Obligatoire avant toute Écriture S3 / API
- Toute action qui crée, modifie ou supprime un objet en production (`POST /objects/signed-url` + `PUT <signedUrl>`, `POST /objects/upsert`, `POST /objects/upload-page`, `POST /objects/{objectId}/reload-page`, `DELETE /objects`) exige :
  1. Un contrôle préalable via `GET /objects/list/{websiteId}` pour vérifier si la `key` existe déjà (et, en cas de mise à jour, une sauvegarde locale de la version en ligne dans `backups/`).
  2. La validation locale de l'aperçu par l'utilisateur (ou la vérification `curl -sI` de l'`originalUrl` pour un import).
  3. **L'accord explicite de l'utilisateur dans le chat** en précisant le domaine cible, le `websiteId` correspondant et la `key` exacte avant d'exécuter les requêtes HTTP d'écriture.

## 2. Protection des Conteneurs Critiques (Formulaires, Tracking & `headerTools.js`)
- Lors de la modification d'une page existante, il est **strictement interdit** de supprimer ou d'altérer :
  - Le script `<script src="https://scripts.propulse-lab.com/headerTools.js" defer></script>` (indispensable à la transmission des paramètres vers le bon de commande),
  - Les formulaires d'inscription (`<form>`), leurs champs cachés (`<input type="hidden">`) et leurs attributs `action` / `method`,
  - Les scripts Google Tag Manager (`GTM-XXXXXXX`) et le pied de page légal (Mentions légales, CGV, Politique de confidentialité).

## 3. Sécurité des Secrets & du Socle `.pro-pilot/`
- Ne jamais committer ni afficher en clair le fichier `.env` ou la clé `PRO_WEB_API_KEY`.
- Ne jamais modifier ni écrire de fichier dans le dossier `.pro-pilot/` (le profil utilisateur local est stocké dans `./.pro-pilot-profile.md` à la racine du dépôt partenaire).
