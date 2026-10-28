#!/usr/bin/env python3
"""
Compilateur Fail-Closed Pro-Pilot (Socle Propulse Lab -> Repo Partenaire)
- Lit les variables `[[ppl.<cle>]]` définies dans lerepo partenaire (`variables.md`).
- Remplit les templates à trous de `pro-pilot-propulse` uniquement pour les outils activés chez ce partenaire.
- Écrit `outils/<outil>/guide-propulse.md` (sans jamais toucher à `variables.md`, `specificites.md`, `erreurs-connues.md`, ni `donnees-business/`).
- Synchronise `ROUTER.md`, `getting-started/`, `regles/` et `tools/`.
- Échoue immédiatement (exit 1) si un trou `[[ppl.*]]` reste non résolu.
"""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"\[\[ppl\.([a-zA-Z0-9_]+)\]\]")
KV_RE = re.compile(r"^\s*-\s*`?ppl\.([a-zA-Z0-9_]+)`?\s*:\s*`?([^`\n]+?)`?\s*$", re.MULTILINE)

def parse_variables_md(text: str) -> dict:
    vars_dict = {}
    for match in KV_RE.finditer(text):
        vars_dict[match.group(1).strip()] = match.group(2).strip()
    return vars_dict

def render_template(template_text: str, variables: dict, source_label: str) -> str:
    missing = []
    def repl(match):
        key = match.group(1)
        if key not in variables or variables[key] == "":
            missing.append(key)
            return match.group(0)
        return variables[key]
    rendered = PLACEHOLDER_RE.sub(repl, template_text)
    if missing:
        raise ValueError(f"[FAIL-CLOSED] Variables manquantes {sorted(set(missing))} lors du rendu de {source_label}")
    header = "<!-- FICHIER GÉNÉRÉ AUTOMATIQUEMENT PAR PRO-PILOT-PROPULSE — NE PAS ÉDITER À LA MAIN -->\n\n"
    return header + rendered.strip() + "\n"

def compile_partner(socle_dir: Path, partner_dir: Path):
    version = (socle_dir / "VERSION").read_text(encoding="utf-8").strip()
    # Collecter toutes les variables définies dans outils/*/variables.md du partenaire
    merged_vars = {}
    outils_partner_dir = partner_dir / "outils"
    if not outils_partner_dir.exists():
        raise RuntimeError(f"Dossier outils/ introuvable dans {partner_dir}")

    active_tools = sorted([d.name for d in outils_partner_dir.iterdir() if d.is_dir()])
    for tool_slug in active_tools:
        v_file = outils_partner_dir / tool_slug / "variables.md"
        if v_file.exists():
            merged_vars.update(parse_variables_md(v_file.read_text(encoding="utf-8")))

    generated_hashes = []

    # 1. Compiler uniquement les outils activés chez ce partenaire
    for tool_slug in active_tools:
        socle_tool_readme = socle_dir / "outils" / tool_slug / "README.md"
        if not socle_tool_readme.exists():
            continue
        rendered_guide = render_template(
            socle_tool_readme.read_text(encoding="utf-8"),
            merged_vars,
            f"outils/{tool_slug}/README.md"
        )
        target_guide = outils_partner_dir / tool_slug / "guide-propulse.md"
        target_guide.write_text(rendered_guide, encoding="utf-8")
        # Supprimer l'ancien README.md de lien s'il existait
        old_readme = outils_partner_dir / tool_slug / "README.md"
        if old_readme.exists():
            old_readme.unlink()
        rel = str(target_guide.relative_to(partner_dir))
        generated_hashes.append({"file": rel, "checksum": "sha256-" + hashlib.sha256(rendered_guide.encode("utf-8")).hexdigest()})

    # 2. Compiler ROUTER.md à la racine du partenaire
    rendered_router = render_template(
        (socle_dir / "ROUTER.md").read_text(encoding="utf-8"),
        merged_vars,
        "ROUTER.md"
    )
    (partner_dir / "ROUTER.md").write_text(rendered_router, encoding="utf-8")
    generated_hashes.append({"file": "ROUTER.md", "checksum": "sha256-" + hashlib.sha256(rendered_router.encode("utf-8")).hexdigest()})

    # 3. Synchroniser getting-started/, regles/ et tools/
    for folder in ["getting-started", "regles", "tools"]:
        src_folder = socle_dir / folder
        dst_folder = partner_dir / folder
        if dst_folder.exists():
            shutil.rmtree(dst_folder)
        shutil.copytree(src_folder, dst_folder)
        for p in sorted(dst_folder.rglob("*")):
            if p.is_file():
                rel = str(p.relative_to(partner_dir))
                generated_hashes.append({"file": rel, "checksum": "sha256-" + hashlib.sha256(p.read_bytes()).hexdigest()})

    # 4. Écrire le manifeste de verrouillage generated.lock
    lock_file = partner_dir / "generated.lock.json"
    lock_data = {
        "socle_version": version,
        "partner_name": merged_vars.get("partner_name"),
        "partner_id": merged_vars.get("partner_id"),
        "active_tools": active_tools,
        "generated_files": generated_hashes,
    }
    lock_file.write_text(json.dumps(lock_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] {partner_dir.name} compilé avec succès (socle v{version}, {len(active_tools)} outils activés, 0 trou non résolu).")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 compile_partner_repo.py <socle_dir> <partner_dir>")
        sys.exit(2)
    compile_partner(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
