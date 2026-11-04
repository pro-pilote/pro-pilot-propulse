# Checklist Pré-Livraison (Contrôle Qualité Obligatoire)

Avant de présenter une page ou un livrable au partenaire, vérifie systématiquement ces 6 points :

1. **Conformité au Design System** : les couleurs, polices et styles de boutons correspondent exactement à `donnees-business/<sku>/design-system.md`.
2. **Exactitude de l'Offre** : les titres, promesses, prix et mentions légales correspondent au brief et à `fiche-produit.md`.
3. **Intégrité des Zones Protégées (Scripts & Formulaires)** :
   - Les conteneurs de formulaires (inscription webinaire, opt-in, paiement BDC) n'ont **jamais** été réécrits ou simplifiés à la main : seuls les snippets officiels de `outils/` sont utilisés.
   - Le script GTM et les scripts d'en-tête (`variables.md`) sont présents et intacts.
4. **Absence d'Erreurs Connues** : relis `outils/<outil>/erreurs-connues.md` du partenaire et vérifie qu'aucun des pièges listés n'est présent dans ton code.
5. **Rendu Mobile-First (Responsive)** : pas de débordement horizontal, textes lisibles sur mobile, bouton d'action (CTA) et formulaire accessibles dès le premier écran lorsque requis.
6. **Aperçu Local (`ppl preview`)** : lance toujours le serveur d'aperçu local (`http://127.0.0.1`) pour vérifier visuellement la page avant toute proposition de mise en ligne.
