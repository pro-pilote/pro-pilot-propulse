#!/usr/bin/env python3
"""outils/feedback_push.py — Envoi d'une note ou règle partenaire vers la boîte de réception GitHub partagée."""
import os
import sys
import json
import urllib.request
import urllib.error

def load_env():
    if os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

def main():
    load_env()
    token = os.environ.get("PRO_PILOT_WRITE_TOKEN", "").strip()
    if not token:
        print("Erreur : PRO_PILOT_WRITE_TOKEN manquant dans l'environnement ou .env")
        sys.exit(1)

    if len(sys.argv) < 3:
        print("Usage : python3 outils/feedback_push.py \"<sujet>\" \"<contenu_ou_chemin>\" [categorie]")
        sys.exit(1)

    subject = sys.argv[1].strip()
    content_raw = sys.argv[2].strip()
    category = sys.argv[3].strip() if len(sys.argv) > 3 else "editorial"

    content = content_raw
    if os.path.isfile(content_raw):
        try:
            with open(content_raw, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Erreur lecture fichier {content_raw} : {e}")
            sys.exit(1)

    payload = {
        "subject": subject,
        "content": content,
        "category": category,
    }

    url = "https://pro-pilot.propulse-lab.com/api/feedback"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Pro-Pilot-Feedback-Push",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"Succès : retour consigné dans {data.get('path')} (commit {str(data.get('commitSha', ''))[:7]})")
    except urllib.error.HTTPError as err:
        err_msg = err.read().decode("utf-8")
        print(f"Erreur HTTP {err.code} : {err_msg}")
        sys.exit(1)
    except Exception as e:
        print(f"Erreur connexion : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
