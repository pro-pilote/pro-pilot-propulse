# Guide Propulse Lab — Pro Webinaire ([[ppl.partner_name]])

## 1. Objectif & Paramètres Pré-remplis
Intégrer un formulaire d'inscription à un webinaire dans une Landing Page de **[[ppl.partner_name]]** (`partner_id: [[ppl.partner_id]]`) et vérifier la salle Live ou Replay sur `[[ppl.webinar_host]]`.

## 2. Snippet Officiel d'Inscription Webinaire (Pré-rempli pour [[ppl.partner_name]])
À insérer tel quel dans la Landing Page (en remplaçant uniquement `<SALLE_SLUG>` par le slug de la salle indiqué dans le brief du webinaire) :

```html
<div id="prowebinar-registration-container" 
     data-room-slug="<SALLE_SLUG>" 
     data-partner-id="[[ppl.partner_id]]" 
     data-redirect-url="https://[[ppl.main_domain]]/confirmation-webinaire">
</div>
<script src="https://[[ppl.webinar_host]]/widget/register.js" async></script>
```

## 3. Commandes `/pro-tools` (`tools/ppl.py webinar`)

```bash
# Générer le snippet exact pour une salle de [[ppl.partner_name]]
python3 tools/ppl.py webinar widget --partner [[ppl.partner_id]] --room <SALLE_SLUG>

# Vérifier l'URL d'une salle Live ou Replay
python3 tools/ppl.py webinar verify --partner [[ppl.partner_id]] --room <SALLE_SLUG>
```
