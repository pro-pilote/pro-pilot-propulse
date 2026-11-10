# Règles Pro-Pilot — Propulse Lab (`partnerId: 9`)

Ce document est le cadre de référence pour tout assistant IA (Claude Code, Cursor, Antigravity) intervenant sur le dépôt socle de **Propulse Lab**.

---

## 0. Socle Central Natif
Ce dépôt contient directement les outils transverses dans [`outils/`](./outils/) et les règles dans [`regles/`](./regles/).
Aucune sous-synchronisation `.pro-pilot/` n'est requise dans ce dépôt maître.

---

## 1. Les Outils Pro Web & Socle Partagé (100 % API `x-api-key`)
Tous les appels passent par l'API publique **`https://api-pro-web.propulse-lab.com`** avec le header `x-api-key: $PRO_WEB_API_KEY` (chargé via `set -a; source .env; set +a`, jamais committé).

- **Domaine de test & validation** : `https://test.propulse-lab.com`
- **Garde-fous** : toujours valider l'aperçu local avant tout upload distant.
- **Référence détaillée** : consulter [`regles/garde-fous.md`](./regles/garde-fous.md).

---

## 2. Principes Fondamentaux
- **Zéro Troncature** : Toujours produire le code HTML complet.
- **Validation Humaine** : Ne jamais exécuter d'appel d'écriture API sans accord explicite dans le chat.
