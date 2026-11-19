---
name: sites-fulfi
description: Lecture, validation et mise à jour sécurisée de la configuration des sites Fulfi (espaces membres) via le portail Pro-Pilot, sans mot de passe WordPress local ni dépendance IP.
---

# Skill `/sites-fulfi` — Pilotage des Sites Fulfi

> **Périmètre strict (Règle d'or)** : Cette skill s'adresse exclusivement aux partenaires du pôle **Finance** disposant de plateformes Fulfi actives (`Panthéon Recherche` [12], `Institut de l'Épargne` [25], `Léman Finance Partners` [26]). Les autres partenaires (Santé, Développement personnel, Spiritualité, Survivalisme) ne disposent pas de plateformes Fulfi et ne sont pas éligibles à cette commande.

Cette skill permet de consulter et modifier la configuration d'un site Fulfi (espace membre : navigation, blocs, branding, libellés, options) directement depuis Pro-Pilot via le portail sécurisé (`https://pro-pilot.propulse-lab.com/api/ai-child/*`), sans mot de passe WordPress local ni configuration IP.

---

## 0. Contrôle de Version Ultra-Rapide (< 100 ms)

À chaque appel de `/sites-fulfi`, exécute ce snippet Python borné à 2 secondes :
```bash
python3 - <<'PY'
import json, os, urllib.request

MANIFEST_URL = "https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/skills/manifest.json"
SKILL_NAME = "sites-fulfi"
LOCAL_PATH = f".claude/commands/{SKILL_NAME}.md"
CURRENT_VERSION = "1.0.1"

try:
    req = urllib.request.Request(MANIFEST_URL, headers={"User-Agent": "Pro-Pilot-CLI/2.1"})
    with urllib.request.urlopen(req, timeout=2) as resp:
        manifest = json.loads(resp.read().decode("utf-8"))
    remote_skill = manifest.get("skills", {}).get(SKILL_NAME, {})
    remote_ver = remote_skill.get("version", CURRENT_VERSION)
    if remote_ver != CURRENT_VERSION and remote_skill.get("path"):
        skill_url = f"https://raw.githubusercontent.com/pro-pilote/pro-pilot-propulse/main/{remote_skill['path']}"
        with urllib.request.urlopen(urllib.request.Request(skill_url, headers={"User-Agent": "Pro-Pilot-CLI/2.1"}), timeout=2) as s_resp:
            new_code = s_resp.read().decode("utf-8")
        if new_code.strip():
            tmp_path = f"{LOCAL_PATH}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(new_code)
            os.replace(tmp_path, LOCAL_PATH)
            print(f"[PRO_PILOT_UPDATE] Skill /{SKILL_NAME} mis à jour automatiquement vers v{remote_ver}.")
except Exception:
    pass
PY
```

---

## 1. Découverte des Sites Autorisés (`GET /api/ai-child/sites`)

Avant toute opération :
1. Charger `.env` : `[ -f .env ] && { set -a; source .env; set +a; }`.
2. Vérifier la présence de `PRO_PILOT_WRITE_TOKEN` (aucun mot de passe WordPress n'est requis dans `.env`).
3. Lister les sites Fulfi accessibles pour cette organisation :
   ```bash
   set -a; source .env; set +a
   curl -fsS -m 15 -H "Authorization: Bearer ${PRO_PILOT_WRITE_TOKEN}" \
     "https://pro-pilot.propulse-lab.com/api/ai-child/sites"
   ```
   *(En mode multi-partenaires, ajouter `?partner=<slug>` si nécessaire.)*
4. Si la liste est vide, indiquer sobrement qu'aucun site Fulfi n'est rattaché à cette organisation. Si plusieurs sites sont retournés et que l'utilisateur n'a pas précisé lequel, lui demander de choisir.

---

## 2. Règles Critiques & Garde-Fous Non Négociables

1. **Toujours éditer `overrides`, JAMAIS `effective`** :
   - `GET /api/ai-child/platform/<slug>` retourne `{ effective, overrides, defaults, registries, revisions, version, updatedAt }`.
   - `effective` fusionne `defaults` + `overrides`. Soumettre `effective` gèlerait définitivement les valeurs par défaut du thème et sera **rejeté (`400 defaults_freeze_detected`)** par la plateforme.
   - Le round-trip obligatoire est : partir d'une copie profonde de `.overrides`, appliquer le patch minimal ciblé, et soumettre `{ "platform": <overrides_patchés>, "baseVersion": <version> }`.
2. **Contrôle de concurrence CAS (`baseVersion`)** :
   - Toujours transmettre le champ numérique `baseVersion` égal au champ `.version` lu sur le `GET`.
   - En cas de réponse `409` (version modifiée entre-temps), refaire un `GET` frais, ré-appliquer le patch sur la nouvelle version et revalider.
3. **Respect strict des registres (`.registries`)** :
   - Avant d'ajouter un bloc, un token de branding (`--rail-*`, `--brand-*`, `--color-*` en triplet RGB `"R G B"`), une colonne ou un champ, vérifier qu'il existe dans `.registries` retourné par le `GET`.
   - Pour le thème clair (`brandingLight`), définir les tokens `--rail-*` sinon la barre latérale retombe sur ses défauts CSS.
   - Ne pas ajouter de titre `richtext` redondant sur les pages dont le bloc natif (`library`, `watchlist`, etc.) affiche déjà un H1.
4. **Piège `Top Menu` WordPress** :
   - Si le site possède un menu WordPress natif (`Top Menu` / emplacement `primary`), celui-ci **prime** sur `overrides.nav` pour l'ordre et les groupes d'onglets. Prévenir l'utilisateur avant toute modification d'ordre de navigation si le site utilise un menu WP natif.
5. **Zéro secret & Zéro jargon** :
   - Ne jamais afficher les jetons `.env`, URLs techniques internes ou commandes shell brutes dans les réponses adressées à l'utilisateur.

---

## 3. Workflow Strict en 4 Étapes

### Étape 1 — Lecture & Sauvegarde Préventive Obligatoire
```bash
set -a; source .env; set +a
mkdir -p .tmp
curl -fsS -m 15 -H "Authorization: Bearer ${PRO_PILOT_WRITE_TOKEN}" \
  "https://pro-pilot.propulse-lab.com/api/ai-child/platform/${SITE_SLUG}" \
  -o ".tmp/platform-${SITE_SLUG}.json"
```
Enregistrer systématiquement une sauvegarde horodatée de `.overrides` et `.version` dans `.tmp/backup-sites-fulfi-${SITE_SLUG}-v${VERSION}.json` avant toute édition.

### Étape 2 — Patch Minimal sur `.overrides` & Validation Serveur (`POST /validate`)
Préparer `.tmp/payload-${SITE_SLUG}.json` contenant exclusivement `{ "platform": <overrides_patchés>, "baseVersion": <version> }`, vérifier par diff que **seules** les clés demandées ont changé, puis valider sans écrire en prod :
```bash
set -a; source .env; set +a
curl --fail-with-body -sS -m 30 -X POST \
  -H "Authorization: Bearer ${PRO_PILOT_WRITE_TOKEN}" \
  -H "Content-Type: application/json" \
  --data-binary "@.tmp/payload-${SITE_SLUG}.json" \
  "https://pro-pilot.propulse-lab.com/api/ai-child/platform/${SITE_SLUG}/validate"
```
- Si `ok` est `false` (ou HTTP `400`), le corps JSON contient les détails `errors` / `violations` à corriger avant de revalider.
- Remonter les éventuels `warnings` à l'utilisateur.

### Étape 3 — Confirmation Humaine Explicite (STOP Obligatoire)
Présenter clairement à l'utilisateur :
- Le nom du site et son domaine public ;
- Le résumé précis des changements (avant $\rightarrow$ après) ;
- Les éventuels avertissements (`warnings` ou `Top Menu`).
Attendre un accord explicite (**« Oui » / « Go » / « Publie »**) avant d'appeler `PUT`.

### Étape 4 — Publication (`PUT /api/ai-child/platform/<slug>`)
```bash
set -a; source .env; set +a
curl --fail-with-body -sS -m 30 -X PUT \
  -H "Authorization: Bearer ${PRO_PILOT_WRITE_TOKEN}" \
  -H "Content-Type: application/json" \
  --data-binary "@.tmp/payload-${SITE_SLUG}.json" \
  "https://pro-pilot.propulse-lab.com/api/ai-child/platform/${SITE_SLUG}"
```
- Confirmer la nouvelle version enregistrée et le lien public du site.
- Note réseau : en cas de timeout lors du `PUT`, ne jamais relancer l'écriture à l'aveugle : exécuter d'abord un `GET` pour vérifier si la version a déjà été incrémentée.
- Note cache : la publication déclenche la purge côté administration ; le cache public peut mettre quelques instants à se rafraîchir (sauf purge manuelle).
- Si l'utilisateur signale un écart ou formule une règle éditoriale permanente, proposer `/fin` pour la mémoriser.
