#!/usr/bin/env python3
"""
proweb_env.py — Module central de découverte d'environnement et source de vérité
pour l'OS, la machine hôte, l'encodage console et le chemin du token Pro Web.
Stdlib pure (zéro dépendance externe).
"""

import base64
import json
import os
import platform
import shutil
import sys
import time
from datetime import datetime, timezone
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

# --- Chemins et constantes Pro Web (SSOT) ----------------------------------
DOMAIN = "pro-web.propulse-lab.com"
TOKEN_DIR = Path.home() / ".pro-web-static"
TOKEN_PATH = TOKEN_DIR / "token.json"


def load_token():
    """Charge le payload JSON du token depuis TOKEN_PATH ou None si absent/invalide."""
    if not TOKEN_PATH.exists():
        return None
    try:
        return json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def setup_console():
    """Configure la console en UTF-8 pour éviter UnicodeEncodeError sur Windows."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def get_chrome_cookies_path():
    """Retourne le chemin standard de la base SQLite des cookies Chrome selon l'OS."""
    home = Path.home()
    if OS_FAMILY == "macos":
        return home / "Library/Application Support/Google/Chrome/Default/Cookies"
    elif OS_FAMILY == "windows":
        appdata = os.environ.get("LOCALAPPDATA")
        if appdata:
            p1 = Path(appdata) / "Google/Chrome/User Data/Default/Network/Cookies"
            if p1.exists():
                return p1
            return Path(appdata) / "Google/Chrome/User Data/Default/Cookies"
        return home / "AppData/Local/Google/Chrome/User Data/Default/Network/Cookies"
    elif OS_FAMILY == "linux":
        return home / ".config/google-chrome/Default/Cookies"
    return None


def get_auth_strategy():
    """Détermine la stratégie d'authentification recommandée selon l'environnement."""
    if OS_FAMILY == "macos":
        p = get_chrome_cookies_path()
        if p and p.exists():
            return "chrome_keychain"
        return "paste"
    # Windows & Linux : mode guidé / paste par défaut (Chrome 127+ App-Bound Encryption sur Windows)
    return "paste"


def parse_jwt_payload(jwt_token):
    """Décode la charge utile d'un JWT (partie 2) sans vérification cryptographique."""
    if not jwt_token or not isinstance(jwt_token, str):
        return None
    parts = jwt_token.strip().split(".")
    if len(parts) < 2:
        return None
    payload_b64 = parts[1]
    # Remplir le padding base64 si nécessaire
    rem = len(payload_b64) % 4
    if rem > 0:
        payload_b64 += "=" * (4 - rem)
    try:
        decoded_bytes = base64.urlsafe_b64decode(payload_b64.encode("ascii"))
        return json.loads(decoded_bytes.decode("utf-8", errors="replace"))
    except Exception:
        return None


def check_token_status():
    """Vérifie l'état et l'expiration du token local ~/.pro-web-static/token.json."""
    if not TOKEN_PATH.exists():
        return {
            "exists": False,
            "valid": False,
            "expired": False,
            "email": None,
            "expires_at": None,
            "remaining_seconds": 0,
            "path": str(TOKEN_PATH)
        }
    try:
        data = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
        bearer = data.get("bearer", "")
        if not bearer:
            return {
                "exists": True,
                "valid": False,
                "expired": True,
                "email": None,
                "expires_at": None,
                "remaining_seconds": 0,
                "path": str(TOKEN_PATH)
            }
        payload = parse_jwt_payload(bearer)
        if not payload:
            return {
                "exists": True,
                "valid": True,
                "expired": False,
                "email": None,
                "expires_at": None,
                "remaining_seconds": None,
                "path": str(TOKEN_PATH)
            }
        exp = payload.get("exp")
        email = payload.get("email") or payload.get("name")
        now = int(time.time())
        if exp and isinstance(exp, (int, float)):
            expired = now >= exp
            rem = max(0, int(exp - now))
            exp_iso = datetime.fromtimestamp(exp, timezone.utc).isoformat()
            return {
                "exists": True,
                "valid": not expired,
                "expired": expired,
                "email": email,
                "expires_at": exp_iso,
                "remaining_seconds": rem,
                "path": str(TOKEN_PATH)
            }
        return {
            "exists": True,
            "valid": True,
            "expired": False,
            "email": email,
            "expires_at": None,
            "remaining_seconds": None,
            "path": str(TOKEN_PATH)
        }
    except Exception:
        return {
            "exists": True,
            "valid": False,
            "expired": True,
            "email": None,
            "expires_at": None,
            "remaining_seconds": 0,
            "path": str(TOKEN_PATH)
        }
