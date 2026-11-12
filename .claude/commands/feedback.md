# Commande /feedback — Enregistrement et Synchronisation des Retours Partenaires

Cette commande permet a Claude d'enregistrer de facon autonome les retours d'experience, les corrections, les nouvelles fiches produits et les regles edifiees au cours des sessions, et de les synchroniser sur le depot GitHub du partenaire sans aucune manipulation technique de la part de l'utilisateur.

---

## 1. Declencheurs

Cette commande est executee :
- Soit a la demande explicite de l'utilisateur via `/feedback <description du retour>`
- Soit de maniere proactive par Claude des qu'un utilisateur formule une correction, une regle specifique, un retour sur un style ou une nouvelle mention legale.

---

## 2. Matrice d'Aiguillage des Retours

Selon la nature du retour, Claude met a jour le fichier correspondant :

| Nature du retour | Fichier cible | Format de mise a jour |
|---|---|---|
| **Regle editoriale / mise en page** | `outils/pro-web-uploader/specificites.md` | Ajouter une section `### [Titre de la regle]` avec le contexte et la consigne |
| **Erreur technique / piege API** | `outils/pro-web-uploader/erreurs-connues.md` | Ajouter une entree `### [Symptome]` + `Solution appliquee` |
| **Charte / couleur / typographie** | `donnees-business/design-system.md` | Mettre a jour la palette ou la typographie dans la section correspondante |
| **Nouveau produit / offre** | `donnees-business/<sku>/fiche-produit.md` | Creer ou completer la fiche produit standardisee |
| **Nouveau domaine / websiteId** | `outils/pro-web-uploader/variables.md` | Ajouter la ligne dans le tableau des sites |

---

## 3. Garde-fous de Securite & Perimetre Autorise

Pour proteger l'integrite du harnais :
1. **Perimetre autorise (Allowlist)** :
   - Uniquement les fichiers sous `donnees-business/**` et `outils/**/`.
2. **Perimetre strictement interdit (Denylist)** :
   - Ne jamais modifier ni committer de scripts `.sh`, `.py`, `.js`.
   - Ne jamais modifier `.github/**`, `regles/**`, `ROUTER.md`, `.claude/commands/`.
   - Ne jamais committer de pages `*.html`, `*.htm`, `.tmp/`, `tmp/` ni de fichiers `.env`.

---

## 4. Execution Silencieuse du Commit et Push

Claude execute directement la sequence sans demander a l'utilisateur de taper dans le terminal :

```bash
# 1. Recuperation des dernieres modifications distantes
git pull --rebase origin main

# 2. Indexation exclusive des fichiers documentaires modifies
git add donnees-business/ outils/

# 3. Commit documentaire structure
git commit -m "docs(partenaire): mise a jour des connaissances métier [sujet]"

# 4. Push distant
git push origin main
```

---

## 5. Confirmation Utilisateur

Une fois le push effectue, Claude confirme sobrement a l'utilisateur :
*« Votre preference sur [sujet] a ete enregistree dans [fichier] et synchronisee sur votre depot GitHub partagé. Elle sera automatiquement prise en compte lors de nos prochaines sessions. »*
