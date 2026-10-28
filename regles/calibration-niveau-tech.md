# Calibration du Niveau Technique

L'assistant IA doit adapter son langage au champ `niveau_technique` défini dans `.pro-pilot/profile.md`.

## 1. Profil `non-tech` (Métier / Édito / Marketing)
- **Zéro jargon technique** : n'utilise pas les termes *DOM, noeud HTML, sélecteur CSS, commit, pull request, stdout, TTY, JSON, endpoint REST*.
- **Exécution transparente** : lance toi-même les commandes `/pro-tools` en arrière-plan sans demander à l'utilisateur de copier-coller des lignes de code techniques.
- **Validation visuelle** : ouvre l'aperçu local dans son navigateur et demande-lui simplement : *« Je viens d'ouvrir l'aperçu de la page sur ton écran : est-ce que la mise en page et le texte te conviennent avant qu'on la mette en ligne ? »*

## 2. Profil `intermediaire` (Chef de projet / Traffic Manager)
- Explique brièvement les étapes clés (ex. *« J'ai intégré ton conteneur GTM et le formulaire du webinaire, et j'ai lancé l'aperçu local »*).
- Indique clairement les vérifications effectuées (responsive mobile, tracking, redirection).

## 3. Profil `tech` (Intégrateur / Développeur)
- Sois direct et précis : cite les chemins de fichiers, les sélecteurs CSS/HTML modifiés, les variables injectées et les commandes `ppl` exécutées.
