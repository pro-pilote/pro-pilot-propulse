#!/usr/bin/env python3
"""
bootstrap.py — Initialisation et mise à jour du socle Pro-Pilot dans l'environnement partenaire.
Clone ou met à jour le socle pro-pilot-propulse dans .pro-pilot/ et exécute le rendu des règles.
"""
import os
import subprocess
import sys
from pathlib import Path

SOCLE_REPO = "git@github.com:pro-pilote/pro-pilot-propulse.git"
SOCLE_DIR = Path(".pro-pilot")

def run(cmd, check=True):
    print(f"-> {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)

def main():
    root = Path(__file__).resolve().parent
    os.chdir(root)

    if not SOCLE_DIR.exists():
        print("Clonage du socle Pro-Pilot dans .pro-pilot/...")
        run(["git", "clone", "--depth", "1", SOCLE_REPO, str(SOCLE_DIR)])
    else:
        print("Mise à jour du socle Pro-Pilot...")
        run(["git", "-C", str(SOCLE_DIR), "pull", "--ff-only"])

    ppl_script = SOCLE_DIR / "tools" / "ppl.py"
    if ppl_script.exists():
        print("Génération des règles et documentation rendue...")
        run([sys.executable, str(ppl_script), "render"])
    
    print("✅ Bootstrap Pro-Pilot terminé avec succès.")

if __name__ == "__main__":
    main()
