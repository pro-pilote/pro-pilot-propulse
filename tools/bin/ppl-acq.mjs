#!/usr/bin/env node
/**
 * ppl-acq.mjs — Module Pro Acquisition (Validation Fail-Closed du Contrat d'Entrée)
 * 
 * Doctrine Globale Medi Chabrol (2026-10-26) :
 * 1. Liste cible (Blueshift / SFMC)
 * 2. Champs demandés (email, tel...)
 * 3. Emplacement où intégrer le formulaire
 * 4. Page de redirection post-inscription
 * 5. Décision de création des pages de confirmation via Pro Web
 */

import fs from 'fs';
import path from 'path';

const args = process.argv.slice(2);

function printHelp() {
  console.log(`
🎯 Pro Acquisition — Module Formulaires & Optins
Doctrine Globale Propulse Lab (Medi Chabrol)

Informations Minimales Obligatoires (Contrat d'Entrée) :
  --list <nom-liste>        Liste cible (Blueshift ou Salesforce Marketing Cloud)
  --fields <champs>         Champs requis séparés par des virgules (ex: email,telephone,prenom)
  --source <url-page>       Emplacement où le formulaire va être intégré
  --redirect <url-page>     URL de destination post-inscription (page de remerciement)
  --create-conf-page <o|n>  Indiquer si les pages de confirmation doivent être créées via Pro Web

Usage :
  ppl acq check --list <nom> --fields <f> --source <url> --redirect <url> --create-conf-page <o|n>
  ppl acq template [--partner <id|slug>]
`);
}

if (args.length === 0 || args.includes('-h') || args.includes('--help')) {
  printHelp();
  process.exit(0);
}

const sub = args[0];

if (sub === 'check') {
  let list = null, fields = null, source = null, redirect = null, createConf = null;

  for (let i = 1; i < args.length; i++) {
    if (args[i] === '--list' && args[i + 1]) list = args[++i];
    else if (args[i] === '--fields' && args[i + 1]) fields = args[++i];
    else if (args[i] === '--source' && args[i + 1]) source = args[++i];
    else if (args[i] === '--redirect' && args[i + 1]) redirect = args[++i];
    else if (args[i] === '--create-conf-page' && args[i + 1]) createConf = args[++i];
  }

  const missing = [];
  if (!list) missing.push('--list (Liste cible Blueshift / SFMC)');
  if (!fields) missing.push('--fields (Champs demandés : email, tel, etc.)');
  if (!source) missing.push('--source (Emplacement du formulaire)');
  if (!redirect) missing.push('--redirect (URL de redirection / remerciement)');
  if (!createConf) missing.push('--create-conf-page (Création page conf Pro Web : oui/non)');

  if (missing.length > 0) {
    console.error(`\n❌ [FAIL-CLOSED] Contrat Pro Acquisition Incomplet !`);
    console.error(`La doctrine globale exige les 5 informations minimales suivantes :\n`);
    for (const m of missing) {
      console.error(`  - Manquant : ${m}`);
    }
    console.error(`\nCorrigez votre demande avant de pouvoir générer le formulaire d'acquisition.\n`);
    process.exit(1);
  }

  console.log(`\n✅ Contrat Pro Acquisition Validé :`);
  console.log(`  • Liste cible      : ${list}`);
  console.log(`  • Champs requis    : ${fields}`);
  console.log(`  • Page source      : ${source}`);
  console.log(`  • Redirection      : ${redirect}`);
  console.log(`  • Page conf ProWeb : ${createConf}\n`);
  process.exit(0);
}

if (sub === 'template') {
  console.log(`\n📋 Template de demande Pro Acquisition prêt à copier :`);
  console.log(`
Liste cible : <nom_liste_blueshift_ou_sfmc>
Champs demandés : email, telephone
Emplacement formulaire : https://<domaine>/inscription
Redirection post-inscription : https://<domaine>/merci
Création page de confirmation Pro Web : Oui / Non
`);
  process.exit(0);
}

console.error(`Sous-commande inconnue : « ${sub} »`);
printHelp();
process.exit(1);
