# Guide Propulse Lab — Pro Acquisition / BDC ([[ppl.partner_name]])

## 1. Objectif & Paramètres Pré-remplis
Créer, modifier, vérifier et publier des Bons de Commande sur `[[ppl.funnel_domain]]` et des formulaires d'opt-in (PSOU / PCOU) pour **[[ppl.partner_name]]** (`partner_id: [[ppl.partner_id]]`).

## 2. Commandes `/pro-tools` (`tools/ppl.py bdc`)

```bash
# 1. Rapatrier un BDC existant de [[ppl.partner_name]]
python3 tools/ppl.py bdc pull <slug_ou_url> --partner [[ppl.partner_id]]

# 2. Vérifier l'intégrité des blocs de paiement et scripts analytics (Linter bloquant)
python3 tools/ppl.py bdc audit <slug>

# 3. Prévisualiser en local sur http://127.0.0.1
python3 tools/ppl.py bdc preview <slug>

# 4. Publier en production (après audit OK + confirmation humaine dans le terminal)
python3 tools/ppl.py bdc push <slug> --go
```

## 3. Règles Critiques
- Ne jamais supprimer ni renommer les attributs `data-pf-*`, les conteneurs de paiement Stripe/Slimpay ou les variables Handlebars `{{...}}`.
- Consulter [`specificites.md`](./specificites.md) et [`erreurs-connues.md`](./erreurs-connues.md) avant toute modification.
