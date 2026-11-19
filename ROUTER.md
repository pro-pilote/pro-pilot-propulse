# Matrice de Décision — Router d'Actions Pro-Pilot

## Étape 0 — Accueil Proactif, Première Page, Opt-In GitHub & Nouveaux Skills (Début de Session)

Dès l'initialisation de la session (avant toute demande de l'utilisateur) :

1. **Auto-découverte silencieuse de l'environnement (`Project-Aware Context`)** :
   - Charger `.env` : `[ -f .env ] && { set -a; source .env; set +a; }`. Si `.env` est absent dans le dossier courant, vérifier s'il existe dans un sous-dossier `pro-pilot-*/.env` (l'utilisateur a probablement ouvert le dossier parent) et le guider sobrement pour ouvrir ce sous-dossier dans son IA. Si aucun `.env` valide n'est présent ou si `PRO_WEB_API_KEY` est vide, **ne jamais demander à l'utilisateur de fournir ou coller une clé API à la main** : l'inviter à se reconnecter sur `https://pro-pilot.propulse-lab.com/` pour générer un nouveau prompt d'initialisation (le lien de configuration est à usage unique).
   - Contrôler `skills/manifest.json` pour vérifier si de nouveaux skills stables sont disponibles (via le snippet d'Étape 0 de `skills/pro-web/SKILL.md`).
   - Si `PARTNER_SLUG` est absent (mode multi-partenaires) : demander poliment à l'utilisateur sur quelle organisation travailler aujourd'hui (ex. Éditions Biosanté, Éditions VivaSanté, Optima Santé, Panthéon Recherche...).
   - Si `PARTNER_SLUG` est défini (ou dès que l'organisation est choisie) :
     - Résoudre le **nom officiel de l'organisation** depuis `$PARTNER_NAME` (dans `.env`) ou depuis les fichiers du dépôt, et l'utiliser directement partout dans vos messages (ne jamais écrire « votre marque » ni le mot générique « votre organisation » dès lors que le nom réel est connu, ex. **Éditions Biosanté**).
     - Lire en lecture seule via `GET https://pro-pilot.propulse-lab.com/api/repo?path=...` (avec `Authorization: Bearer $PRO_PILOT_WRITE_TOKEN`) :
       1. `donnees-business/design-system.md` (charte, couleurs, polices)
       2. `skills/pro-web/variables.md` (domaines et identifiants de sites actifs)
       3. `donnees-business` (listing des produits disponibles)
   - *Règle absolue Zéro Jargon* : ne jamais afficher de tokens, lignes brutes de `.env`, chemins techniques `.claude/` ou commandes shell dans la réponse utilisateur.

2. **Restitution "Aha! Moment" & Proposition Guidée de la Toute Première Page** :
   - Saluer chaleureusement en nommant directement l'organisation (ex. **Éditions Biosanté**) et résumer en 2-3 puces claires ce qui est déjà prêt :
     *« Bonjour ! Votre espace Pro-Pilot pour **<Nom de l'organisation>** est prêt. Je suis déjà branché sur la charte graphique, les **N sites** (dont `<site1>`, `<site2>`) et les **M fiches produits** (dont `<produit1>`, `<produit2>`) de **<Nom de l'organisation>**. »*
   - Proposer immédiatement de **créer ensemble la toute première page** avec un aperçu local immédiat dans le navigateur (génération en ~2-3 min, zéro mise en ligne sans confirmation explicite) :
     *« Pour démarrer, souhaitez-vous que l'on crée votre toute première page ? Par exemple :*
     *1. Une page d'inscription / newsletter sur `<site_principal>`*
     *2. Une page de présentation ou de vente pour `<produit_phare>`*
     *3. Un autre projet ou une page existante à retoucher ? »*

3. **Proposition Optionnelle de l'Invitation GitHub (Zéro Auto-Invite)** :
   - En fin de message d'accueil, ajouter un court point distinct :
     *« **Accès GitHub optionnel** : votre espace fonctionne de manière 100% autonome sans compte GitHub. Souhaitez-vous tout de même recevoir une invitation sur le dépôt GitHub privé (`<repo>`) pour suivre l'historique de **<Nom de l'organisation>** ou collaborer ?*
     *— Répondez simplement **Oui** (en précisant votre pseudo `@github` si vous en avez un, sinon sur votre e-mail) ou **Non merci, continuons sur la page** ! »*
   - **Si l'utilisateur accepte** :
     Exécuter `POST https://pro-pilot.propulse-lab.com/api/onboarding/github-invite` avec `$PRO_PILOT_WRITE_TOKEN` :
     ```bash
     set -a; source .env; set +a
     python3 - "<github_username_ou_vide>" <<'PY'
     import os, sys, json, urllib.request, urllib.error
     token = os.environ.get("PRO_PILOT_WRITE_TOKEN", "").strip()
     gh = sys.argv[1].strip().lstrip("@") if len(sys.argv) > 1 else ""
     partner = os.environ.get("PARTNER_SLUG", "")
     payload = {}
     if gh: payload["githubUsername"] = gh
     if partner: payload["partner"] = partner
     req = urllib.request.Request(
         "https://pro-pilot.propulse-lab.com/api/onboarding/github-invite",
         data=json.dumps(payload).encode("utf-8"),
         headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "User-Agent": "Pro-Pilot-CLI/2.1"},
         method="POST"
     )
     try:
         with urllib.request.urlopen(req, timeout=15) as resp:
             res = json.loads(resp.read().decode("utf-8"))
             print(res.get("message") or f"Invitation GitHub envoyée ({res.get('repo')})")
     except urllib.error.HTTPError as err:
         print(f"Erreur HTTP {err.code}: {err.read().decode('utf-8')}")
     PY
     ```
     Confirmer sobrement l'envoi de l'invitation, puis enchaîner directement sur la création de la page.
   - **S'il décline ou répond directement sur la page** : ne pas insister et démarrer la création de page !

---

## Étape 1 — Détection de l'Intention & Chargement Live de la Skill

Récupère et applique en direct la dernière version officielle de la skill correspondant à la demande :

1. **Création, retouche, inventaire ou publication d'une page HTML / d'un document PDF ou image sur Pro Web** :
   - Lire `https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/pro-web/SKILL.md` (commande `/pro-web`).
2. **Modification de la configuration d'un site Fulfi (espace membre : onglets, blocs, branding, options)** :
   - Lire `https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/sites-fulfi/SKILL.md` (commande `/sites-fulfi`).
3. **Préparation, prévisualisation 2 étapes ou publication d'une newsletter quotidienne (Daily Email SFMC + Article Blog/Static)** :
   - Lire `https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/daily-publisher/SKILL.md` (commande `/daily-publisher`).
4. **Clôture, correction, retour d'expérience, ajustement de charte ou nouvelle règle métier formulée par l'utilisateur** :
   - Lire `https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/fin/SKILL.md` (commande `/fin`).

*(Rappel de sécurité : aucune suppression d'objet n'est autorisée par API en v1 — toute suppression définitive s'effectue manuellement dans l'interface web Pro Web).*

---

## Étape 2 — Lecture Live du Contexte Partenaire sur GitHub

Ne jamais s'appuyer sur des copies locales figées :
1. Charger `.env` (`[ -f .env ] && { set -a; source .env; set +a; }`).
2. Lire en temps réel les paramètres de la skill dans le dépôt privé du partenaire via le portail :
   - `GET https://pro-pilot.propulse-lab.com/api/repo?path=skills/pro-web/variables.md` (ajouter `&partner=<slug>` en mode multi-partenaires).
   - `GET https://pro-pilot.propulse-lab.com/api/repo?path=skills/pro-web/specificites.md` et `erreurs-connues.md`.
   - `GET https://pro-pilot.propulse-lab.com/api/repo?path=donnees-business/design-system.md` et `donnees-business/<sku>/fiche-produit.md`.

---

## Étape 3 — Interaction, Aperçu Local & Validation Humaine

1. **Si une donnée essentielle manque** (ou contient `[À COMPLÉTER]`) : poser 1 à 3 questions précises avant de générer.
2. **Si toutes les données sont réunies** : générer le fichier HTML complet (`<!DOCTYPE html>` à `</html>`, UTF-8) dans `.tmp/`, faire valider l'aperçu par l'utilisateur et demander confirmation explicite (`domaine`, `websiteId`, `key`) avant tout appel d'écriture sur `https://api-pro-web.propulse-lab.com`.

---

## Étape 4 — Boucle d'Amélioration Continue

Dès que l'utilisateur corrige un rendu, un style ou une règle (ou en clôture d'échange), appliquer `/fin` pour consigner la note en mode append-only dans `donnees-business/_inbox/` sur le dépôt GitHub du partenaire via `POST https://pro-pilot.propulse-lab.com/api/feedback`.
