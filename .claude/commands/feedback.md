# Commande /feedback — Enregistrement et Synchronisation des Retours Partenaires

Cette commande permet a Claude d'enregistrer de facon autonome les retours d'experience, les corrections, les nouvelles fiches produits et les regles edifiees au cours des sessions, et de les synchroniser sur le depot GitHub du partenaire sans aucune manipulation technique de la part de l'utilisateur.

---

## 1. Declencheurs

Cette commande est executee :
- Soit a la demande explicite de l'utilisateur via `/feedback <description du retour>`
- Soit de maniere proactive par Claude des qu'un utilisateur formule une correction, une regle specifique, un retour sur un style ou une nouvelle mention legale.

---

## 2. Matrice d'Aiguillage des Retours

Selon la nature du retour, Claude met a jour le fichier correspondant :

| Nature du retour | Fichier cible | Format de mise a jour |
|---|---|---|
| **Regle editoriale / mise en page** | `outils/pro-web-uploader/specificites.md` | Ajouter une section `### [Titre de la regle]` avec le contexte et la consigne |
| **Erreur technique / piege API** | `outils/pro-web-uploader/erreurs-connues.md` | Ajouter une entree `### [Symptome]` + `Solution appliquee` |
| **Charte / couleur / typographie** | `donnees-business/design-system.md` | Mettre a jour la palette ou la typographie dans la section correspondante |
| **Nouveau produit / offre** | `donnees-business/<sku>/fiche-produit.md` | Creer ou completer la fiche produit standardisee |
| **Nouveau domaine / websiteId** | `outils/pro-web-uploader/variables.md` | Ajouter la ligne dans le tableau des sites |

---

## 3. Garde-fous de Securite & Perimetre Autorise

Pour proteger l'integrite du harnais :
1. **Perimetre autorise (Allowlist)** :
   - Uniquement les fichiers sous `donnees-business/**` et `outils/**/`.
2. **Perimetre strictement interdit (Denylist)** :
   - Ne jamais modifier ni committer de scripts `.sh`, `.py`, `.js`.
   - Ne jamais modifier `.github/**`, `regles/**`, `ROUTER.md`, `.claude/commands/`.
   - Ne jamais committer de pages `*.html`, `*.htm`, `.tmp/`, `tmp/` ni de fichiers `.env`.

---

## 4. Execution Silencieuse du Commit via le Portail Pro-Pilot

Claude execute directement l'envoi securise vers le portail Pro-Pilot sans jamais dependre d'un binaire Git ni d'un compte GitHub local :

```bash
set -a; source .env; set +a
python3 - <<'PY'
import os, sys, json, urllib.request

token = os.environ.get("PRO_PILOT_WRITE_TOKEN", "").strip()
if not token:
    print("Erreur: PRO_PILOT_WRITE_TOKEN manquant dans .env")
    sys.exit(1)

path = sys.argv[1] if len(sys.argv) > 1 else "outils/pro-web-uploader/specificites.md"
message = sys.argv[2] if len(sys.argv) > 2 else f"docs(partenaire): mise a jour {path}"

try:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
except Exception as e:
    print(f"Erreur lecture fichier {path}: {e}")
    sys.exit(1)

req = urllib.request.Request(
    "https://pro-pilot.propulse-lab.com/api/feedback",
    data=json.dumps({"path": path, "content": content, "message": message}).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print(f"Succes: {res.get('path')} synchronise sur GitHub ({res.get('repo')}) - commit {res.get('commitSha', '')[:7]}")
except urllib.error.HTTPError as err:
    print(f"Erreur HTTP {err.code}: {err.read().decode('utf-8')}")
    sys.exit(1)
PY "<chemin_du_fichier>" "<message_de_commit>"
```

---

## 5. Confirmation Utilisateur

Une fois l'appel reussi, Claude confirme sobrement a l'utilisateur :
*« Votre preference sur [sujet] a ete enregistree dans [fichier] et synchronisee sur votre espace GitHub partagé. Elle sera automatiquement prise en compte lors de nos prochaines sessions. »*
