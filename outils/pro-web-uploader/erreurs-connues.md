# Erreurs Connues — Pro Web Uploader (Socle Pro-Pilot)

- **Suppression d'objets non autorisée en v1 (Sécurité)** :
  - **Symptôme** : L'appel `DELETE /objects/{objectId}` échoue avec `403 Missing Authentication Token` (aucune route DELETE n'est exposée sur l'API publique).
  - **Règle de sécurité** : Par mesure de sécurité, aucune route DELETE n'est ouverte sur l'API publique en v1. L'assistant IA n'exécute aucune suppression. Toute suppression définitive doit être réalisée manuellement par un opérateur humain depuis l'interface web Pro Web.
- **Sur les sites `STATIC`, les URL avec slash de dossier `/<slug>/` renvoient `500` (pas d'index automatique)** :
  - **Symptôme** : Une page publiée avec la `key` `<slug>/index.html` répond `200` sur `https://<domaine>/<slug>/index.html`, mais renvoie une erreur `500` sur `https://<domaine>/<slug>/` et `https://<domaine>/<slug>`. Pro Web ne réalise aucune réécriture automatique de dossier vers `index.html` (seule la racine `/` sert `index.html`).
  - **Solution appliquée** : Pour toute URL propre sans extension, utiliser une `key` sans extension ni slash final (ex. `articles/<slug>` ou `<slug>`), servie en `text/html`. Aligner tous les liens internes, le tag `canonical` et le `sitemap.xml` sur cette URL exacte. Toujours contrôler l'URL réelle `curl -sI "https://<domaine>/<key>"` sans slash final.

- **400 Bad Request sur `POST /objects/signed-url` ("Invalid request body")** :
  - **Symptôme** : L'API renvoie `400 {"message": "Invalid request body"}` si le corps JSON ne contient que `websiteId`, `key` et `contentType`.
  - **Solution** : Ajouter impérativement `"partnerId": ${PARTNER_ID}` (numérique, ex. `4` pour VivaSanté, `2` pour Biosanté, `12` pour Panthéon) dans le payload JSON de `POST /objects/signed-url`. Inclure également `"partnerId": ${PARTNER_ID}` dans `POST /objects/upsert` par cohérence.
- **Effet de bord d'un upsert manuel sur `leadpageEditUrl`** :
  - **Symptôme** : Après un appel `POST /objects/upsert`, le champ `leadpageEditUrl` de l'objet passe à `null`.
  - **Conséquence** : Une page retouchée ou téléversée manuellement sur Pro Web S3 ne doit pas être écrasée ou réimportée depuis une source externe sans confirmation humaine explicite.
- **Absence de route `DELETE /objects/{objectId}` (retour 403 `Missing Authentication Token`)** :
  - **Symptôme** : L'appel de suppression `DELETE /objects/{objectId}` échoue avec `403 Missing Authentication Token` car aucune route `DELETE` n'est configurée sur la passerelle AWS API Gateway publique.
  - **Solution appliquée** : Supprimer l'objet directement depuis l'interface web Pro Web (UI), ou, à défaut, écraser l'objet (`signed-url` $\rightarrow$ `PUT` $\rightarrow$ `upsert` sur la même `key`) par une page de redirection minimale (`meta refresh` + `window.location.replace` vers l'URL cible, balise `meta name="robots" content="noindex"`, `canonical`). Sauvegarder impérativement la version en ligne dans `backups/` avant toute modification.
- **Sur les sites `STATIC`, les URL avec slash de dossier `/<slug>/` renvoient `500`** :
  - **Symptôme** : Une page publiée avec la `key` `<slug>/index.html` répond `200` sur `https://<domaine>/<slug>/index.html`, mais renvoie une erreur `500 Internal Server Error` sur `https://<domaine>/<slug>/` et `https://<domaine>/<slug>`. Pro Web ne réalise aucune réécriture automatique de dossier vers `index.html` (seule la racine `/` sert `index.html`).
  - **Solution appliquée** : Pour toute URL propre sans extension, utiliser une `key` sans slash final (ex. `articles/<slug>` ou `<slug>`), servie en `text/html`. Aligner tous les liens internes, le tag `canonical` et le `sitemap.xml` sur cette URL exacte. Toujours contrôler l'URL réelle `curl -sI "https://<domaine>/<key>"` sans slash final.
- **Header `x-amz-acl` interdit lors du PUT S3** :
  - Lors du `PUT` sur l'URL S3 présignée (`signed-url`), n'envoyer que le header `Content-Type` (ne jamais ajouter `x-amz-acl` en header → `403 AccessDenied`).
- **Scripts Pro Web obligatoires** :
  - Ne jamais omettre `<script src="https://cdn.info-contenu.io/assets/headerTools.js" type="text/javascript"></script>` ni `<script src="https://cdn.info-contenu.io/assets/preserveParamsV2.js" type="text/javascript"></script>` sur une Landing Page pointant vers un bon de commande (sinon perte des paramètres `utm_*`, `leadcode`, `salescode`, `bdc`).
- **Préservation des conteneurs existants** :
  - Ne jamais supprimer le conteneur GTM ni `leadBox-v1.0.0.js` lors de la modification d'une page existante.
- **Contrôle HTTP post-publication** :
  - Toujours vérifier `curl -sI "<urlPublic>"` (`HTTP/2 200`) après `POST /objects/upsert`.
