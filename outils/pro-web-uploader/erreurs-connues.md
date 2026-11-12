# Erreurs Connues — Pro Web Uploader (Socle Pro-Pilot)

- **400 Bad Request sur `POST /objects/signed-url` ("Invalid request body")** :
  - **Symptôme** : L'API renvoie `400 {"message": "Invalid request body"}` si le corps JSON ne contient que `websiteId`, `key` et `contentType`.
  - **Solution** : Ajouter impérativement `"partnerId": ${PARTNER_ID}` (numérique, ex. `4` pour VivaSanté, `2` pour Biosanté) dans le payload JSON de `POST /objects/signed-url`. Inclure également `"partnerId": ${PARTNER_ID}` dans `POST /objects/upsert` par cohérence.
- **Effet de bord d'un upsert manuel sur `leadpageEditUrl`** :
  - **Symptôme** : Après un appel `POST /objects/upsert`, le champ `leadpageEditUrl` de l'objet passe à `null`.
  - **Conséquence** : Une page retouchée ou téléversée manuellement sur Pro Web S3 ne doit pas être écrasée ou réimportée depuis une source externe sans confirmation humaine explicite.
- **Header `x-amz-acl` interdit lors du PUT S3** :
  - Lors du `PUT` sur l'URL S3 présignée (`signed-url`), n'envoyer que le header `Content-Type` (ne jamais ajouter `x-amz-acl` en header → `403 AccessDenied`).
- **Scripts Pro Web obligatoires** :
  - Ne jamais omettre `<script src="https://cdn.info-contenu.io/assets/headerTools.js" type="text/javascript"></script>` ni `<script src="https://cdn.info-contenu.io/assets/preserveParamsV2.js" type="text/javascript"></script>` sur une Landing Page pointant vers un bon de commande (sinon perte des paramètres `utm_*`, `leadcode`, `salescode`, `bdc`).
- **Préservation des conteneurs existants** :
  - Ne jamais supprimer le conteneur GTM ni `leadBox-v1.0.0.js` lors de la modification d'une page existante.
- **Contrôle HTTP post-publication** :
  - Toujours vérifier `curl -sI "<urlPublic>"` (`HTTP/2 200`) après `POST /objects/upsert`.
