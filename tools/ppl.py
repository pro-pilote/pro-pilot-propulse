#!/usr/bin/env python3
"""
ppl — CLI Unifié de la Suite Propulse Lab Pro-Pilot.

Conception & Architecture : Medi Chabrol · Propulse Lab
Doctrine Globale : 100% API Key (x-api-key), Cloisonnement Multi-Tenant, Zero Extrapolation.

Usage :
  python ppl.py doctor
  python ppl.py render
  python ppl.py static <pull|preview|push|add|rm|set-home|replace|ls|resolve> [domaine]
"""

import os
import re
import sys
from pathlib import Path

import proweb_env

ROOT_DIR = Path(__file__).resolve().parent

BANNER = """
========================================================================
⚡ PROPULSE LAB · PRO PILOTE (ppl)
Architecture & Conception : Medi Chabrol
========================================================================

Commandes Disponibles :
  • static     → Objets & Sites Pro Web (API Publique S3 / CloudFront)
  • render     → Génération optionnelle de la doc rendue (.pro-pilot/rendered/)
  • doctor     → Diagnostic de l'OS, de la machine et de la clé API (PRO_WEB_API_KEY)

Usage :
  ./ppl static ls <domaine>
  ./ppl static pull <domaine>
  ./ppl static preview <domaine>
  ./ppl static push <domaine>
  ./ppl doctor
"""


def cmd_render(sub_args=None):
    """Génère la documentation rendue dans .pro-pilot/rendered/."""
    partner_dir = Path(os.environ.get("PPL_WORKSPACE") or os.getcwd()).resolve()
    socle_dir = ROOT_DIR.parent
    if (partner_dir / ".pro-pilot").exists():
        socle_dir = partner_dir / ".pro-pilot"

    version = "1.0.0"
    if (socle_dir / "VERSION").exists():
        version = (socle_dir / "VERSION").read_text(encoding="utf-8").strip()

    rendered_dir = socle_dir / "rendered"
    rendered_dir.mkdir(parents=True, exist_ok=True)

    vars_dict = {}
    var_files = list(partner_dir.glob("outils/*/variables.md"))
    var_re = re.compile(r"^\s*-\s*`?ppl\.([a-zA-Z0-9_]+)`?\s*:\s*`?([^`\n]+?)`?\s*$", re.MULTILINE)
    for vf in var_files:
        content = vf.read_text(encoding="utf-8")
        for match in var_re.finditer(content):
            vars_dict[match.group(1).strip()] = match.group(2).strip()

    def replace_vars(text):
        def repl(m):
            k = m.group(1)
            return vars_dict.get(k, m.group(0))
        return re.sub(r"\[\[ppl\.([a-zA-Z0-9_]+)\]\]", repl, text)

    for section in ["outils", "regles"]:
        src_sec = socle_dir / section
        dst_sec = rendered_dir / section
        if src_sec.exists():
            for src_file in src_sec.rglob("*.md"):
                rel = src_file.relative_to(src_sec)
                target = dst_sec / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                raw_text = src_file.read_text(encoding="utf-8")
                target.write_text(replace_vars(raw_text), encoding="utf-8")

    router_file = socle_dir / "ROUTER.md"
    if router_file.exists():
        (rendered_dir / "ROUTER.md").write_text(replace_vars(router_file.read_text(encoding="utf-8")), encoding="utf-8")

    print(f"✅ Rendu terminé dans {rendered_dir} (v{version})")
    return 0


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

    elif cmd == "static":
        import ppl_static
        sys.argv = ["ppl_static.py"] + sub_args
        ppl_static.main()

    elif cmd == "render":
        code = cmd_render(sub_args)
        sys.exit(code)

    else:
        print(f"❌ Commande inconnue : « {cmd} »")
        print(BANNER)
        sys.exit(1)


if __name__ == "__main__":
    main()
