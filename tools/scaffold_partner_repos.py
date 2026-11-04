#!/usr/bin/env python3
"""
Générateur déterministe des 13 dépôts partenaires Pro-Pilot (`pro-pilote/pro-pilot-<aws_slug>`)
Sources SSOT autorisées uniquement (ZÉRO mapping-prod.json) :
  1. Export Athena `pro_billing_prod.products` (/Users/medi/scratch/claude/athena-dl/out/pro_pilot_products_full.csv)
  2. Identifiants d'organisation AWS (~/.aws/config)
  3. Design tokens DTCG (~/Outils/design-system/tokens/<org>.dtcg.json)
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPOS_ROOT = Path("/Users/medi/Projects/2-projets-ppl/repos")
SOCLE_DIR = REPOS_ROOT / "pro-pilot-propulse"
ATHENA_CSV = Path("/Users/medi/scratch/claude/athena-dl/out/pro_pilot_products_full.csv")
DTCG_DIR = Path("/Users/medi/Outils/design-system/tokens")

PARTNERS = {
    2: {
        "aws_slug": "biosante",
        "aws_sso_session": "biosante",
        "aws_portal": "https://biosante-editions.awsapps.com/start/#/",
        "partner_name": "Éditions Biosanté",
        "main_domain": "editionsbiosante.fr",
        "funnel_domain": "paiement-securise.biosante-editions.com",
        "webinar_host": "event.prowebinaire.com",
        "gtm_id": "GTM-BIOSANTE",
        "dtcg_file": "bse.dtcg.json",
        "static_domains": [
            "editionsbiosante.fr",
            "alternativesante.fr",
            "sante-corps-esprit.com",
            "plantes-et-sante.fr",
        ],
    },
    4: {
        "aws_slug": "vivasante",
        "aws_sso_session": "vivasante",
        "aws_portal": "https://vivasante.awsapps.com/start/#/",
        "partner_name": "Éditions VivaSanté",
        "main_domain": "editions-vivasante.com",
        "funnel_domain": "paiement-securise.editions-vivasante.com",
        "webinar_host": "event.prowebinaire.com",
        "gtm_id": "GTM-VIVASANTE",
        "dtcg_file": "viv.dtcg.json",
        "static_domains": [
            "editions-vivasante.com",
            "remedes-vivasante.com",
        ],
    },
    5: {
        "aws_slug": "biovancia",
        "aws_sso_session": "biovancia",
        "aws_portal": "https://biovancia.awsapps.com/start",
        "partner_name": "Institut Biovancia",
        "main_domain": "biovancia.com",
        "funnel_domain": "paiement-securise.biovancia.com",
        "webinar_host": "event.prowebinaire.com",
        "gtm_id": "GTM-BIOVANCIA",
        "dtcg_file": None,
        "static_domains": [
            "biovancia.com",
        ],
    },
    10: {
        "aws_slug": "innovia",
        "aws_sso_session": "innovia",
        "aws_portal": "https://innovia.awsapps.com/start",
        "partner_name": "Innovia Laboratoires (Sérénalpes)",
        "main_domain": "serenalpes.com",
        "funnel_domain": "paiement-securise.serenalpes.com",
        "webinar_host": "event.prowebinaire.com",
        "gtm_id": "GTM-INNOVIA",
        "dtcg_file": None,
        "static_domains": [
            "serenalpes.com",
        ],
    },
    12: {
        "aws_slug": "pantheon",
        "aws_sso_session": "pantheon",
        "aws_portal": "https://pantheon-recherche.awsapps.com/start/#/",
        "partner_name": "Panthéon Recherche",
        "main_domain": "pantheon-recherche.com",
        "funnel_domain": "paiement-securise.pantheon-recherche.com",
        "webinar_host": "event.prowebinaire.com",
        "gtm_id": "GTM-PANTHEON",
        "dtcg_file": "pan.dtcg.json",
        "static_domains": [
            "pantheon-recherche.com",
            "citadelle-suisse.com",
            "ia-visionnaire.fr",
            "le-coffre-fort-pantheon-recherche.com",
        ],
    },
    14: {
        "aws_slug": "cilumine",
        "aws_sso_session": "cilumine",
        "aws_portal": "https://cilumine.awsapps.com/start/#/",
        "partner_name": "Institut Cilumine",
        "main_domain": "cilumine.com",
        "funnel_domain": "paiement-securise.cilumine.com",
        "webinar_host": "event.prowebinaire.com",
        "gtm_id": "GTM-CILUMINE",
        "dtcg_file": None,
        "static_domains": [
            "cilumine.com",
        ],
    },
    15: {
        "aws_slug": "nutrazenith",
        "aws_sso_session": "nutrazenith",
        "aws_portal": "https://nutrazenith.awsapps.com/start/#/",
        "partner_name": "Laboratoire Nutrazenith",
        "main_domain": "nutrazenith.com",
        "funnel_domain": "paiement-securise.nutrazenith.com",
        "webinar_host": "event.prowebinaire.com",
        "gtm_id": "GTM-NUTRAZENITH",
        "dtcg_file": None,
        "static_domains": [
            "nutrazenith.com",
        ],
    },
    20: {
        "aws_slug": "nutriorigines",
        "aws_sso_session": "nutriorigines",
        "aws_portal": "https://nutriorigines.awsapps.com/start/#/",
        "partner_name": "Laboratoire NutriOrigines",
        "main_domain": "nutriorigines.com",
        "funnel_domain": "paiement-securise.nutriorigines.com",
        "webinar_host": "event.prowebinaire.com",
        "gtm_id": "GTM-NUTRIORIGINES",
        "dtcg_file": None,
        "static_domains": [
            "nutriorigines.com",
        ],
    },
    21: {
        "aws_slug": "optima",
        "aws_sso_session": "optima",
        "aws_portal": "https://optima-editions.awsapps.com/start/#/",
        "partner_name": "Éditions Optima",
        "main_domain": "optima-editions.com",
        "funnel_domain": "paiement-securise.optima-editions.com",
        "webinar_host": "event.prowebinaire.com",
        "gtm_id": "GTM-OPTIMA",
        "dtcg_file": "opt.dtcg.json",
        "static_domains": [
            "optima-editions.com",
            "agora-editions-optima.com",
        ],
    },
    23: {
        "aws_slug": "tao",
        "aws_sso_session": "editions-tao",
        "aws_portal": "https://editions-tao.awsapps.com/start/#/",
        "partner_name": "Éditions TAO",
        "main_domain": "editions-tao.com",
        "funnel_domain": "paiement-securise.editions-tao.com",
        "webinar_host": "event.prowebinaire.com",
        "gtm_id": "GTM-TAO",
        "dtcg_file": "tao.dtcg.json",
        "static_domains": [
            "editions-tao.com",
        ],
    },
    24: {
        "aws_slug": "aps",
        "aws_sso_session": "aps",
        "aws_portal": "https://aps-formation.awsapps.com/start/#/",
        "partner_name": "Apprendre Préparer Survivre",
        "main_domain": "apprendre-preparer-survivre.com",
        "funnel_domain": "paiement-securise.apprendre-preparer-survivre.com",
        "webinar_host": "event.prowebinaire.com",
        "gtm_id": "GTM-APS",
        "dtcg_file": "aps.dtcg.json",
        "static_domains": [
            "apprendre-preparer-survivre.com",
            "sain-et-naturel.ouest-france.fr",
        ],
    },
    25: {
        "aws_slug": "inse",
        "aws_sso_session": "institut-epargne",
        "aws_portal": "https://institut-epargne.awsapps.com/start/#/",
        "partner_name": "Institut de l'Épargne",
        "main_domain": "institutdelepargne.com",
        "funnel_domain": "paiement-securise.institutdelepargne.com",
        "webinar_host": "event.prowebinaire.com",
        "gtm_id": "GTM-INSE",
        "dtcg_file": "ie.dtcg.json",
        "static_domains": [
            "institutdelepargne.com",
        ],
    },
    26: {
        "aws_slug": "lfp",
        "aws_sso_session": "lfp",
        "aws_portal": "https://lfp.awsapps.com/start/#/",
        "partner_name": "Léman Financial Press",
        "main_domain": "lemanfp.com",
        "funnel_domain": "paiement-securise.lemanfp.com",
        "webinar_host": "event.prowebinaire.com",
        "gtm_id": "GTM-LFP",
        "dtcg_file": "lfp.dtcg.json",
        "static_domains": [
            "lemanfp.com",
        ],
    },
}


def is_test_product(row: dict) -> bool:
    sku_u = (row.get("sku") or "").strip().upper()
    name_u = (row.get("name") or "").strip().upper()
    return "TEST" in sku_u or "TEST" in name_u or sku_u.startswith("SKU")


def load_dtcg_tokens(dtcg_filename: str | None) -> dict | None:
    if not dtcg_filename:
        return None
    p = DTCG_DIR / dtcg_filename
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def resolve_product_design_tokens(dtcg: dict | None, row: dict) -> dict:
    if not dtcg:
        return {
            "primary": "[À COMPLÉTER — Couleur Primaire]",
            "accent": "[À COMPLÉTER — Couleur Accent / CTA]",
            "surface": "#FFFFFF",
            "secondary": "#F8FAFC",
            "text": "#1E293B",
            "font_display": "[À COMPLÉTER — Police Titres]",
            "font_sans": "[À COMPLÉTER — Police Corps de texte]",
            "source_note": "Tokens DTCG à compléter par l'équipe Design du partenaire",
        }
    color = dtcg.get("color", {})
    typo = dtcg.get("typography", {})
    pubs = dtcg.get("partner", {}).get("publications", [])

    bu_l = (row.get("businessunit") or "").lower()
    name_l = (row.get("name") or "").lower()
    matched_pub = None
    for pub in pubs:
        title_l = (pub.get("title") or "").lower()
        if title_l and (title_l in bu_l or title_l in name_l or (bu_l and bu_l in title_l)):
            matched_pub = pub
            break

    primary = (matched_pub or {}).get("primary") or color.get("primary", {}).get("$value", "#111827")
    accent = (matched_pub or {}).get("accent") or color.get("accent", {}).get("$value", "#2563EB")
    surface = (matched_pub or {}).get("surface") or color.get("surface", {}).get("$value", "#FFFFFF")
    secondary = (matched_pub or {}).get("secondary") or color.get("secondary", {}).get("$value", "#F8FAFC")
    text_col = (matched_pub or {}).get("text") or color.get("text", {}).get("$value", "#111827")
    font_display = typo.get("display", {}).get("$value", "Georgia, serif")
    font_sans = typo.get("sans", {}).get("$value", "Inter, system-ui, sans-serif")
    source_note = dtcg.get("partner", {}).get("source_note", "Tokens DTCG Propulse Lab")
    return {
        "primary": primary,
        "accent": accent,
        "surface": surface,
        "secondary": secondary,
        "text": text_col,
        "font_display": font_display,
        "font_sans": font_sans,
        "source_note": source_note,
    }


def render_fiche_produit(partner_meta: dict, row: dict) -> str:
    sku = (row.get("sku") or "").strip()
    name = (row.get("name") or "").strip()
    bu = (row.get("businessunit") or "").strip() or partner_meta["partner_name"]
    ptype = (row.get("type") or "").strip() or "Non spécifié"
    category = (row.get("category") or "").strip() or "Non spécifiée"
    delivery = (row.get("deliverymode") or "").strip() or "Non spécifié"
    desc = (row.get("description") or "").strip() or "Description éditoriale à enrichir dans cette fiche."
    image = (row.get("image") or "").strip() or "Aucune image référencée dans Pro Billing"

    return f"""# Fiche Produit — {name} (`{sku}`)

## 1. Identité du Produit (Source SSOT : `pro_billing_prod.products`)
- **Partenaire** : {partner_meta["partner_name"]} (`partner_id: {row["partnerid"]}`)
- **Business Unit / Marque** : {bu}
- **Nom du Produit** : {name}
- **Code Produit (SKU Pro Billing)** : `{sku}`
- **Type de Produit** : `{ptype}`
- **Catégorie** : `{category}`
- **Mode de Livraison (`deliverymode`)** : `{delivery}`
- **Visuel Produit (`image`)** : `{image}`
- **Domaine Principal** : `https://{partner_meta["main_domain"]}`
- **Domaine BDC / Checkout** : `https://{partner_meta["funnel_domain"]}`

## 2. Description & Positionnement Éditorial
- **Description Pro Billing** : {desc}
- **Public cible** : Lecteurs, prospects et clients de {bu} ({partner_meta["partner_name"]}).
- **Ton éditorial** : Clair, rigoureux, sourcé et conforme aux exigences de {partner_meta["partner_name"]}.

## 3. Offres & Paramètres de Conversion
- **Format principal** : `{ptype}` ({category} / `{delivery}`)
- **Arguments clés (Bullets)** :
  1. [À COMPLÉTER — Argument clé 1 du produit `{sku}`]
  2. [À COMPLÉTER — Argument clé 2 du produit `{sku}`]
  3. [À COMPLÉTER — Argument clé 3 du produit `{sku}`]

## 4. Mentions Légales & Pied de Page Obligatoire
- Mentions légales officielles de **{partner_meta["partner_name"]}** (`https://{partner_meta["main_domain"]}`) + liens CGV et Politique de confidentialité obligatoires en pied de page.
"""


def render_design_system(partner_meta: dict, row: dict, tokens: dict) -> str:
    sku = (row.get("sku") or "").strip()
    name = (row.get("name") or "").strip()
    bu = (row.get("businessunit") or "").strip() or partner_meta["partner_name"]

    return f"""# Design System — {name} (`{sku}`)

> **Marque / Business Unit** : {bu} ({partner_meta["partner_name"]})
> **Source Tokens** : {tokens["source_note"]}

## 1. Palette de Couleurs
- **Couleur Primaire (Titres & En-têtes)** : `{tokens["primary"]}`
- **Couleur d'Accent / Bouton CTA** : `{tokens["accent"]}`
- **Couleur de Fond Principal (`surface`)** : `{tokens["surface"]}`
- **Couleur de Fond Sections Secondaires (`secondary`)** : `{tokens["secondary"]}`
- **Couleur de Texte Principal (`text`)** : `{tokens["text"]}`

## 2. Typographies
- **Titres (H1, H2, H3)** : `{tokens["font_display"]}`
- **Corps de texte & Formulaires** : `{tokens["font_sans"]}`

## 3. Composants & Règles Visuelles
- **Boutons d'action (CTA)** : coins arrondis (`8px`), contraste WCAG AA respecté, verbe d'action explicite.
- **Responsive Mobile-First** : taille de police minimale `16px` sur mobile (`375px`), formulaire ou CTA visible dès le premier écran lorsque requis.
"""


def write_partner_scaffold(partner_id: int, meta: dict, products: list[dict]):
    repo_name = f"pro-pilot-{meta['aws_slug']}"
    repo_dir = REPOS_ROOT / repo_name
    repo_dir.mkdir(parents=True, exist_ok=True)

    # 1. Nettoyer donnees-business/ et écrire uniquement les produits de ce partenaire (partner_id)
    db_dir = repo_dir / "donnees-business"
    if db_dir.exists():
        shutil.rmtree(db_dir)
    db_dir.mkdir(parents=True, exist_ok=True)

    dtcg = load_dtcg_tokens(meta["dtcg_file"])

    sku_list = []
    for row in sorted(products, key=lambda r: (r.get("sku") or "").upper()):
        assert int(row["partnerid"]) == partner_id, f"Violation d'isolation: produit {row} dans partner {partner_id}"
        sku_raw = (row.get("sku") or "").strip()
        sku_folder = sku_raw.lower()
        sku_list.append(sku_raw)
        prod_dir = db_dir / sku_folder
        prod_dir.mkdir(parents=True, exist_ok=True)

        tokens = resolve_product_design_tokens(dtcg, row)
        (prod_dir / "fiche-produit.md").write_text(render_fiche_produit(meta, row), encoding="utf-8")
        (prod_dir / "design-system.md").write_text(render_design_system(meta, row, tokens), encoding="utf-8")

    # Index récapitulatif donnees-business/README.md pour navigation rapide par l'IA
    rows_md = []
    for row in sorted(products, key=lambda r: (r.get("sku") or "").upper()):
        sku_raw = (row.get("sku") or "").strip()
        sku_l = sku_raw.lower()
        name = (row.get("name") or "").strip().replace("|", "-")
        bu = (row.get("businessunit") or "").strip().replace("|", "-") or "—"
        ptype = (row.get("type") or "").strip() or "—"
        cat = (row.get("category") or "").strip() or "—"
        rows_md.append(
            f"| `{sku_raw}` | {name} | {bu} | `{ptype}` | `{cat}` | [`donnees-business/{sku_l}/`](./{sku_l}/fiche-produit.md) |"
        )
    db_index = (
        f"# Catalogue Produits — {meta['partner_name']} (`partner_id: {partner_id}`)\n\n"
        f"Ce répertoire contient les **{len(products)} produits actifs (hors test)** de **{meta['partner_name']}** extraits de `pro_billing_prod.products`.\n\n"
        "| SKU (`pro_billing`) | Nom du Produit | Business Unit | Type | Catégorie | Dossier Fiche & Design System |\n"
        "|---|---|---|---|---|---|\n"
        + "\n".join(rows_md)
        + "\n"
    )
    (db_dir / "README.md").write_text(db_index, encoding="utf-8")

    # 2. Créer / mettre à jour les 4 dossiers outils/<outil>/{variables,specificites,erreurs-connues}.md
    outils_dir = repo_dir / "outils"
    outils_dir.mkdir(parents=True, exist_ok=True)

    variables_common = (
        f"# Variables Partenaire — {meta['partner_name']}\n\n"
        f"- `ppl.partner_slug` : `{meta['aws_slug']}`\n"
        f"- `ppl.partner_name` : `{meta['partner_name']}`\n"
        f"- `ppl.partner_id` : `{partner_id}`\n"
        f"- `ppl.main_domain` : `{meta['main_domain']}`\n"
        f"- `ppl.webinar_host` : `{meta['webinar_host']}`\n"
        f"- `ppl.funnel_domain` : `{meta['funnel_domain']}`\n"
        f"- `ppl.gtm_id` : `{meta['gtm_id']}`\n"
    )

    domains_bullets = "\n".join(f"- `https://{d}`" for d in meta["static_domains"])

    tool_specs = {
        "pro-web-page-creator": (
            f"# Spécificités — Pro Web Page Creator ({meta['partner_name']})\n\n"
            f"## Domaines autorisés pour {meta['partner_name']}\n"
            f"{domains_bullets}\n\n"
            "## Règles de Génération\n"
            "- Toujours charger `donnees-business/<sku>/fiche-produit.md` et `donnees-business/<sku>/design-system.md` avant de générer une page.\n"
            f"- Conserver le conteneur GTM `{meta['gtm_id']}` intact.\n"
        ),
        "pro-web-uploader": (
            f"# Spécificités — Pro Web Uploader ({meta['partner_name']})\n\n"
            "## Domaines cibles Pro Web (`ppl static`)\n"
            f"{domains_bullets}\n\n"
            "## Garde-fous de Publication\n"
            "- Toujours vérifier l'aperçu local (`preview`) et l'anti-collision (`list`) avant toute mise en ligne.\n"
        ),
        "pro-webinaire": (
            f"# Spécificités — Pro Webinaire ({meta['partner_name']})\n\n"
            f"- **Hôte Webinaire** : `https://{meta['webinar_host']}`\n"
            f"- **Domaine des Landing Pages Webinaire** : `https://{meta['main_domain']}`\n"
            "- Toujours demander le `<SALLE_SLUG>` exact avant d'intégrer le widget d'inscription.\n"
        ),
        "pro-acquisition": (
            f"# Spécificités — Pro Acquisition / BDC ({meta['partner_name']})\n\n"
            f"- **Domaine BDC / Pro Funnel** : `https://{meta['funnel_domain']}`\n"
            f"- **Identifiant Partenaire (`partner_id`)** : `{partner_id}`\n"
            "- Toujours utiliser le code produit (`SKU`) exact référencé dans `donnees-business/<sku>/fiche-produit.md`.\n"
        ),
    }

    for tool_slug, spec_content in tool_specs.items():
        t_dir = outils_dir / tool_slug
        t_dir.mkdir(parents=True, exist_ok=True)
        (t_dir / "variables.md").write_text(variables_common, encoding="utf-8")
        (t_dir / "specificites.md").write_text(spec_content, encoding="utf-8")
        err_file = t_dir / "erreurs-connues.md"
        if not err_file.exists():
            err_file.write_text(
                f"# Erreurs Connues — {tool_slug} ({meta['partner_name']})\n\n"
                "- Ne jamais modifier à la main l'intérieur des conteneurs de formulaires ou de scripts injectés.\n"
                "- Ne jamais inventer un identifiant de salle, un code source (`SRC`) ou un tarif non présent dans le brief ou la fiche produit.\n",
                encoding="utf-8",
            )

    # 3. .github/ISSUE_TEMPLATE/feedback.yml & .github/workflows/apply-feedback.yml
    issue_tpl_dir = repo_dir / ".github" / "ISSUE_TEMPLATE"
    wf_dir = repo_dir / ".github" / "workflows"
    issue_tpl_dir.mkdir(parents=True, exist_ok=True)
    wf_dir.mkdir(parents=True, exist_ok=True)

    (issue_tpl_dir / "feedback.yml").write_text(
        """name: "Retour IA / Amélioration Pro-Pilot"
description: "Signaler une erreur commise par l'IA ou ajouter une spécificité métier pour éviter qu'elle ne se reproduise."
title: "[FEEDBACK] "
labels: ["statut:à-trier"]
body:
  - type: dropdown
    id: categorie
    attributes:
      label: "Catégorie du retour"
      description: "Quel dossier du dépôt partenaire doit être enrichi ?"
      options:
        - "Outil — Pro Web Page Creator (outils/pro-web-page-creator/)"
        - "Outil — Pro Webinaire (outils/pro-webinaire/)"
        - "Outil — Pro Web Uploader (outils/pro-web-uploader/)"
        - "Outil — Pro Acquisition / BDC (outils/pro-acquisition/)"
        - "Données Business — Fiche Produit (donnees-business/<sku>/fiche-produit.md)"
        - "Données Business — Design System (donnees-business/<sku>/design-system.md)"
    validations:
      required: true
  - type: input
    id: fichier_cible
    attributes:
      label: "Chemin du fichier cible dans ce dépôt"
      placeholder: "ex: outils/pro-web-page-creator/erreurs-connues.md"
    validations:
      required: true
  - type: textarea
    id: erreur_constatee
    attributes:
      label: "Ce que l'IA a fait par erreur (ou ce qui manquait)"
      placeholder: "Décrire brièvement l'erreur constatée sur la page ou dans la réponse de l'IA."
    validations:
      required: true
  - type: textarea
    id: regle_attendue
    attributes:
      label: "Règle ou correctif à enregistrer (Markdown prêt à intégrer)"
      placeholder: "Écrire la règle claire que l'IA devra systématiquement appliquer la prochaine fois."
    validations:
      required: true
""",
        encoding="utf-8",
    )

    (wf_dir / "apply-feedback.yml").write_text(
        """name: "Phase 2 — Intégration Automatique d'un Feedback Validé"

on:
  issues:
    types: [labeled]

permissions:
  contents: write
  pull-requests: write
  issues: write

jobs:
  create-feedback-pr:
    if: github.event.label.name == 'validé'
    runs-on: ubuntu-latest
    steps:
      - name: Checkout du dépôt partenaire
        uses: actions/checkout@v4

      - name: Préparation de la Pull Request à partir de l'Issue validée
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          ISSUE_TITLE: ${{ github.event.issue.title }}
          ISSUE_BODY: ${{ github.event.issue.body }}
        run: |
          echo "Traitement automatisé de l'Issue #${ISSUE_NUMBER} : ${ISSUE_TITLE}"
""",
        encoding="utf-8",
    )

    # 4. .gitignore, README.md, partner-manifest.json
    (repo_dir / ".gitignore").write_text(
        ".DS_Store\n.pro-pilot/\nbackups/\nnode_modules/\nsites/\nbdcs/\ndist/\n*.local.json\n.env\n.env.local\n__pycache__/\n*.pyc\n",
        encoding="utf-8",
    )

    (repo_dir / "README.md").write_text(
        f"""# Pro-Pilot — Dépôt Partenaire {meta['partner_name']} (`{repo_name}`)

Dépôt autonome de **{meta['partner_name']}** (`partner_id: {partner_id}`, organisation AWS `{meta['aws_slug']}`) pour **Pro-Pilot**.
Le socle Propulse Lab (`ROUTER.md`, `getting-started/`, `regles/`, `tools/` et les guides `outils/<outil>/guide-propulse.md`) est **pré-compilé automatiquement** avec les variables de `{meta['partner_name']}` issues de `variables.md`.

## Structure du Dépôt

```text
{repo_name}/
├── ROUTER.md                         # Routeur atomique (pré-rempli pour {meta['partner_name']})
├── getting-started/                  # Starter pack & fiche mémoire locale (.pro-pilot/profile.md)
├── regles/                           # // REGLES (Glossaire, Letta, niveau tech, checklist, garde-fous)
├── donnees-business/                 # // DONNEE BUSINESS ({len(products)} produits Pro Billing : <sku>/fiche-produit.md + design-system.md)
├── outils/                           # // OUTILS (Outils activés pour {meta['partner_name']})
│   ├── pro-acquisition/
│   ├── pro-web-page-creator/
│   ├── pro-web-uploader/
│   └── pro-webinaire/
├── tools/                            # Scripts d'exécution locale /pro-tools (ppl)
└── .github/
    ├── ISSUE_TEMPLATE/feedback.yml   # Remontée d'erreur IA (Étape 4)
    └── workflows/apply-feedback.yml  # Automatisation Phase 2 (sur label 'validé')
```
""",
        encoding="utf-8",
    )

    manifest = {
        "repo": f"pro-pilote/{repo_name}",
        "partner_id": partner_id,
        "partner_slug": meta["aws_slug"],
        "aws_sso_session": meta["aws_sso_session"],
        "aws_portal": meta["aws_portal"],
        "partner_name": meta["partner_name"],
        "main_domain": meta["main_domain"],
        "funnel_domain": meta["funnel_domain"],
        "webinar_host": meta["webinar_host"],
        "products_count": len(products),
        "active_tools": sorted(tool_specs.keys()),
    }
    (repo_dir / "partner-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # 5. Compiler via compile_partner_repo.py
    subprocess.run(
        [sys.executable, str(SOCLE_DIR / "tools" / "compile_partner_repo.py"), str(SOCLE_DIR), str(repo_dir)],
        check=True,
    )
    return repo_dir, len(products)


def main():
    if not ATHENA_CSV.exists():
        raise FileNotFoundError(f"Export Athena introuvable : {ATHENA_CSV}")

    rows = list(csv.DictReader(ATHENA_CSV.open("r", encoding="utf-8")))
    by_partner: dict[int, list[dict]] = {pid: [] for pid in PARTNERS}

    skipped_tests = 0
    for r in rows:
        if is_test_product(r):
            skipped_tests += 1
            continue
        pid = int(r["partnerid"])
        if pid not in PARTNERS:
            raise ValueError(f"partnerid={pid} inconnu dans PARTNERS: {r}")
        by_partner[pid].append(r)

    total_dispatched = 0
    for pid, meta in sorted(PARTNERS.items()):
        prods = by_partner[pid]
        repo_dir, count = write_partner_scaffold(pid, meta, prods)
        total_dispatched += count
        print(f"  -> partner_id={pid:<2} | {repo_dir.name:<25} | {count:>3} produits Pro Billing générés")

    print(f"\n[SUMMARY] {len(PARTNERS)} dépôts partenaires générés | {total_dispatched} produits hors test dispatchés ({skipped_tests} produits de test exclus).")


if __name__ == "__main__":
    main()
