# Protocole d'Onboarding Partenaire (Premier Lancement)

## Instructions pour l'Assistant IA

Si le fichier local `.pro-pilot/profile.md` n'existe pas encore sur l'ordinateur de l'utilisateur (ou contient des champs `À_REMPLIR`), tu DOIS :
1. **Vérifier et installer silencieusement l'environnement Python local** avant que l'utilisateur n'ait à le faire lui-même :
   - Si `./tools/ppl` (macOS/Linux) ou `.\tools\ppl.cmd` (Windows) est présent, exécute-le (`./tools/ppl doctor`) : il télécharge automatiquement un Python 3.12 portable isolé (`.venv/`) et installe `tools/requirements.txt` si Python est absent du poste.
   - Sinon, vérifie `python3 -c "import sys"` (ou `py -3 -c "import sys"` sous Windows). S'il est absent, installe-le automatiquement (`winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements` sous Windows, `brew install python || xcode-select --install` sous macOS), puis installe `tools/requirements.txt`.
2. **Conduire cet entretien d'onboarding** avant toute autre tâche.

Pose les questions suivantes de manière claire, chaleureuse et concise :

### Question 1 — Identité & Organisation
- Qui es-tu (prénom/rôle) et pour quel partenaire / Business Unit travailles-tu ?
- Quel est le nom de ton dépôt partenaire (ex. `pro-pilot-pan`, `pro-pilot-aps`) ?

### Question 2 — Périmètre d'activité
Que vas-tu avoir besoin de faire principalement ?
- **Option A — Édito & Contenu** : création/modification de pages éditoriales, articles, pages produits, mise en forme de contenus.
- **Option B — Acquisition & Conversion** : création de landing pages (LP), pages d'inscription webinaire, pages de vente / bons de commande (BDC), suivi des performances.
- **Option C — Actions ciblées** : uniquement certaines opérations précises au quotidien.

### Question 3 — Confirmation des actions à disposition
En fonction de la réponse à la Question 2, présente à l'utilisateur la liste concrète des outils et actions qu'il aura à disposition :
- **Pro Web Page Creator** : créer ou adapter une page web (LP, page webinaire, page statique) à partir d'un brief ou d'un Google Doc.
- **Pro Web Uploader** : prévisualiser une page en local (`127.0.0.1`) et la publier sur Pro Web.
- **Pro Webinaire** : intégrer un formulaire d'inscription ou configurer une salle de webinaire.
- **Pro Acquisition** : préparer et vérifier un bon de commande (BDC) ou un formulaire d'opt-in.
- **Salesforce / Bi-Brother / ClickUp** : consulter les indicateurs, vérifier le CRM ou créer un ticket de suivi.

**Attends la confirmation explicite de l'utilisateur** sur cette liste d'actions avant de passer à la suite.

### Question 4 — Niveau technique
Demande à l'utilisateur comment il souhaite que tu communiques avec lui :
- **Niveau 1 — Métier / Non-technique** : tu t'occupes de toute la technique en coulisses sans jamais afficher de jargon (HTML, DOM, CLI, Git) ; tu parles uniquement de rendu visuel, de texte et d'aperçu navigateur.
- **Niveau 2 — Hybride / Intermédiaire** : explications synthétiques avec aperçu des commandes principales.
- **Niveau 3 — Technique / Avancé** : détails complets sur le code, les sélecteurs CSS/HTML et les scripts exécutés.

---

## Enregistrement de la Fiche Mémoire Locale

Dès que l'utilisateur a validé ses réponses, crée le fichier `.pro-pilot/profile.md` sur son ordinateur en remplissant le modèle [`profile.template.md`](./profile.template.md). Confirme-lui en une phrase que sa mémoire locale est prête.
