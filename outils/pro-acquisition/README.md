# Outil : Pro Acquisition (Bons de Commande BDC & Opt-in PSOU/PCOU)

## 1. Objectif
Créer, modifier, vérifier et publier des Bons de Commande (Pro Funnel) et des formulaires d'opt-in (PSOU / PCOU) sans jamais altérer le tunnel de paiement.

## 2. Commandes `/pro-tools` (`tools/ppl.py bdc`)

```bash
# 1. Rapatrier un BDC existant
python3 tools/ppl.py bdc pull <slug_ou_url> --partner <PARTNER_ID>

# 2. Vérifier l'intégrité des blocs de paiement et scripts analytics (Linter bloquant)
python3 tools/ppl.py bdc audit <slug>

# 3. Prévisualiser en local sur http://127.0.0.1
python3 tools/ppl.py bdc preview <slug>

# 4. Publier en production (après audit OK + confirmation humaine dans le terminal)
python3 tools/ppl.py bdc push <slug> --go
```

## 3. Règles Critiques
- Ne jamais supprimer ni renommer les attributs `data-pf-*`, les conteneurs de paiement Stripe/Slimpay ou les variables Handlebars `{{...}}`.
- Toujours exécuter `bdc audit` avant de proposer l'aperçu au partenaire.
