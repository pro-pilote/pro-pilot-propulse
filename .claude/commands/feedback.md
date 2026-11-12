# Commande /feedback — Enregistrement des Retours Partenaires (Mode Append-Only)

Cette commande permet a Claude ou au partenaire d'enregistrer de facon autonome les retours d'experience, les regles de charte, les nouvelles formules ou les mentions legales dans la boite de reception partagee de l'equipe (`donnees-business/_inbox/`) sans aucun risque d'ecraser les fichiers existants.

---

## 1. Declencheurs

Cette commande est executee :
- Soit a la demande explicite de l'utilisateur via `/feedback <sujet>`
- Soit de maniere proactive et silencieuse par Claude des qu'un utilisateur formule une correction, une preference de charte ou une regle perenne.

---

## 2. Execution

```bash
python3 outils/feedback_push.py "<sujet>" "<contenu_ou_chemin_de_fichier>" "[categorie: design|editorial|technique|produit]"
```

Exemples :
```bash
python3 outils/feedback_push.py "Couleur bouton principal" "Toujours utiliser le vert #2D6A4F pour les boutons d'appel a l'action." "design"
python3 outils/feedback_push.py "Mention legale complements" "donnees-business/mentions-legales.md" "editorial"
```

Le script contacte directement l'API securisee du portail Pro-Pilot qui consigne la note dans `donnees-business/_inbox/` du depot GitHub officiel sans aucune manipulation Git locale.

---

## 3. Confirmation Utilisateur

En fin de reponse, Claude ajoute une simple mention informative :
*« Page mise a jour. J'ai egalement consigne la regle [sujet] dans la boite de reception partagee de votre equipe. »*
