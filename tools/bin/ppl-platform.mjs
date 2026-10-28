#!/usr/bin/env node
/**
 * ppl-platform.mjs — Module de Vibecoding des Espaces Membres & Thème ai-child
 * 
 * Conception & Architecture : Medi Chabrol · Propulse Lab
 * Gouvernance 3 Zones · Contrôle de concurrence optimiste CAS · Fail-Closed
 */

import fs from 'fs';
import path from 'path';
import os from 'os';
import { fileURLToPath } from 'url';

const TOKEN_PATH = path.join(os.homedir(), '.pro-web-static', 'token.json');
const BASE_PROWEB_URL = 'https://pro-web.propulse-lab.com';
const ROOT_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const BACKUP_DIR = path.join(ROOT_DIR, 'backups');

function printHelp() {
  console.log(`
🏛️  ppl platform — Vibecoding Espaces Membres (Thème ai-child)
Conception & Architecture : Medi Chabrol · Propulse Lab

Usage :
  python ppl.py platform list                                      Lister les plateformes ai-child accessibles
  python ppl.py platform get <domaine> [--full] [--registries]      Inspecter la configuration active (/platform)
  python ppl.py platform validate <domaine> <fichier.json>          Valider la conformité du payload (Dry-run contractuel)
  python ppl.py platform put <domaine> <fichier.json> [--go]        Publier en production avec contrôle optimiste CAS
`);
}

function loadToken() {
  if (!fs.existsSync(TOKEN_PATH)) {
    throw new Error(`Aucun token trouvé dans ${TOKEN_PATH}. Lancez d'abord : python ppl.py login`);
  }
  const data = JSON.parse(fs.readFileSync(TOKEN_PATH, 'utf-8'));
  if (!data.bearer) {
    throw new Error(`Jeton expiré ou invalide. Lancez : python ppl.py login`);
  }
  return data.bearer;
}

async function callProWebApi(subpath, partnerId = null) {
  const token = loadToken();
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
  if (partnerId) {
    headers['x-partner-id'] = String(partnerId);
  }
  const res = await fetch(`${BASE_PROWEB_URL}${subpath}`, { headers });
  if (res.status === 401) {
    const err = new Error(`401 Non autorisé sur Pro Web. Relancez : python ppl.py login`);
    err.status = 401;
    throw err;
  }
  if (!res.ok) {
    const errText = await res.text();
    const err = new Error(`Erreur Pro Web API (${res.status}) : ${errText.slice(0, 300)}`);
    err.status = res.status;
    throw err;
  }
  return await res.json();
}

async function resolveSite(domain) {
  const cleanDomain = domain.toLowerCase().replace(/^https?:\/\//, '').replace(/\/.*$/, '').trim();
  const user = await callProWebApi('/api/auth/user');
  const partners = user.partners || [];

  for (const pid of partners) {
    try {
      const sites = await callProWebApi('/api/websites', pid);
      const list = Array.isArray(sites) ? sites : (sites.data || []);
      for (const s of list) {
        const dName = (s.domainName || '').toLowerCase();
        const urlName = (s.url || '').toLowerCase().replace(/^https?:\/\//, '').replace(/\/.*$/, '');
        if (dName === cleanDomain || urlName === cleanDomain || dName === `www.${cleanDomain}` || `www.${dName}` === cleanDomain) {
          const adminDomain = s.terraformData?.cloudfront_admin_domain || `www-admin.${cleanDomain}`;
          const pw = s.wordpressApiPassword || null;
          return {
            site: s,
            partnerId: pid,
            domain: cleanDomain,
            adminDomain,
            password: pw
          };
        }
      }
    } catch (e) {
      if (e.status === 401) {
        throw e;
      }
      console.warn(`⚠️ Avertissement découverte partenaire ${pid} : ${e.message}`);
    }
  }
  throw new Error(`Site « ${cleanDomain} » introuvable parmi vos organisations autorisées.`);
}

function getAuthHeader(siteInfo) {
  // 1. Priorité au fichier d'Application Passwords local sécurisé (~/.pro-web-static/wp-apps.json) par domaine
  const wpAppsPath = path.join(os.homedir(), '.pro-web-static', 'wp-apps.json');
  if (fs.existsSync(wpAppsPath)) {
    try {
      const wpApps = JSON.parse(fs.readFileSync(wpAppsPath, 'utf-8'));
      const app = wpApps[siteInfo.domain] || wpApps[siteInfo.adminDomain];
      if (app) {
        if (!app.user || !app.password) {
          throw new Error(`L'entrée pour ${siteInfo.domain} est incomplète (user ou password manquant).`);
        }
        const creds = Buffer.from(`${app.user}:${app.password}`).toString('base64');
        return `Basic ${creds}`;
      }
    } catch (e) {
      throw new Error(`❌ [FAIL-CLOSED] Erreur dans ${wpAppsPath} : ${e.message}`);
    }
  }

  // 2. Identifiants personnels via variables d'environnement (sessions CLI ciblées / CI)
  if (process.env.WP_APP_USER || process.env.WP_APP_PASSWORD) {
    if (!process.env.WP_APP_USER || !process.env.WP_APP_PASSWORD) {
      throw new Error(`❌ [FAIL-CLOSED] Les variables d'environnement WP_APP_USER et WP_APP_PASSWORD doivent être définies conjointement.`);
    }
    if (!process.env.WP_APP_DOMAIN) {
      throw new Error(
        `❌ [FAIL-CLOSED SÉCURITÉ] Les identifiants WP_APP_USER et WP_APP_PASSWORD requièrent impérativement la définition de WP_APP_DOMAIN (ex: WP_APP_DOMAIN=${siteInfo.domain}).\n` +
        `   Pour gérer plusieurs domaines sans variable d'environnement, utilisez le trousseau local sécurisé ~/.pro-web-static/wp-apps.json.`
      );
    }
    const targetDomain = process.env.WP_APP_DOMAIN.toLowerCase().replace(/^https?:\/\//, '').replace(/\/.*$/, '').trim();
    if (targetDomain !== siteInfo.domain && targetDomain !== siteInfo.adminDomain) {
      throw new Error(
        `❌ [SÉCURITÉ] Les identifiants WP_APP_* sont configurés pour « ${targetDomain} », mais la cible est « ${siteInfo.domain} ».\n` +
        `   Définissez WP_APP_DOMAIN=${siteInfo.domain} ou utilisez ~/.pro-web-static/wp-apps.json pour gérer plusieurs domaines.`
      );
    }
    const creds = Buffer.from(`${process.env.WP_APP_USER}:${process.env.WP_APP_PASSWORD}`).toString('base64');
    return `Basic ${creds}`;
  }

  // 3. Repli technique de dernier recours sur le secret partagé Pro Web API (Risque prod)
  if (siteInfo.password) {
    console.warn(
      '⚠️ [RISQUE SÉCURITÉ PRODUCTION] Utilisation du compte technique partagé pro-web-api.\n' +
      '   Recommandation stricte : configurez vos identifiants personnels dans ~/.pro-web-static/wp-apps.json ou WP_APP_USER/WP_APP_PASSWORD.'
    );
    const creds = Buffer.from(`pro-web-api:${siteInfo.password}`).toString('base64');
    return `Basic ${creds}`;
  }

  throw new Error(
    `Aucun mot de passe d'application WordPress trouvé pour ${siteInfo.domain}.\n` +
    `👉 Générez votre mot de passe d'application en 1 clic : https://${siteInfo.adminDomain}/wp-admin/authorize-application.php?app_name=agent-api\n` +
    `Puis définissez vos identifiants dans ~/.pro-web-static/wp-apps.json ou via WP_APP_USER et WP_APP_PASSWORD.`
  );
}

function loadPayloadFile(filepath) {
  const cleanPath = filepath.startsWith('@') ? filepath.slice(1) : filepath;
  if (!fs.existsSync(cleanPath)) {
    throw new Error(`Fichier payload introuvable : ${cleanPath}`);
  }
  const raw = fs.readFileSync(cleanPath, 'utf-8');
  try {
    return JSON.parse(raw);
  } catch (e) {
    throw new Error(`Le fichier « ${cleanPath} » ne contient pas un JSON valide : ${e.message}`);
  }
}

// -------------------------------------------------------------------------
// Commandes
// -------------------------------------------------------------------------

async function cmdList() {
  console.log('🔍 Découverte des plateformes ai-child accessibles via Pro Web...\n');
  const user = await callProWebApi('/api/auth/user');
  const partners = user.partners || [];
  const foundSites = [];

  for (const pid of partners) {
    try {
      const sites = await callProWebApi('/api/websites', pid);
      const list = Array.isArray(sites) ? sites : (sites.data || []);
      for (const s of list) {
        if (s.type !== 'STATIC') {
          foundSites.push({
            Domaine: s.domainName || s.url,
            Partenaire: pid,
            Type: s.type || 'CMS',
            Admin: s.terraformData?.cloudfront_admin_domain || 'www-admin'
          });
        }
      }
    } catch (e) {
      if (e.status === 401) {
        throw e;
      }
      console.warn(`⚠️ Avertissement découverte partenaire ${pid} : ${e.message}`);
    }
  }

  if (foundSites.length === 0) {
    console.log('Aucun site WordPress / ai-child détecté pour vos organisations.');
    return;
  }

  console.table(foundSites);
  console.log(`\nPour inspecter une plateforme : python ppl.py platform get <domaine>`);
}

async function cmdGet(domain, args) {
  const full = args.includes('--full');
  const registries = args.includes('--registries');
  const siteInfo = await resolveSite(domain);

  const url = `https://${siteInfo.adminDomain}/wp-json/ai-child/v1/platform`;
  const res = await fetch(url, {
    headers: {
      'Authorization': getAuthHeader(siteInfo),
      'Accept': 'application/json'
    }
  });

  if ([500, 503].includes(res.status)) {
    throw new Error(`HTTP ${res.status} sur ${siteInfo.adminDomain}. Vérifiez que votre IP est autorisée sur https://pro-ips.propulse-lab.com`);
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Erreur GET /platform (${res.status}) : ${text.slice(0, 300)}`);
  }

  const data = await res.json();

  if (full) {
    console.log(JSON.stringify(data, null, 2));
    return;
  }

  console.log(`\n🏛️  Plateforme ai-child : ${siteInfo.domain}`);
  console.log(`   • Administration : https://${siteInfo.adminDomain}`);
  console.log(`   • Version CAS    : ${data.version ?? 'non versionné'}`);
  console.log(`   • Dernière MAJ   : ${data.updatedAt ?? 'inconnue'}`);

  if (registries && data.registries) {
    console.log('\n📦 Blocs UI disponibles (Registries) :');
    for (const [k, v] of Object.entries(data.registries)) {
      console.log(`   - ${k} : ${v.label || v.title || ''}`);
    }
    return;
  }

  const nav = data.effective?.nav || [];
  console.log(`\n🧭 Navigation effective (${nav.length} entrées) :`);
  for (let i = 0; i < nav.length; i++) {
    const item = nav[i];
    const sec = item.section ? ` [section: ${item.section}]` : '';
    const adm = item.adminOnly ? ' (ADMIN ONLY)' : '';
    console.log(`   ${i + 1}. ${item.label || item.id}${sec}${adm}`);
  }

  console.log(`\n💡 Astuce :`);
  console.log(`   - Pour exporter l'arbre complet : python ppl.py platform get ${domain} --full > platform.json`);
  console.log(`   - Pour inspecter les blocs React : python ppl.py platform get ${domain} --registries\n`);
}

async function cmdValidate(domain, filepath) {
  const payload = loadPayloadFile(filepath);

  // 1. Contrôle CAS fail-closed client
  const isVersionValid = (typeof payload.baseVersion === 'number' && !isNaN(payload.baseVersion)) || 
                         (typeof payload.baseVersion === 'string' && payload.baseVersion.trim().length > 0);
  if (!isVersionValid) {
    throw new Error(
      `❌ [FAIL-CLOSED] Le champ 'baseVersion' est obligatoire (nombre ou chaîne non-vide) dans le payload pour le contrôle CAS.\n` +
      `   Exportez avec jq : jq '{platform: .overrides, baseVersion: .version}' platform-export.json > platform-overrides.json`
    );
  }

  // 2. Contrôle structurel de platform
  if (!payload.platform || typeof payload.platform !== 'object' || Array.isArray(payload.platform) || Object.keys(payload.platform).length === 0) {
    throw new Error(
      `❌ [FAIL-CLOSED] Le payload doit contenir un objet 'platform' non-vide ({ platform: { ... }, baseVersion: ... }).\n` +
      `   La racine ne doit pas être soumise directement sous peine d'effacement partiel.`
    );
  }
  const platform = payload.platform;

  // 3. Contrôle anti-écrasement brut
  if ('effective' in platform || 'version' in platform) {
    throw new Error(
      `❌ [FAIL-CLOSED] Le payload contient les clés 'effective' ou 'version' (export brut détecté).\n` +
      `   Vous devez soumettre UNIQUEMENT les overrides ({ platform: { ... }, baseVersion: ... }).`
    );
  }

  const siteInfo = await resolveSite(domain);

  console.log(`🔍 Validation du payload pour « ${domain} » (baseVersion: ${payload.baseVersion})...`);
  const url = `https://${siteInfo.adminDomain}/wp-json/ai-child/v1/platform/validate`;
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': getAuthHeader(siteInfo),
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ platform, baseVersion: payload.baseVersion })
  });

  if ([500, 503].includes(res.status)) {
    throw new Error(`HTTP ${res.status} sur ${siteInfo.adminDomain}. Vérifiez que votre IP est autorisée sur https://pro-ips.propulse-lab.com`);
  }
  if (!res.ok) {
    const text = await res.text();
    console.error(`⚠️ Échec validation serveur (HTTP ${res.status}) : ${text.slice(0, 300)}`);
    process.exit(1);
  }

  const result = await res.json();
  if (result.ok) {
    console.log('✅ Validation RÉUSSIE : le payload est conforme au contrat ai-child.');
  } else {
    console.log('❌ Validation ÉCHOUÉE :');
    if (result.errors) result.errors.forEach(e => console.log(`   - ${e}`));
    if (result.violations) result.violations.forEach(v => console.log(`   - ${v.field} : ${v.reason}`));
    process.exit(1);
  }
}

async function cmdPut(domain, filepath, args) {
  const isGo = args.includes('--go');
  const payload = loadPayloadFile(filepath);

  // 1. Contrôle CAS fail-closed client
  const isVersionValid = (typeof payload.baseVersion === 'number' && !isNaN(payload.baseVersion)) || 
                         (typeof payload.baseVersion === 'string' && payload.baseVersion.trim().length > 0);
  if (!isVersionValid) {
    throw new Error(
      `❌ [FAIL-CLOSED] Le champ 'baseVersion' est obligatoire (nombre ou chaîne non-vide) dans le payload pour le contrôle CAS.\n` +
      `   Exportez avec jq : jq '{platform: .overrides, baseVersion: .version}' platform-export.json > platform-overrides.json`
    );
  }

  // 2. Contrôle structurel de platform
  if (!payload.platform || typeof payload.platform !== 'object' || Array.isArray(payload.platform) || Object.keys(payload.platform).length === 0) {
    throw new Error(
      `❌ [FAIL-CLOSED] Le payload doit contenir un objet 'platform' non-vide ({ platform: { ... }, baseVersion: ... }).\n` +
      `   La racine ne doit pas être soumise directement sous peine d'effacement partiel.`
    );
  }
  const platform = payload.platform;

  // 3. Contrôle anti-écrasement brut
  if ('effective' in platform || 'version' in platform) {
    throw new Error(
      `❌ [FAIL-CLOSED] Le payload contient les clés 'effective' ou 'version' (export brut détecté).\n` +
      `   Vous devez soumettre UNIQUEMENT les overrides ({ platform: { ... }, baseVersion: ... }).`
    );
  }

  const siteInfo = await resolveSite(domain);
  const baseVersion = payload.baseVersion;
  console.log(`\n📋 Cible : ${domain} (baseVersion soumise : ${baseVersion})`);
  console.log(`   Fichier : ${filepath}`);

  if (!isGo) {
    console.log('\n🔒 MODE DRY-RUN ACTIF : aucune modification en production.');
    console.log(`👉 Pour déployer réellement avec contrôle CAS, ajoutez --go :`);
    console.log(`   python ppl.py platform put ${domain} ${filepath} --go\n`);
    return;
  }

  // Résolution unique de l'en-tête d'authentification pour toute la séquence de publication
  const authHeader = getAuthHeader(siteInfo);

  // 4. Validation serveur obligatoire préalable avant publication
  console.log(`🔍 Validation serveur préalable obligatoire...`);
  const valUrl = `https://${siteInfo.adminDomain}/wp-json/ai-child/v1/platform/validate`;
  const valRes = await fetch(valUrl, {
    method: 'POST',
    headers: {
      'Authorization': authHeader,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ platform, baseVersion })
  });
  if ([500, 503].includes(valRes.status)) {
    throw new Error(`HTTP ${valRes.status} sur ${siteInfo.adminDomain}. Vérifiez que votre IP est autorisée sur https://pro-ips.propulse-lab.com`);
  }
  if (!valRes.ok) {
    const valErrText = await valRes.text();
    throw new Error(`Échec validation serveur (HTTP ${valRes.status}) : ${valErrText.slice(0, 300)}`);
  }
  const valResult = await valRes.json();
  if (!valResult.ok) {
    const errDetails = (valResult.errors || []).concat((valResult.violations || []).map(v => `${v.field}: ${v.reason}`));
    throw new Error(`Validation serveur rejetée : ${errDetails.join(' ; ')}`);
  }

  // 5. Récupération préalable distante et contrôle local CAS avant écriture
  const getRes = await fetch(`https://${siteInfo.adminDomain}/wp-json/ai-child/v1/platform`, {
    headers: { 'Authorization': authHeader }
  });
  if ([500, 503].includes(getRes.status)) {
    throw new Error(`HTTP ${getRes.status} sur ${siteInfo.adminDomain}. Vérifiez que votre IP est autorisée sur https://pro-ips.propulse-lab.com`);
  }
  if (!getRes.ok) {
    throw new Error(`Échec de la récupération préalable avant écriture (HTTP ${getRes.status}). Déploiement annulé par sécurité.`);
  }
  const backupData = await getRes.json();

  // Contrôle local de non-régression CAS avant émission du PUT (fail-closed strict, normalisation de type)
  if (backupData.version === undefined || backupData.version === null || String(backupData.version).trim() !== String(baseVersion).trim()) {
    throw new Error(
      `❌ [CONFLIT CAS DÉTECTÉ LOCALEMENT] La version distante (${backupData.version ?? 'indéfinie'}) ne correspond pas à votre baseVersion (${baseVersion}) !\n` +
      `   Un autre collaborateur a publié ou la version est introuvable. Relancez 'python ppl.py platform get ${domain}' pour récupérer la nouvelle version avant d'appliquer vos modifications.`
    );
  }

  // Contrôle de présence de la clé contractuelle 'overrides' avant sauvegarde (objet non-null et non-tableau)
  if (!('overrides' in backupData) || backupData.overrides === null || typeof backupData.overrides !== 'object' || Array.isArray(backupData.overrides)) {
    throw new Error(
      `❌ [FAIL-CLOSED] La réponse distante ne contient pas la clé contractuelle 'overrides' sous forme d'objet.\n` +
      `   Sauvegarde préventive et publication annulées par sécurité.`
    );
  }

  // 6. Sauvegarde préventive bloquante dans backups/
  if (!fs.existsSync(BACKUP_DIR)) {
    fs.mkdirSync(BACKUP_DIR, { recursive: true });
  }
  const safeDomain = domain.replace(/[^a-z0-9]/gi, '_');
  const safeVersion = String(backupData.version ?? 'unknown').replace(/[^a-z0-9._-]/gi, '_');
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const backupFile = path.join(BACKUP_DIR, `backup-${safeDomain}-v${safeVersion}-${timestamp}.json`);
  fs.writeFileSync(backupFile, JSON.stringify(backupData, null, 2), 'utf-8');
  console.log(`💾 Sauvegarde de sécurité créée : ${backupFile}`);

  // 7. Publication en production avec la baseVersion du fichier
  console.log(`🚀 Publication en production (CAS baseVersion=${baseVersion})...`);
  const putUrl = `https://${siteInfo.adminDomain}/wp-json/ai-child/v1/platform`;
  let putRes;
  try {
    putRes = await fetch(putUrl, {
      method: 'PUT',
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        platform,
        baseVersion
      })
    });
  } catch (err) {
    throw new Error(
      `❌ [ÉCHEC RÉSEAU POST-PUT] Échec réseau pendant le PUT (avant ou après émission) : ${err.message}.\n` +
      `   Exécutez immédiatement 'python ppl.py platform get ${domain} --full' et comparez .version avec votre baseVersion (${baseVersion}) pour vérifier si l'écriture a été enregistrée.`
    );
  }

  if (putRes.status === 409) {
    throw new Error(
      `❌ [CONFLIT CAS 409] La version distante a été modifiée par un autre collaborateur !\n` +
      `   Votre baseVersion (${baseVersion}) est obsolète.\n` +
      `   Relancez 'python ppl.py platform get ${domain}' pour récupérer la nouvelle version avant d'appliquer vos modifications.`
    );
  }

  if ([500, 503].includes(putRes.status)) {
    throw new Error(
      `❌ HTTP ${putRes.status} sur ${siteInfo.adminDomain}. L'écriture a pu être enregistrée côté serveur.\n` +
      `   Exécutez immédiatement 'python ppl.py platform get ${domain} --full' pour vérifier .version et vérifiez votre IP sur https://pro-ips.propulse-lab.com.`
    );
  }

  if (!putRes.ok) {
    let text;
    try {
      text = await putRes.text();
    } catch (err) {
      throw new Error(
        `❌ [ÉCHEC RÉSEAU POST-PUT] Échec de lecture du corps d'erreur HTTP ${putRes.status} post-PUT : ${err.message}.\n` +
        `   Exécutez immédiatement 'python ppl.py platform get ${domain} --full' pour vérifier l'état distant.`
      );
    }
    throw new Error(`❌ Échec du déploiement (HTTP ${putRes.status}) : ${text.slice(0, 300)}`);
  }

  let putData;
  try {
    putData = await putRes.json();
  } catch (err) {
    const isSyntax = err instanceof SyntaxError;
    throw new Error(
      `❌ [${isSyntax ? 'RÉPONSE INVALIDE (NON-JSON)' : 'ÉCHEC RÉSEAU'}] Échec de lecture du corps de réponse post-PUT : ${err.message}.\n` +
      `   Exécutez immédiatement 'python ppl.py platform get ${domain} --full' pour vérifier si votre écriture est active.`
    );
  }
  console.log(`✅ Publication réussie ! Nouvelle version CAS : ${putData.version}`);
  console.log(`   Invalidation CloudFront automatique post-écriture déclenchée.\n`);
}

// -------------------------------------------------------------------------
// Main
// -------------------------------------------------------------------------

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0 || args.includes('-h') || args.includes('--help')) {
    printHelp();
    process.exit(0);
  }

  const cmd = args[0].toLowerCase();
  const subArgs = args.slice(1);

  try {
    if (cmd === 'list') {
      await cmdList();
    } else if (cmd === 'get') {
      if (!subArgs[0]) throw new Error(`Domaine manquant : python ppl.py platform get <domaine>`);
      await cmdGet(subArgs[0], subArgs.slice(1));
    } else if (cmd === 'validate') {
      if (!subArgs[0] || !subArgs[1]) throw new Error(`Arguments manquants : python ppl.py platform validate <domaine> <fichier.json>`);
      await cmdValidate(subArgs[0], subArgs[1]);
    } else if (cmd === 'put') {
      if (!subArgs[0] || !subArgs[1]) throw new Error(`Arguments manquants : python ppl.py platform put <domaine> <fichier.json> [--go]`);
      await cmdPut(subArgs[0], subArgs[1], subArgs.slice(2));
    } else {
      console.error(`❌ Commande platform inconnue : « ${cmd} »`);
      printHelp();
      process.exit(1);
    }
  } catch (err) {
    console.error(`\n❌ ${err.message}\n`);
    process.exit(1);
  }
}

main();
