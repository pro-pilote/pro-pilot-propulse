# Matrice de Décision — Router d'Actions Pro-Pilot

## Étape 1 — Détection de l'Intention & Chargement Live de la Skill

Récupère et applique en direct la dernière version officielle de la skill correspondant à la demande :

1. **Création, retouche, inventaire ou publication d'une page HTML / d'un document PDF ou image sur Pro Web** :
   - Lire `https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/pro-web/SKILL.md` (commande `/pro-web`).
2. **Préparation, prévisualisation 2 étapes ou publication d'une newsletter quotidienne (Daily Email SFMC + Article Blog/Static)** :
   - Lire `https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/daily-publisher/SKILL.md` (commande `/daily-publisher`).
3. **Clôture, correction, retour d'expérience, ajustement de charte ou nouvelle règle métier formulée par l'utilisateur** :
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
