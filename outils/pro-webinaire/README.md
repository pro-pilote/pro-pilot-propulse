# Outil : Pro Webinaire (Salles Live, Replays & Inscription)

## 1. Objectif
Intégrer un formulaire d'inscription à un webinaire dans une Landing Page et vérifier la configuration de la salle Live ou Replay du partenaire.

## 2. Snippet Standard d'Inscription Webinaire
À insérer tel quel dans la Landing Page (en remplaçant `SALLE_SLUG`, `PARTNER_ID`, `MAIN_DOMAIN` et `WEBINAR_HOST` par les valeurs de `outils/pro-webinaire/variables.md` du dépôt partenaire) :

```html
<div id="prowebinar-registration-container" 
     data-room-slug="SALLE_SLUG" 
     data-partner-id="PARTNER_ID" 
     data-redirect-url="https://MAIN_DOMAIN/confirmation-webinaire">
</div>
<script src="https://WEBINAR_HOST/widget/register.js" async></script>
```

## 3. Commandes `/pro-tools` (`tools/ppl.py webinar`)

```bash
# Générer le snippet exact pour une salle du partenaire
python3 tools/ppl.py webinar widget --partner <PARTNER_ID> --room <SALLE_SLUG>

# Vérifier l'URL d'une salle Live ou Replay
python3 tools/ppl.py webinar verify --partner <PARTNER_ID> --room <SALLE_SLUG>
```
