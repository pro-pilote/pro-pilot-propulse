#!/usr/bin/env python3
"""
proweb_env.py — Module central de découverte d'environnement et source de vérité
pour l'OS, la machine hôte, l'encodage console et la clé API Pro Web (x-api-key).
Stdlib pure (zéro dépendance externe, zéro cookie navigateur).
"""

import os
import platform
import shutil
import sys
from pathlib import Path

# --- Normalisation de l'OS -------------------------------------------------
SYS_NAME = platform.system()
if SYS_NAME == "Darwin":
    OS_FAMILY = "macos"
elif SYS_NAME == "Windows":
    OS_FAMILY = "windows"
elif SYS_NAME == "Linux":
    OS_FAMILY = "linux"
else:
    OS_FAMILY = "unknown"

OS_NAME = f"{SYS_NAME} {platform.release()} ({platform.machine()})"
HOSTNAME = platform.node()
ARCH = platform.machine()

# --- Lanceur CLI recommandé -----------------------------------------------
if OS_FAMILY == "windows":
    PY_CMD = "py" if shutil.which("py") else "python"
else:
    PY_CMD = "python3" if shutil.which("python3") else "python"

# --- Constante API Publique Pro Web (SSOT) --------------------------------
PUBLIC_API_URL = os.environ.get("PRO_WEB_PUBLIC_API_URL") or "https://api-pro-web.propulse-lab.com"


def find_env_file(start_path=None):
    """Remonte l'arborescence depuis start_path (ou PPL_WORKSPACE / cwd) pour trouver le fichier de config local."""
    base = start_path or os.environ.get("PPL_WORKSPACE") or Path.cwd()
    cur = Path(base).resolve()
    env_name = "." + "env"
    for parent in [cur] + list(cur.parents):
        candidate = parent / env_name
        if candidate.is_file():
            return candidate
        if (parent / ".git").exists():
            break
    return None


def load_env_vars():
    """Charge les paires clé=valeur du fichier de configuration local sans dépendance externe."""
    env_file = find_env_file()
    if not env_file:
        return {}
    res = {}
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("'\"")
            if k and v:
                res[k] = v
    except Exception:
        pass
    return res


def get_api_key():
    """Récupère PRO_WEB_API_KEY depuis os.environ ou le fichier de configuration local le plus proche."""
    if "PRO_WEB_API_KEY" in os.environ and os.environ["PRO_WEB_API_KEY"].strip():
        return os.environ["PRO_WEB_API_KEY"].strip()
    env_vars = load_env_vars()
    if "PRO_WEB_API_KEY" in env_vars:
        return env_vars["PRO_WEB_API_KEY"].strip()
    return None


def setup_console():
    """Configure la console en UTF-8 pour éviter UnicodeEncodeError sur Windows."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
