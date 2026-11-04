#!/usr/bin/env python3
"""
bootstrap.py — Initialisation et mise à jour du socle Pro-Pilot dans l'environnement partenaire.
Synchronise le socle pro-pilot-propulse dans .pro-pilot/ (en HTTPS ou via le socle local PPL).
"""
import os
import subprocess
import sys
from pathlib import Path

SOCLE_HTTPS_REPO = "https://github.com/pro-pilote/pro-pilot-propulse.git"
SOCLE_DIR = Path(".pro-pilot")


def run(cmd, check=True):
    print(f"-> {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)


def main():
    root = Path(__file__).resolve().parent
    os.chdir(root)

    # 1. Détection environnement PPL interne : si le socle adjacent existe
    local_socle = (root.parent / "pro-pilot-propulse").resolve()
    if local_socle.exists() and (local_socle / "regles").exists() and local_socle != root:
        print(f"⚡ Mode interne Propulse Lab : liaison vers le socle local {local_socle}")
        if not SOCLE_DIR.exists():
            try:
                os.symlink(local_socle, SOCLE_DIR)
            except OSError:
                run(["git", "clone", "--depth", "1", str(local_socle), str(SOCLE_DIR)])
        print("✅ Socle Pro-Pilot lié avec succès.")
        return 0

    # 2. Mode Partenaire : clone ou pull HTTPS
    if not SOCLE_DIR.exists():
        print("Clonage du socle Pro-Pilot dans .pro-pilot/...")
        run(["git", "clone", "--depth", "1", SOCLE_HTTPS_REPO, str(SOCLE_DIR)])
    else:
        print("Mise à jour du socle Pro-Pilot...")
        run(["git", "-C", str(SOCLE_DIR), "pull", "--ff-only"])

    print("✅ Socle Pro-Pilot synchronisé avec succès.")
    return 0


if __name__ == "__main__":
    main()
