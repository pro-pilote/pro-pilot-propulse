# Getting Started — Starter Pack Pro-Pilot

Bienvenue dans **Pro-Pilot**. Ce dossier permet à votre assistant IA (Claude Desktop, Claude Code, Cursor, Codex, Antigravity, Grok, ChatGPT) de connaître votre métier, vos produits et d'exécuter vos actions en toute sécurité.

## Étape 0 — Prérequis Techniques (Automatique — 1 seule fois)

Les outils d'exécution locale nécessitent **Python 3.9+** et la librairie `requests` (voir [`prerequis.md`](./prerequis.md)).
- **Avec le lanceur racine** (synchronise automatiquement le socle dans `.pro-pilot/` au premier appel) :
  - **macOS / Linux** : `./ppl doctor`
  - **Windows** : `ppl.cmd doctor`
- **Installation rapide de `requests` si manquant** :
  - **macOS / Linux** : `python3 -m pip install -r .pro-pilot/tools/requirements.txt`
  - **Windows** : `py -3 -m pip install -r .pro-pilot\tools\requirements.txt`

## Étape 1 — Premier lancement (Onboarding)

Lors de votre toute première session, votre IA vous pose **4 questions rapides** :
1. **Qui êtes-vous ?** (Votre organisation / marque et votre rôle)
2. **Quel est votre périmètre au quotidien ?** (Édito, Acquisition, ou actions ciblées)
3. **Confirmation de vos actions :** l'IA vous propose la liste des actions correspondant à votre besoin et vous demande de la confirmer.
4. **Votre niveau technique :** pour adapter son vocabulaire (zéro jargon technique si vous préférez une approche 100 % métier).

Vos réponses sont enregistrées uniquement sur votre ordinateur dans `.pro-pilot/profile.md`.

## Étape 2 — Utilisation au quotidien

Exprimez simplement votre demande en langage naturel et glissez vos pièces jointes (Google Docs, PDF, brief) :
- *« Crée une page HTML de présentation à partir de ce document et publie cet objet sur Pro Web. »*
- *« Importe cette URL Leadpages sur notre site Pro Web. »*

Votre IA consulte automatiquement le routeur [`ROUTER.md`](../ROUTER.md), charge les fiches de votre dépôt partenaire et exécute les outils nécessaires.
