#!/usr/bin/env python3
"""
proweb_auth.py — récupère un token d'auth pour l'API pro-web.propulse-lab.com
depuis ton navigateur Chrome (macOS) ou via assistant guidé (Windows/Linux/tiers),
et l'écrit dans ~/.pro-web-static/token.json.

Ne lit RIEN d'autre que les cookies du domaine pro-web.propulse-lab.com. Ne
contient aucune clé partagée : c'est TA session (tu dois être connecté sur
https://pro-web.propulse-lab.com) qui fournit le token, donc tu n'as accès
qu'à ce que ton propre compte peut voir sur la plateforme.

Usage recommandé :
    python ppl.py login           # Auto sur macOS/Chrome, guidé sur Windows/Linux
    python ppl.py login --paste   # Force le mode saisie / collage manuel

Exécution directe tolérée :
    python proweb_auth.py [--paste]
"""

import argparse
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import proweb_env as env

env.setup_console()

class CookieDecryptError(RuntimeError):
    """Le cookie est présent en base mais son déchiffrement a échoué."""


DOMAIN = env.DOMAIN
CHROME_COOKIES = env.get_chrome_cookies_path()
SALT = b"saltysalt"
ITERATIONS = 1003
IV = b" " * 16
TOKEN_PATH = env.TOKEN_PATH


def get_chrome_key():
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    except ImportError:
        raise RuntimeError(f"dépendance manquante sur macOS : {env.PY_CMD} -m pip install cryptography")

    result = subprocess.run(
        ["security", "find-generic-password", "-w", "-s", "Chrome Safe Storage"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "impossible de lire la clé Chrome Safe Storage depuis le trousseau macOS "
            "(autorise l'accès si macOS te le demande, puis relance)"
        )
    password = result.stdout.strip().encode("utf-8")
    kdf = PBKDF2HMAC(algorithm=hashes.SHA1(), length=16, salt=SALT, iterations=ITERATIONS)
    return kdf.derive(password)


def decrypt_value(encrypted, key):
    if not encrypted:
        return ""
    try:
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    except ImportError:
        raise RuntimeError(f"dépendance manquante sur macOS : {env.PY_CMD} -m pip install cryptography")

    if encrypted[:3] in (b"v10", b"v11"):
        encrypted = encrypted[3:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(IV))
    decryptor = cipher.decryptor()
    padded = decryptor.update(encrypted) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    try:
        decrypted = unpadder.update(padded) + unpadder.finalize()
    except ValueError:
        decrypted = padded
    if len(decrypted) > 32 and any(b < 0x20 or b > 0x7E for b in decrypted[:32]):
        decrypted = decrypted[32:]
    return decrypted.decode("utf-8", errors="replace")


def read_cookies():
    if not CHROME_COOKIES or not CHROME_COOKIES.exists():
        raise RuntimeError(f"base de cookies Chrome introuvable : {CHROME_COOKIES}")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        shutil.copy2(CHROME_COOKIES, tmp_path)
        key = get_chrome_key()
        conn = sqlite3.connect(tmp_path)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT name, value, encrypted_value FROM cookies "
                "WHERE host_key = ? OR host_key = ? OR host_key LIKE ?",
                (DOMAIN, f".{DOMAIN}", f"%.{DOMAIN}"),
            )
            cookies = {}
            for name, value, encrypted in cur.fetchall():
                if name in cookies:
                    continue
                if value:
                    cookies[name] = value
                elif encrypted:
                    try:
                        cookies[name] = decrypt_value(encrypted, key)
                    except Exception as e:
                        if name == "userCredential":
                            raise CookieDecryptError(str(e)) from e
                        print(f"  ⚠️  impossible de déchiffrer le cookie {name}: {e}", file=sys.stderr)
            return cookies
        finally:
            conn.close()
    finally:
        tmp_path.unlink(missing_ok=True)


def prompt_paste_token():
    """Mode guidé pour Windows, Linux ou navigateurs tiers."""
    print(f"\n💻 Système détecté : {env.OS_NAME} (Machine: {env.HOSTNAME})")
    print(f"🔑 Mode Authentification Guidée Pro Web\n")
    print(f"1. Connecte-toi sur https://{DOMAIN} dans ton navigateur.")
    print("2. Ouvre les Outils de développement (Touche F12 ou Ctrl+Shift+I / Cmd+Opt+I).")
    print("3. Onglet 'Application' (ou 'Stockage') > 'Cookies' > clique sur https://pro-web.propulse-lab.com.")
    print("4. Copie la valeur du cookie nommé 'userCredential' (c'est un long JWT commençant par ey...).")
    print("-" * 70)
    raw = input("Colle la valeur du cookie 'userCredential' ici :\n> ").strip()
    if not raw:
        raise RuntimeError("Aucune valeur saisie, token non créé.")
    if raw.startswith("userCredential="):
        raw = raw[len("userCredential="):].strip()
    val = raw.strip("\"' ;")
    return {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bearer": val,
        "auth_cookie": "",
        "g_state_cookie": "",
    }


def fetch_token(retries=2, force_paste=False):
    """Lit les cookies ou déclenche la saisie guidée.
    Appelé automatiquement par ppl_static.py en cas de rafraîchissement lazy."""
    if not force_paste and env.OS_FAMILY == "macos":
        for attempt in range(retries):
            try:
                cookies = read_cookies()
                bearer = cookies.get("userCredential", "")
                if not bearer:
                    raise RuntimeError(
                        f"pas de cookie 'userCredential' — connecte-toi (login Google) sur https://{DOMAIN}"
                    )
                return {
                    "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "bearer": bearer,
                    "auth_cookie": cookies.get("auth", ""),
                    "g_state_cookie": cookies.get("g_state", ""),
                }
            except CookieDecryptError as e:
                if attempt + 1 == retries:
                    raise RuntimeError(
                        f"le cookie 'userCredential' est présent mais n'a pas pu être déchiffré, "
                        f"même après {retries} essais ({e}) — ferme et rouvre Chrome, ou lance avec --paste"
                    )
            except RuntimeError:
                if attempt + 1 == retries:
                    raise
    # Si Windows, Linux, ou macOS avec --paste
    return prompt_paste_token()


def run(force_paste=False):
    """Point d'entrée principal pour initialiser le token Pro Web.
    Appelé par ppl.py login ou en CLI direct."""
    if force_paste or env.OS_FAMILY != "macos":
        try:
            payload = prompt_paste_token()
        except RuntimeError as e:
            sys.exit(f"❌ {e}.")
    else:
        print(f"→ lecture des cookies Chrome pour {DOMAIN} ({env.OS_NAME})…")
        try:
            payload = fetch_token(retries=2)
        except RuntimeError as e:
            print(f"⚠️ Extraction automatique impossible ({e}). Passage en mode guidé :", file=sys.stderr)
            try:
                payload = prompt_paste_token()
            except RuntimeError as err:
                sys.exit(f"❌ {err}.")

    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Token écrit avec succès → {TOKEN_PATH}")
    return payload


def main():
    parser = argparse.ArgumentParser(description="Authentification Pro Web Multi-OS")
    parser.add_argument("--paste", action="store_true", help="Force le mode saisie/collage manuel du JWT")
    args = parser.parse_args()
    run(force_paste=args.paste)


if __name__ == "__main__":
    main()
