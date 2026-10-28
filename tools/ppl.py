#!/usr/bin/env python3
"""
ppl — CLI Unifié de la Suite Propulse Lab Partner Tools (5 Piliers).

Conception & Architecture : Medi Chabrol · Propulse Lab
Doctrine Globale : Pro-IPS, Cloisonnement Multi-Tenant, Zero Extrapolation.

Usage :
  python ppl.py doctor
  python ppl.py login [--paste]
  python ppl.py whoami
  python ppl.py init <domaine | slug-bdc | url>
  python ppl.py static <pull|preview|push|diff|ls|resolve> [domaine]
  python ppl.py bdc <pull|audit|preview> [slug]
  python ppl.py acq check --list <l> --fields <f> --source <s> --redirect <r> --create-conf-page <o|n>
  python ppl.py doc --tool <nom|all> [--partner <slug|id>]
  python ppl.py doc --list
  python ppl.py update
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

# Chargement du socle multi-OS
import proweb_env
import proweb_auth

ROOT_DIR = Path(__file__).resolve().parent

BANNER = """
========================================================================
⚡ PROPULSE LAB · PRO TOOLS PARTNER (ppl)
Architecture & Conception : Medi Chabrol
========================================================================

Commandes Rapides :
  • doctor     → Diagnostic complet de l'OS, de la machine et du token
  • login      → Connexion Pro Web (Keychain auto sous macOS, guidé sous Windows)
  • whoami     → Vérification de votre identité et organisations autorisées
  • init       → Initialise en < 15s n'importe quel site STATIC, BDC ou espace
  • update     → Met à jour le kit et la documentation depuis le dépôt officiel

Piliers Techniques Disponibles :
  1. static    → Sites Vitrines STATIC Pro Web (S3 / CloudFront)
  2. bdc       → Bons de Commande BDC (Pro Funnel — Audit contractuel DOM/CSS)
  3. platform  → Espaces Membres & Plateformes (ai-child / REST API)
  4. acq       → Pro Acquisition (Formulaires Optin, Listes Blueshift/SFMC)
  5. doc       → Compilateur de Documentation Atomique Partenaire

Usage :
  ppl init <domaine | slug-bdc | url>
  ppl doc --tool <nom|all> [--partner <slug|id>]
  ppl doc --list
  ppl update
  ppl <commande> [options...]
"""


def cmd_whoami():
    token = proweb_env.load_token()
    if not token or not token.get("bearer"):
        print("❌ Non connecté. Lancez : python ppl.py login")
        sys.exit(1)
    
    import requests
    headers = {
        "Authorization": f"Bearer {token['bearer']}",
        "Content-Type": "application/json"
    }
    try:
        r = requests.post("https://pro-web.propulse-lab.com/api/auth/user", headers=headers, json={}, timeout=15)
        if r.status_code != 200:
            print(f"❌ Erreur d'authentification Pro Web (HTTP {r.status_code}). Lancez : python ppl.py login")
            sys.exit(1)
        user_res = r.json()
        user = user_res.get("data", user_res) if isinstance(user_res, dict) else {}
        print("\n👤 Identité Connectée :")
        print(f"  • Email         : {user.get('email')}")
        print(f"  • Nom           : {user.get('name')}")
        print(f"  • Rôles         : {', '.join(user.get('roles', []))}")
        print(f"  • Organisations : {user.get('partners', [])}\n")
    except Exception as e:
        print(f"❌ Erreur réseau lors de la vérification : {e}")
        sys.exit(1)


def cmd_update(args):
    """Met à jour le kit de documentation et d'outils partenaires."""
    version_file = ROOT_DIR / "VERSION"
    current_ver = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else "1.0.0"
    print(f"\n🔄 Vérification des mises à jour pour pro-tools-partner (version actuelle: {current_ver})...\n")

    git_dir = ROOT_DIR / ".git"
    if not git_dir.exists():
        print("📦 Ce kit est installé via une archive locale sans Git.")
        print("👉 Pour mettre à jour la documentation et les outils, téléchargez la dernière archive livrée par Propulse Lab.\n")
        return 0

    try:
        remotes_proc = subprocess.run(["git", "remote"], cwd=str(ROOT_DIR), capture_output=True, text=True, check=True)
        remotes = remotes_proc.stdout.strip().split()
    except Exception as e:
        print(f"⚠️ Impossible d'exécuter git : {e}\n")
        return 1

    if not remotes:
        print("📦 Aucun remote Git configuré (installation locale).")
        print("👉 Pour lier votre kit au dépôt officiel Propulse Lab :")
        print("   git remote add origin https://github.com/propulse-lab/pro-tools-partner.git")
        print("   git pull origin main\n")
        return 0

    # Vérification de la branche courante (main requise)
    try:
        branch_proc = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(ROOT_DIR), capture_output=True, text=True, check=True)
        current_branch = branch_proc.stdout.strip()
        if current_branch != "main":
            print(f"⚠️ Vous êtes sur la branche « {current_branch} » (main requise). Mise à jour automatique refusée pour éviter les conflits.\n")
            return 1
    except Exception as e:
        print(f"⚠️ Impossible de déterminer la branche courante : {e}\n")
        return 1

    # Vérification de l'état de l'arbre de travail (zéro modification locale non commitée)
    try:
        status_proc = subprocess.run(["git", "status", "--porcelain"], cwd=str(ROOT_DIR), capture_output=True, text=True, check=True)
        if status_proc.stdout.strip():
            print("⚠️ Des modifications locales non commitées sont présentes. Mise à jour refusée pour ne pas écraser votre travail.\n")
            return 1
    except Exception as e:
        print(f"⚠️ Impossible de vérifier le statut git : {e}\n")
        return 1

    remote_name = "origin" if "origin" in remotes else remotes[0]

    # Vérification de sécurité de l'URL du remote (dépôt officiel Propulse Lab requis)
    try:
        url_proc = subprocess.run(["git", "remote", "get-url", remote_name], cwd=str(ROOT_DIR), capture_output=True, text=True, check=True)
        remote_url = url_proc.stdout.strip().lower().rstrip("/")
        allowed_remotes = {
            "https://github.com/propulse-lab/pro-tools-partner",
            "https://github.com/propulse-lab/pro-tools-partner.git",
            "git@github.com:propulse-lab/pro-tools-partner.git"
        }
        if remote_url not in allowed_remotes:
            print(f"⚠️ Remote non officiel détecté : « {remote_url} ». Mise à jour refusée par sécurité (dépôt officiel attendu).\n")
            return 1
    except Exception as e:
        print(f"⚠️ Impossible de vérifier l'URL du remote « {remote_name} » : {e}\n")
        return 1

    print(f"📡 Récupération des dernières versions depuis « {remote_name} »...")
    try:
        subprocess.run(["git", "fetch", remote_name], cwd=str(ROOT_DIR), check=True)
        res = subprocess.run(["git", "pull", "--ff-only", remote_name, "main"], cwd=str(ROOT_DIR), capture_output=True, text=True)
        if res.returncode == 0:
            if "Already up to date" in res.stdout or "Déjà à jour" in res.stdout:
                print("✅ Votre suite pro-tools-partner est déjà parfaitement à jour.\n")
            else:
                new_ver = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else current_ver
                print(f"✅ Mise à jour appliquée avec succès ! Nouvelle version : {new_ver}\n")
                print(res.stdout)
            return 0
        else:
            print(f"⚠️ Attention lors de la mise à jour (git pull) :\n{res.stderr}\n")
            return 1
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour : {e}\n")
        return 1


def build_rules(clean_domain: str, partner_id: int, duplicate_pairs: list = None) -> str:
    """Génère le contenu de RULES.md / CLAUDE.md pour un site statique."""
    dup_rules = ""
    if duplicate_pairs:
        dup_rules = (
            f"\n### ⚠️ Règle Double Arborescence HTML ({len(duplicate_pairs)} pages détectées) :\n"
            "Les sous-pages suivantes existent à la fois sous forme de dossier et de fichier .html :\n"
            + "\n".join(f"  - /{p}/index.html ET /{p}.html" for p in duplicate_pairs)
            + "\n👉 Si tu modifies l'une de ces pages, mets TOUJOURS à jour les deux fichiers de façon identique !\n"
        )

    return f"""# Consignes Assistant IA (Grok / ChatGPT / Claude / Cursor) — {clean_domain}

> **Site** : {clean_domain} (Partner ID: {partner_id})
> **Architecture** : Site **statique pur** (HTML5, CSS, JS, images). Zéro WordPress, zéro CMS.

---

## 🛑 RÈGLE D'OR POUR L'IA (GROK / CHATGPT) : ZÉRO TRONCATURE

Quand tu génères du code HTML, CSS ou JS pour ce site :
1. **INTERDICTION FORMELLE DE TRONQUER LE CODE** avec des commentaires du type :
   - `<!-- rest of code unchanged -->`
   - `<!-- reste du code inchangé -->`
   - `<!-- same as before -->`
   - `/* rest of code unchanged */`
2. **FOURNIR LE FICHIER COMPLET** : Tout fichier HTML doit être fourni intégralement, de `<!DOCTYPE html>` jusqu'à `</html>`.
   L'utilisateur travaille en remplacement complet dans son éditeur local. Un fichier tronqué détruirait la mise en page en production.

---

## 🔄 Workflow Autonome pour l'Agent IA (Grok / Cursor / Claude)

1. **Édition du Code** :
   - Modifie directement les fichiers locaux (ex: `index.html`) en fournissant toujours le code HTML complet.
2. **Contrôle Pré-vol (Dry-Run)** :
   - Lance le contrôle pré-vol : `python ppl.py static push {clean_domain}`
   - Présente le récapitulatif des fichiers modifiés à l'utilisateur dans le chat.
3. **Publication en Production (Sur Accord de l'Utilisateur)** :
   - Dès que l'utilisateur valide dans le chat (ex: "go", "publie", "oui"), exécute :
     `python ppl.py static push {clean_domain} --go --yes`
   - Le flag `--yes` confirme l'approbation explicite de l'utilisateur dans le chat.

---

## 5 Règles Techniques Essentielles

### 1. Chemins d'Assets Statiques
- Les images et styles sont servis depuis la racine : `/assets/images/...`, `/assets/css/...`.
- Ne convertis jamais ces chemins en relatifs. Utilise `preview` pour tester en local.
{dup_rules}
### 2. Formats Autorisés & Interdiction Vidéo
- Formats autorisés : HTML, CSS, JS, JSON, images WebP/PNG/JPG/SVG, PDF.
- **Vidéos strictement interdites** sur STATIC : elles doivent être hébergées sur la plateforme Pro Video.
- Taille max : 20 Mo par fichier.

### 3. Navigation & Liens Internes
- Liens internes toujours avec slash final : `href="/"`, `href="/<slug>/"`.

### 4. Sécurité & Approbation Chat
- L'agent exécute les commandes à la place de l'utilisateur.
- L'agent ne doit lancer `--go --yes` qu'après approbation explicite de l'utilisateur dans la conversation chat.
"""


def cmd_init(args):
    if not args:
        print("Usage : ppl init <domaine | slug-bdc | url>")
        sys.exit(1)

    target_spec = args[0].strip()

    # Détection Bon de Commande Pro Funnel
    is_bdc = "paiement-securise." in target_spec or "secure." in target_spec or target_spec.upper().startswith("SRC-") or target_spec.upper().startswith("PPL-")

    if is_bdc:
        print(f"\n⚡ Initialisation du Bon de Commande Pro Funnel : « {target_spec} »...\n")
        bdc_script = ROOT_DIR / "bdc" / "ppl-bdc.mjs"
        node_cmd = "node"
        res = subprocess.run([node_cmd, str(bdc_script), "pull", target_spec])
        sys.exit(res.returncode)

    # Cible domaine ou URL Pro Web
    clean_domain = target_spec.replace("http://", "").replace("https://", "").split("/")[0].strip()
    requested_path = ""
    try:
        if "://" in target_spec:
            parsed = urlparse(target_spec)
            requested_path = parsed.path
        elif "/" in target_spec:
            requested_path = "/" + "/".join(target_spec.split("/")[1:])
    except Exception:
        requested_path = ""

    print(f"\n⚡ Initialisation de la cible : « {clean_domain} » (chemin : « {requested_path or '/'} »)...\n")

    # Résolution via ppl_static.py resolve
    import ppl_static
    try:
        info = ppl_static.resolve(clean_domain, refresh=False, require=True)
    except SystemExit:
        sys.exit(1)

    if not info or not info.get("partner") or not info.get("type"):
        print(f"❌ Impossible de résoudre la cible « {clean_domain} ».")
        sys.exit(1)

    partner_id = info["partner"]
    site_type = info["type"]

    # RÈGLE CRITIQUE DOCTRINE GLOBALE :
    # "Pour les sites non-STATIC, seules les pages /pages/, /leads/, /cadeau/ sont vibecodables."
    if site_type != "STATIC":
        allowed_prefixes = ("/pages/", "/leads/", "/cadeau/")
        if requested_path and not any(requested_path.startswith(p) for p in allowed_prefixes):
            print(f"\n❌ [VETO DOCTRINE GLOBALE PRO WEB] Site non-STATIC détecté ({site_type}) :")
            print(f"   SEULES les pages commençant par /pages/, /leads/ ou /cadeau/ sont vibecodables !")
            print(f"   Le chemin demandé (« {requested_path} ») touche au Core ou au thème et ne doit PAS être vibecodé.\n")
            sys.exit(1)

    # Site STATIC Pro Web
    if site_type == "STATIC":
        print(f"📥 Téléchargement du miroir local pour « {clean_domain} »...")
        class DummyArgs:
            domain = clean_domain
            full = False
            raw = False
        ppl_static.cmd_pull(DummyArgs())

        # Découverte du slug partenaire
        partner_slug = "pan"
        partners_dir = ROOT_DIR / "storage" / "partners"
        if partners_dir.exists():
            for pf in partners_dir.glob("*.json"):
                try:
                    pdata = json.loads(pf.read_text(encoding="utf-8"))
                    if pdata.get("partner_id") == partner_id:
                        partner_slug = pdata.get("slug", "pan")
                        break
                except Exception:
                    pass

        actual_domain = info.get("domain") or clean_domain

        # Analyse des particularités du site (pages doublons)
        site_dir = ROOT_DIR / "sites" / actual_domain
        if not site_dir.exists():
            site_dir = Path.cwd() / "sites" / actual_domain

        duplicate_pairs = []
        if site_dir.exists():
            subdirs = [p for p in site_dir.iterdir() if p.is_dir() and not p.name.startswith(".")]
            for sd in subdirs:
                if (sd / "index.html").exists() and (site_dir / f"{sd.name}.html").exists():
                    duplicate_pairs.append(sd.name)

        dup_rules = ""
        if duplicate_pairs:
            dup_rules = (
                f"\n### ⚠️ Règle Double Arborescence HTML ({len(duplicate_pairs)} pages détectées) :\n"
                "Les sous-pages suivantes existent à la fois sous forme de dossier et de fichier .html :\n"
                + "\n".join(f"  - /{p}/index.html ET /{p}.html" for p in duplicate_pairs)
                + "\n👉 Si tu modifies l'une de ces pages, mets TOUJOURS à jour les deux fichiers de façon identique !\n"
            )

        rules_content = build_rules(actual_domain, partner_id, duplicate_pairs)

        # Écriture des consignes dans le workspace
        if site_dir.exists():
            (site_dir / "RULES.md").write_text(rules_content, encoding="utf-8")
            (site_dir / "CLAUDE.md").write_text(rules_content, encoding="utf-8")

            claude_dir = site_dir / ".claude"
            claude_dir.mkdir(parents=True, exist_ok=True)
            settings_path = claude_dir / "settings.json"
            
            # Copie des 26 règles de sécurité du repo si présentes, ou template complet
            repo_settings = ROOT_DIR / ".claude" / "settings.json"
            if repo_settings.exists():
                settings_path.write_text(repo_settings.read_text(encoding="utf-8"), encoding="utf-8")
            else:
                settings_path.write_text(json.dumps({
                    "permissions": {
                        "deny": [
                            "Bash(*--go*)", "Bash(*--g*)", "Bash(*--yes*)", "Bash(*--y*)",
                            "Bash(script *)", "Bash(*xargs*)", "Bash(*expect*)", "Bash(*unbuffer*)", "Bash(*tmux*)",
                            "Read(~/.pro-web-static/**)", "Bash(*token.json*)", "Bash(*.pro-web-static*)",
                            "Bash(curl*pro-web.propulse-lab.com*)", "Bash(python*-c*)",
                            "Edit(*.py)", "Edit(**/*.py)", "Write(*.py)", "Write(**/*.py)",
                            "Edit(**/*.sh)", "Write(**/*.sh)", "Bash(*.sh*)", "Bash(perl*)",
                            "Bash(node*-e*)", "Bash(ruby*)", "Edit(.claude/**)", "Write(.claude/**)"
                        ]
                    }
                }, indent=2), encoding="utf-8")

        print(f"\n✅ Workspace configuré avec succès dans : {site_dir}")
        print("   📄 RULES.md généré (prêt à être copié dans Grok, Cursor, ChatGPT)")
        print("   🛡️  26 Garde-fous Claude Code actifs (.claude/settings.json)")
        print(f"\n🚀 Commandes opérationnelles (depuis la racine du kit) :")
        print(f"   {proweb_env.PY_CMD} ppl.py static preview {actual_domain}              # tester sur http://localhost:8080")
        print(f"   {proweb_env.PY_CMD} ppl.py static push {actual_domain}                 # vérifier le diff (dry-run)")
        print(f"   {proweb_env.PY_CMD} ppl.py static push {actual_domain} --go --yes      # publication agent (après approbation chat)\n")
        sys.exit(0)

    # Si WordPress / ai-child
    print(f"\n🧩 Site WordPress détecté ({clean_domain}) :")
    print("   • Prérequis Réseau & Connexion (Doctrine Globale) :")
    print("   1. Autoriser votre IP au préalable sur : https://pro-ips.propulse-lab.com (1 fois par mois)")
    print(f"   2. Connexion admin sur : https://www-admin.{clean_domain}/wp-login.php")
    print("      - Si votre email est celui de l'organisation : cliquez directement sur 'Se connecter avec Google'")
    print("      - Si vous n'avez pas d'email @organisation : demandez la création préalable de votre compte")
    print(f"   3. Générer votre clé en 1 clic : https://www-admin.{clean_domain}/wp-admin/authorize-application.php?app_name=agent-api\n")
    sys.exit(0)


def main():
    proweb_env.setup_console()
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(BANNER)
        sys.exit(0)

    cmd = args[0].lower()
    sub_args = args[1:]

    if cmd == "doctor":
        class DummyArgs:
            pass
        import ppl_static
        ppl_static.cmd_doctor(DummyArgs())
        sys.exit(0)

    elif cmd == "login":
        force_paste = "--paste" in sub_args
        proweb_auth.run(force_paste=force_paste)
        sys.exit(0)

    elif cmd == "whoami":
        cmd_whoami()

    elif cmd == "init":
        cmd_init(sub_args)

    elif cmd == "static":
        import ppl_static
        sys.argv = ["ppl_static.py"] + sub_args
        ppl_static.main()

    elif cmd == "bdc":
        bdc_script = ROOT_DIR / "bdc" / "ppl-bdc.mjs"
        res = subprocess.run(["node", str(bdc_script)] + sub_args)
        sys.exit(res.returncode)

    elif cmd == "acq":
        acq_script = ROOT_DIR / "bin" / "ppl-acq.mjs"
        res = subprocess.run(["node", str(acq_script)] + sub_args)
        sys.exit(res.returncode)

    elif cmd == "platform":
        platform_script = ROOT_DIR / "bin" / "ppl-platform.mjs"
        res = subprocess.run(["node", str(platform_script)] + sub_args)
        sys.exit(res.returncode)

    elif cmd == "doc":
        compile_script = ROOT_DIR / "compiler" / "compile.mjs"
        res = subprocess.run(["node", str(compile_script)] + sub_args)
        sys.exit(res.returncode)

    elif cmd == "update":
        code = cmd_update(sub_args)
        sys.exit(code)

    else:
        print(f"❌ Commande inconnue : « {cmd} »")
        print(BANNER)
        sys.exit(1)


if __name__ == "__main__":
    main()
