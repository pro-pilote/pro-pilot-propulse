# Instructions Agent IA — Propulse Lab (Sites Internes)

1. **Règles et Routeur** : Consulte immédiatement [`./RULES.md`](./RULES.md) et [`./ROUTER.md`](./ROUTER.md).
2. **Opérations Pro Web** : Applique [`./.claude/commands/pro-web.md`](./.claude/commands/pro-web.md) (commande `/pro-web`) et [`./.claude/commands/feedback.md`](./.claude/commands/feedback.md) (commande `/feedback`).
3. **Résolution des Identifiants** : Résous le couple `(domainName, websiteId)` depuis [`outils/pro-web-uploader/variables.md`](./outils/pro-web-uploader/variables.md). Demande systématiquement une confirmation humaine explicite à l'utilisateur avant tout appel d'écriture sur l'API Pro Web.
4. **Zéro HTML sur Git & Prévisualisation** : Ne jamais committer de fichiers HTML, HTM ou PDF sur le dépôt Git. Utiliser Claude Artifacts pour l'aperçu visuel ou le dossier local `.tmp/`. Les pages publiées sont hébergées exclusivement sur Pro Web (S3).
5. **Auto-Alimentation Silencieuse (Append-Only)** : Dès qu'une correction, un ajustement de charte ou une nouvelle mention légale est formulée, enregistre la règle dans `donnees-business/_inbox/` via la commande `/feedback` ou le script `outils/feedback_push.py`.
