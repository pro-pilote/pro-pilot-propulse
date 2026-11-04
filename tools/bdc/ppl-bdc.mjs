#!/usr/bin/env node
/**
 * ppl-bdc — Boîte à outils "vibecoding" pour Bons de Commande (BDC / Pro Funnel).
 *
 * Fournit les *mains* (résolution, miroir local, preview, audit anti-régression, déploiement) ;
 * le *cerveau* c'est Claude Code ou Antigravity (en local).
 *
 * Workflow type :
 *   ppl-bdc resolve <url|slug>        # inspecte le BDC et résout son Flow/Step
 *   ppl-bdc pull    <url|slug>        # miroir local dans bdcs/<slug>/
 *   (ouvre Claude Code dans bdcs/<slug>/ et vibecode)
 *   ppl-bdc preview <slug>            # prévisualisation locale (http://localhost:8080)
 *   ppl-bdc audit   <slug>            # audit statique des règles contractuelles DOM/CSS
 *   ppl-bdc push    <slug>            # DRY-RUN par défaut (montre le diff)
 *   ppl-bdc push    <slug> --go       # déploie en PROD (confirmation demandée)
 *   ppl-bdc clone   <url|slug>        # duplique un BDC éprouvé en un nouveau flow test
 */

import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import http from 'node:http';
import readline from 'node:readline';
import { fileURLToPath } from 'node:url';
import { ProFunnelClient, ProFunnelApiError } from './lib/profunnel-api.mjs';
import { auditBdc, extractDomIds, SEVERITY } from './lib/bdc-rules.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BDCS_DIR = path.join(__dirname, 'bdcs');
const MANIFEST_FILE = '.ppl-manifest.json';
const FLOW_META_FILE = 'flow.json';
const DEFAULT_BDC_DOMAIN = process.env.PPL_BDC_DOMAIN || '';
const DEFAULT_PARTNER_ID = Number(process.env.PPL_PARTNER_ID || 0);

function sha256(content) {
  return crypto.createHash('sha256').update(content).digest('hex');
}

function die(msg) {
  console.error(`❌ ${msg}`);
  process.exit(1);
}

async function confirmPrompt(question) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });
  return new Promise(resolve => {
    rl.question(`${question} [oui/non] `, answer => {
      rl.close();
      const a = (answer || '').trim().toLowerCase();
      resolve(a === 'oui' || a === 'o' || a === 'yes' || a === 'y');
    });
  });
}

function parseUrlOrSlug(input) {
  let url = input.trim();
  let domain = '';
  let slug = '';

  if (url.startsWith('http://') || url.startsWith('https://')) {
    try {
      const u = new URL(url);
      domain = u.hostname;
      slug = u.pathname.replace(/^\/+/, '').split('/')[0];
    } catch {
      die(`URL invalide : ${input}`);
    }
  } else if (url.includes('/')) {
    const parts = url.split('/');
    domain = parts[0];
    slug = parts[1];
  } else {
    slug = url;
  }

  let partnerId = DEFAULT_PARTNER_ID;

  return { domain, slug, partnerId };
}

/**
 * Extrait les métadonnées embarquées (dataLayer, jsonFlow, jsonOffres) depuis l'HTML public d'un BDC.
 */
async function inspectLiveHtml(liveUrl) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  let html = '';
  try {
    const resp = await fetch(liveUrl, {
      signal: controller.signal,
      headers: {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
      }
    });
    clearTimeout(timeoutId);
    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status} ${resp.statusText}`);
    }
    html = await resp.text();
  } catch (err) {
    clearTimeout(timeoutId);
    throw new Error(`Impossible de charger la page live ${liveUrl} : ${err.message}`);
  }

  // Parse scripts JSON
  const grabJson = id => {
    const m = html.match(new RegExp(`<script type="application/json" id="${id}">(.*?)</script>`, 's'));
    if (!m) return null;
    try {
      return JSON.parse(m[1]);
    } catch {
      return null;
    }
  };

  const flow = grabJson('jsonFlow') || {};
  const offers = grabJson('jsonOffres') || [];
  const recurringOffers = grabJson('jsonRecurringOffers') || [];
  const packs = grabJson('jsonPacks') || [];
  const orderBumps = grabJson('jsonOrderBumps') || [];
  const paymentMean = grabJson('jsonPaymentMean') || {};

  // Parse dataLayer pour trouver orderSteps et orderFlowId
  let orderSteps = [];
  let orderFlowId = flow._id || '';
  let currentStepSlug = '';

  const dlMatch = html.match(/dataLayer\s*=\s*(\[\{.*?\}\]);/s);
  if (dlMatch) {
    try {
      const dl = JSON.parse(dlMatch[1]);
      if (Array.isArray(dl) && dl[0]) {
        orderSteps = dl[0].orderSteps || [];
        orderFlowId = dl[0].orderFlowId || orderFlowId;
        currentStepSlug = dl[0].orderStepSlug || '';
      }
    } catch {}
  }

  // Extraction du corps GrapesJS et du CSS
  let gjsHtml = '';
  let gjsCss = '';

  const bodyMatch = html.match(/<body id="grapes-iframe-body"[^>]*>(.*?)<\/body>/s);
  if (bodyMatch) {
    gjsHtml = `<body id="grapes-iframe-body">\n${bodyMatch[1].trim()}\n</body>`;
  } else {
    // Fallback corps de body
    const genericBody = html.match(/<body[^>]*>(.*?)<\/body>/s);
    if (genericBody) {
      gjsHtml = `<body id="grapes-iframe-body">\n${genericBody[1].trim()}\n</body>`;
    }
  }

  const styles = [...html.matchAll(/<style[^>]*>(.*?)<\/style>/gs)];
  if (styles.length > 0) {
    // Les derniers blocs de styles portent généralement le design spécifique
    gjsCss = styles.map(s => s[1].trim()).join('\n\n');
  }

  return {
    rawHtml: html,
    flow,
    orderFlowId,
    orderSteps,
    currentStepSlug,
    offers,
    recurringOffers,
    packs,
    orderBumps,
    paymentMean,
    gjsHtml,
    gjsCss
  };
}

// ──────────────────────────────── COMMANDES ────────────────────────────────

async function cmdResolve(target) {
  const { domain, slug } = parseUrlOrSlug(target);
  if (!slug) die('Veuillez fournir une URL ou un slug valide.');

  let liveDomain = domain || DEFAULT_BDC_DOMAIN;
  if (!liveDomain) {
    die('Veuillez fournir une URL complète (https://<domaine>/<slug>) ou définir PPL_BDC_DOMAIN.');
  }

  const liveUrl = `https://${liveDomain}/${slug}?preview=1`;
  console.log(`🔍 Résolution du BDC via ${liveUrl}...`);

  try {
    const live = await inspectLiveHtml(liveUrl);
    const partnerId = live.flow.partnerId || DEFAULT_PARTNER_ID;

    const result = {
      flowId: live.orderFlowId || live.flow._id,
      partnerId,
      partnerDomain: liveDomain,
      flowTitle: live.flow.title || 'Sans titre',
      tags: live.flow.tags || [],
      steps: live.orderSteps.map(s => ({
        id: s._id,
        type: s.type,
        slug: s.slug,
        title: s.title,
        url: `https://${liveDomain}/${s.slug}?preview=1`
      })),
      offersCount: live.offers.length,
      offers: live.offers.map(o => ({
        id: o._id || o.id,
        offername: o.offername || '',
        name: o.name || '',
        price: o.regularPrice
      })),
      paymentMeans: live.paymentMean.means || live.paymentMean || []
    };

    console.log(JSON.stringify(result, null, 2));
    return result;
  } catch (err) {
    die(`Échec de résolution : ${err.message}`);
  }
}

async function cmdPull(target) {
  const { domain, slug } = parseUrlOrSlug(target);
  if (!slug) die('Veuillez fournir une URL ou un slug valide.');

  let liveDomain = domain || DEFAULT_BDC_DOMAIN;
  if (!liveDomain) {
    die('Veuillez fournir une URL complète (https://<domaine>/<slug>) ou définir PPL_BDC_DOMAIN.');
  }
  const liveUrl = `https://${liveDomain}/${slug}?preview=1`;

  console.log(`↓ Téléchargement du BDC depuis ${liveUrl}...`);
  const live = await inspectLiveHtml(liveUrl);
  const partnerId = live.flow.partnerId || DEFAULT_PARTNER_ID;

  // Création du dossier cible
  const folderName = `${partnerId}_${slug}`;
  const targetDir = path.join(BDCS_DIR, folderName);

  // Protection contre écrasement de modifications locales
  const manifestPath = path.join(targetDir, MANIFEST_FILE);
  if (fs.existsSync(manifestPath) && !process.argv.includes('--force')) {
    try {
      const existingManifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
      if (existingManifest.files) {
        for (const [fname, expectedSha] of Object.entries(existingManifest.files)) {
          const fpath = path.join(targetDir, fname);
          if (fs.existsSync(fpath) && sha256(fs.readFileSync(fpath, 'utf8')) !== expectedSha) {
            die(`[CONFLIT LOCAL] Le fichier « ${fname} » a été modifié localement depuis le pull précédent.\nSauvegardez vos modifications ou ajoutez l'option --force pour écraser.`);
          }
        }
      }
    } catch (e) {
      if (e.message.includes('[CONFLIT LOCAL]')) throw e;
    }
  }

  fs.mkdirSync(targetDir, { recursive: true });

  // Identification des étapes checkout et thankyou
  const checkoutStep = live.orderSteps.find(s => s.type === 'checkout') || { slug, _id: '' };
  const merciStep = live.orderSteps.find(s => s.type === 'thankyou') || { slug: `MERCI-${slug}`, _id: '' };

  let checkoutHtml = live.gjsHtml || '<body id="grapes-iframe-body">\n  <!-- Formulaire BDC -->\n</body>';
  let checkoutCss = live.gjsCss || '/* Styles BDC */';
  let thankyouHtml = '<body id="grapes-iframe-body">\n  <div class="container">\n    <h1>Merci pour votre commande</h1>\n  </div>\n</body>';
  let thankyouCss = '/* Styles Page Merci */';

  // Si la page merci est résolue, tenter de télécharger son HTML live
  if (merciStep.slug) {
    try {
      const merciLive = await inspectLiveHtml(`https://${liveDomain}/${merciStep.slug}?preview=1`);
      if (merciLive.gjsHtml) thankyouHtml = merciLive.gjsHtml;
      if (merciLive.gjsCss) thankyouCss = merciLive.gjsCss;
    } catch {}
  }

  // Tenter de rafraîchir les assets officiels via l'API BO si les crédentiels sont discrets
  let apiCheckoutVersion = 0;
  let apiMerciVersion = 0;
  let source = 'dom';
  try {
    const client = new ProFunnelClient({ partnerId });
    if (checkoutStep._id) {
      const sData = await client.getStep(checkoutStep._id);
      apiCheckoutVersion = sData.__v || 0;
      if (sData.grapes && sData.grapes[0]?.content) {
        if (sData.grapes[0].content['gjs-html']) {
          checkoutHtml = sData.grapes[0].content['gjs-html'];
          source = 'api';
        }
        if (sData.grapes[0].content['gjs-css']) checkoutCss = sData.grapes[0].content['gjs-css'];
      }
    }
    if (merciStep._id) {
      const mData = await client.getStep(merciStep._id);
      apiMerciVersion = mData.__v || 0;
      if (mData.grapes && mData.grapes[0]?.content) {
        if (mData.grapes[0].content['gjs-html']) thankyouHtml = mData.grapes[0].content['gjs-html'];
        if (mData.grapes[0].content['gjs-css']) thankyouCss = mData.grapes[0].content['gjs-css'];
      }
    }
  } catch (err) {
    console.log(`  ℹ️  Extraction API directe non active (${err.message.slice(0, 80)}) ; extraction DOM live retenue.`);
  }

  // Écriture des fichiers de travail
  fs.writeFileSync(path.join(targetDir, 'checkout.html'), checkoutHtml, 'utf8');
  fs.writeFileSync(path.join(targetDir, 'checkout.css'), checkoutCss, 'utf8');
  fs.writeFileSync(path.join(targetDir, 'thankyou.html'), thankyouHtml, 'utf8');
  fs.writeFileSync(path.join(targetDir, 'thankyou.css'), thankyouCss, 'utf8');

  // flow.json
  const flowMeta = {
    flowId: live.orderFlowId || live.flow._id,
    partnerId,
    partnerDomain: liveDomain,
    title: live.flow.title || slug,
    tags: live.flow.tags || [],
    defaultPaymentMean: live.flow.defaultPaymentMean || 'SEPA',
    paymentMeans: ['SEPA', 'CC'],
    checkout: {
      stepId: checkoutStep._id,
      slug: checkoutStep.slug,
      title: checkoutStep.title || 'Offre Spéciale',
      next: merciStep.slug,
      __v: apiCheckoutVersion
    },
    thankyou: {
      stepId: merciStep._id,
      slug: merciStep.slug,
      title: merciStep.title || 'Merci',
      __v: apiMerciVersion
    },
    offers: live.offers.map(o => ({
      id: o._id || o.id,
      offername: o.offername || '',
      name: o.name || '',
      price: o.regularPrice
    }))
  };
  fs.writeFileSync(path.join(targetDir, FLOW_META_FILE), JSON.stringify(flowMeta, null, 2), 'utf8');

  // Manifeste avec empreintes SHA-256 et inventaire d'IDs contractuels
  const contractualIds = extractDomIds(checkoutHtml);
  const manifest = {
    pulledAt: new Date().toISOString(),
    source,
    flowId: flowMeta.flowId,
    partnerId,
    slug,
    checkoutStepId: checkoutStep._id,
    checkoutVersion: apiCheckoutVersion,
    merciStepId: merciStep._id,
    merciVersion: apiMerciVersion,
    contractualIds,
    files: {
      'checkout.html': sha256(checkoutHtml),
      'checkout.css': sha256(checkoutCss),
      'thankyou.html': sha256(thankyouHtml),
      'thankyou.css': sha256(thankyouCss),
      [FLOW_META_FILE]: sha256(JSON.stringify(flowMeta, null, 2))
    }
  };
  fs.writeFileSync(path.join(targetDir, MANIFEST_FILE), JSON.stringify(manifest, null, 2), 'utf8');

  console.log(`\n✅ BDC téléchargé avec succès dans : ${targetDir}`);
  console.log(`\nFichiers créés :`);
  console.log(`  📄 checkout.html  (${Buffer.byteLength(checkoutHtml)} octets)`);
  console.log(`  🎨 checkout.css   (${Buffer.byteLength(checkoutCss)} octets)`);
  console.log(`  📄 thankyou.html  (${Buffer.byteLength(thankyouHtml)} octets)`);
  console.log(`  🎨 thankyou.css   (${Buffer.byteLength(thankyouCss)} octets)`);
  console.log(`  ⚙️  flow.json      (Métadonnées du tunnel)`);
  console.log(`  🔒 .ppl-manifest.json`);
  console.log(`\n→ Pour vibecoder, ouvrez Claude Code dans ce dossier :`);
  console.log(`   cd "${targetDir}" && claude`);
  console.log(`→ Puis validez et prévisualisez vos modifications :`);
  console.log(`   ppl-bdc preview ${slug}`);
  console.log(`   ppl-bdc audit ${slug}`);
  console.log(`   ppl-bdc push ${slug} --go`);
}

function resolveTargetDir(target) {
  // Soit chemin direct, soit slug, soit dossier dans BDCS_DIR
  if (fs.existsSync(target) && fs.statSync(target).isDirectory()) {
    return target;
  }
  const directMatch = path.join(BDCS_DIR, target);
  if (fs.existsSync(directMatch)) return directMatch;

  // Chercher par slug suffix
  const entries = fs.readdirSync(BDCS_DIR);
  for (const e of entries) {
    if (e.endsWith(`_${target}`) || e === target) {
      return path.join(BDCS_DIR, e);
    }
  }
  die(`Dossier ou BDC introuvable pour "${target}". Lancez 'ppl-bdc pull <url|slug>' d'abord.`);
}

async function cmdAudit(target) {
  const dir = resolveTargetDir(target);
  console.log(`🔍 Audit contractuel DOM/CSS pour : ${dir}`);

  const html = fs.readFileSync(path.join(dir, 'checkout.html'), 'utf8');
  const css = fs.readFileSync(path.join(dir, 'checkout.css'), 'utf8');
  const flowMeta = JSON.parse(fs.readFileSync(path.join(dir, FLOW_META_FILE), 'utf8'));
  const manifest = JSON.parse(fs.readFileSync(path.join(dir, MANIFEST_FILE), 'utf8'));

  const result = auditBdc({ html, css, flowMeta, manifest });

  console.log(`\nRésultats de l'audit (${result.findings.length} constat(s)) :`);
  for (const f of result.findings) {
    const icon = f.severity === SEVERITY.BLOCKER ? '❌' : f.severity === SEVERITY.WARNING ? '⚠️ ' : 'ℹ️ ';
    console.log(`  ${icon} [${f.severity}] ${f.code} : ${f.message}`);
  }

  if (result.valid) {
    console.log(`\n✅ AUDIT CONFORME : 0 Blocker détecté. Ce BDC respecte tous les contrats Pro Funnel.`);
  } else {
    console.log(`\n❌ AUDIT EN ÉCHEC : Des bloqueurs critiques empêchent le déploiement en production.`);
    process.exitCode = 1;
  }

  return result;
}

async function cmdPreview(target, port = 8080) {
  const dir = resolveTargetDir(target);
  const checkoutHtml = fs.readFileSync(path.join(dir, 'checkout.html'), 'utf8');
  const checkoutCss = fs.readFileSync(path.join(dir, 'checkout.css'), 'utf8');
  const thankyouHtml = fs.readFileSync(path.join(dir, 'thankyou.html'), 'utf8');
  const thankyouCss = fs.readFileSync(path.join(dir, 'thankyou.css'), 'utf8');
  const flowMeta = JSON.parse(fs.readFileSync(path.join(dir, FLOW_META_FILE), 'utf8'));

  // Construction d'une enveloppe HTML simulant l'environnement du BDC Pro Funnel Express
  const renderWrapper = (bodyContent, styleContent, title, isThankYou = false) => `<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <title>[PREVIEW LOCALE] ${title}</title>
  <!-- Bootstrap 4 CDN standard Pro Funnel -->
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <style>
    /* Base Pro Funnel Styles */
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; background-color: #f8fafc; }
    .ppl-preview-bar {
      background: #0f172a; color: #fff; padding: 8px 16px; font-size: 13px; font-weight: 600;
      display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 99999;
    }
    .ppl-preview-badge { background: #ea580c; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
  </style>
  <style>
${styleContent}
  </style>
</head>
<body>
  <div class="ppl-preview-bar">
    <div>
      <span class="ppl-preview-badge">LOCAL PREVIEW</span>
      <span>${flowMeta.title || 'BDC Pro Funnel'}</span>
      <span style="opacity: 0.7; margin-left: 8px;">(Partner ${flowMeta.partnerId})</span>
    </div>
    <div>
      <a href="/" style="color: #fff; margin-right: 12px; text-decoration: ${isThankYou ? 'none' : 'underline'};">1. Checkout</a>
      <a href="/merci" style="color: #fff; text-decoration: ${isThankYou ? 'underline' : 'none'};">2. Merci</a>
    </div>
  </div>
  ${!isThankYou ? '<form id="mainForm" method="POST" novalidate="novalidate">' : ''}
    ${bodyContent}
  ${!isThankYou ? '</form>' : ''}
</body>
</html>`;

  const server = http.createServer((req, res) => {
    if (req.url === '/merci') {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(renderWrapper(thankyouHtml, thankyouCss, 'Confirmation de commande', true));
    } else {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(renderWrapper(checkoutHtml, checkoutCss, flowMeta.title, false));
    }
  });

  server.listen(port, () => {
    console.log(`\n🌐 Serveur de prévisualisation démarré sur : http://localhost:${port}`);
    console.log(`   - Étape Checkout : http://localhost:${port}/`);
    console.log(`   - Étape Merci    : http://localhost:${port}/merci`);
    console.log(`\n(Appuyez sur Ctrl+C pour arrêter le serveur)`);
  });
}

async function cmdPush(target, options = {}) {
  const dir = resolveTargetDir(target);
  console.log(`🚀 Préparation du déploiement pour : ${dir}`);

  const manifestPath = path.join(dir, MANIFEST_FILE);
  if (!fs.existsSync(manifestPath)) {
    die(`Fichier ${MANIFEST_FILE} manquant. Lancez 'pull' d'abord.`);
  }

  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  const flowMeta = JSON.parse(fs.readFileSync(path.join(dir, FLOW_META_FILE), 'utf8'));
  const html = fs.readFileSync(path.join(dir, 'checkout.html'), 'utf8');
  const css = fs.readFileSync(path.join(dir, 'checkout.css'), 'utf8');
  const thankyouHtml = fs.readFileSync(path.join(dir, 'thankyou.html'), 'utf8');
  const thankyouCss = fs.readFileSync(path.join(dir, 'thankyou.css'), 'utf8');

  // 1. Calcul du diff SHA-256
  const changedFiles = [];
  const currentFiles = {
    'checkout.html': sha256(html),
    'checkout.css': sha256(css),
    'thankyou.html': sha256(thankyouHtml),
    'thankyou.css': sha256(thankyouCss),
    [FLOW_META_FILE]: sha256(fs.readFileSync(path.join(dir, FLOW_META_FILE), 'utf8'))
  };

  for (const [file, hash] of Object.entries(currentFiles)) {
    if (manifest.files[file] !== hash) {
      changedFiles.push(file);
    }
  }

  if (changedFiles.length === 0) {
    console.log(`Rien à publier : aucun fichier modifié par rapport au dernier pull.`);
    return;
  }

  console.log(`\nFichiers modifiés à publier (${changedFiles.length}) :`);
  for (const f of changedFiles) {
    console.log(`  ~ ${f}`);
  }

  // 1.5. Vérifications d'intégrité fail-closed
  if (manifest.source === 'dom') {
    die("❌ Rejet fail-closed : ce BDC a été extrait depuis le DOM public sans crédentiels API BO. Re-pull avec crédentiels requis avant publication.");
  }
  if (manifest.partnerId && flowMeta.partnerId !== manifest.partnerId) {
    die(`❌ Rejet fail-closed : altération non autorisée de partnerId (${flowMeta.partnerId} != ${manifest.partnerId}).`);
  }
  if (manifest.checkoutStepId && flowMeta.checkout?.stepId !== manifest.checkoutStepId) {
    die(`❌ Rejet fail-closed : altération non autorisée de checkoutStepId.`);
  }
  if (manifest.merciStepId && flowMeta.thankyou?.stepId !== manifest.merciStepId) {
    die(`❌ Rejet fail-closed : altération non autorisée de merciStepId.`);
  }
  if (!flowMeta.flowId || (manifest.flowId && flowMeta.flowId !== manifest.flowId)) {
    die(`❌ Rejet fail-closed : altération ou absence de flowId.`);
  }

  // 2. Audit de conformité obligatoire
  console.log(`\nExécution de l'audit contractuel anti-régression...`);
  const auditResult = auditBdc({ html, css, flowMeta, manifest });
  if (!auditResult.valid) {
    console.error(`\n❌ DÉPLOIEMENT BLOQUÉ : L'audit contractuel a détecté des infractions critiques :`);
    for (const f of auditResult.findings.filter(item => item.severity === SEVERITY.BLOCKER)) {
      console.error(`  - [${f.code}] ${f.message}`);
    }
    die(`Corrigez les infractions avant de redéployer.`);
  }

  // 3. Dry-Run par défaut
  if (!options.go) {
    console.log(`\n[DRY-RUN] L'audit est validé (0 Blocker). Ajoutez '--go' pour publier ces modifications en PROD.`);
    return;
  }

  // 4. Confirmation explicite
  if (!options.yes) {
    const ok = await confirmPrompt(`\nConfirmez-vous le déploiement en PROD de ${changedFiles.length} fichier(s) sur le BDC "${flowMeta.title}" ?`);
    if (!ok) {
      console.log('Déploiement annulé.');
      return;
    }
  }

  // 5. Sauvegarde automatique dans .history/
  const ts = new Date().toISOString().replace(/[-:T.Z]/g, '').slice(0, 14);
  const historyDir = path.join(dir, '.history', ts);
  fs.mkdirSync(historyDir, { recursive: true });
  for (const f of ['checkout.html', 'checkout.css', 'thankyou.html', 'thankyou.css', FLOW_META_FILE]) {
    fs.copyFileSync(path.join(dir, f), path.join(historyDir, f));
  }

  // 6. Déploiement via l'API Pro Funnel BO
  const client = new ProFunnelClient({ partnerId: flowMeta.partnerId });

  // A. Mise à jour de l'étape Checkout si modifiée
  if (changedFiles.includes('checkout.html') || changedFiles.includes('checkout.css')) {
    console.log(`\n↑ Publication des assets Checkout (Step: ${flowMeta.checkout.stepId})...`);
    // Récupération de la version fraîche __v
    const freshStep = await client.getStep(flowMeta.checkout.stepId);
    const freshVersion = freshStep.__v || 0;

    await client.updateStepAssets(
      flowMeta.checkout.stepId,
      { html, css },
      freshVersion
    );
    console.log(`  ✓ Assets Checkout mis à jour avec x-step-version: ${freshVersion}`);
    manifest.checkoutVersion = freshVersion + 1;
  }

  // B. Mise à jour de l'étape Merci si modifiée
  if (changedFiles.includes('thankyou.html') || changedFiles.includes('thankyou.css')) {
    console.log(`\n↑ Publication des assets Merci (Step: ${flowMeta.thankyou.stepId})...`);
    const freshStep = await client.getStep(flowMeta.thankyou.stepId);
    const freshVersion = freshStep.__v || 0;

    await client.updateStepAssets(
      flowMeta.thankyou.stepId,
      { html: thankyouHtml, css: thankyouCss },
      freshVersion
    );
    console.log(`  ✓ Assets Merci mis à jour avec x-step-version: ${freshVersion}`);
    manifest.merciVersion = freshVersion + 1;
  }

  // C. Mise à jour de la configuration de flow si flow.json a changé
  if (changedFiles.includes(FLOW_META_FILE)) {
    console.log(`\n↑ Vérification des métadonnées du step...`);
    const freshStep = await client.getStep(flowMeta.checkout.stepId);
    const paymentMeanChanged = (flowMeta.defaultPaymentMean !== freshStep.defaultPaymentMean) ||
      (JSON.stringify(flowMeta.paymentMeans || ['SEPA', 'CC']) !== JSON.stringify(freshStep.paymentMeans || ['SEPA', 'CC'])) ||
      (flowMeta.checkout?.next !== freshStep.next);

    if (paymentMeanChanged) {
      console.log(`  ↑ Mise à jour des moyens de paiement / routing sur l'étape checkout...`);
      await client.updateStep(flowMeta.checkout.stepId, {
        ...freshStep,
        defaultPaymentMean: flowMeta.defaultPaymentMean || 'SEPA',
        paymentMeans: flowMeta.paymentMeans || ['SEPA', 'CC'],
        next: flowMeta.checkout.next
      }, freshStep.__v);
      console.log(`  ✓ Configuration de la step mise à jour.`);
    } else {
      console.log(`  ℹ️  Aucune modification de paiement/routing dans flow.json. Step checkout préservée.`);
    }
  }

  // D. Invalidation du cache Express par le touch du flow
  console.log(`\n🔄 Invalidation du cache Express (Touch Flow ${flowMeta.flowId})...`);
  await client.touchFlow(flowMeta.flowId);
  console.log(`  ✓ Cache Express invalidé.`);

  // E. Mise à jour du manifeste local
  manifest.files = currentFiles;
  manifest.lastPushedAt = new Date().toISOString();
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), 'utf8');

  const liveUrl = `https://${flowMeta.partnerDomain}/${flowMeta.checkout.slug}?preview=1`;
  console.log(`\n🎉 DÉPLOIEMENT RÉUSSI EN PRODUCTION !`);
  console.log(`   URL live BDC : ${liveUrl}`);
}

async function cmdClone(target, newTitle = '') {
  const { domain, slug } = parseUrlOrSlug(target);
  if (!slug) die('Veuillez fournir une URL ou un slug source valide.');

  let liveDomain = domain || DEFAULT_BDC_DOMAIN;
  if (!liveDomain) {
    die('Veuillez fournir une URL complète (https://<domaine>/<slug>) ou définir PPL_BDC_DOMAIN.');
  }
  const liveUrl = `https://${liveDomain}/${slug}?preview=1`;

  console.log(`📋 Clonage du BDC source depuis ${liveUrl}...`);
  const live = await inspectLiveHtml(liveUrl);
  const partnerId = live.flow.partnerId || DEFAULT_PARTNER_ID;

  const now = new Date();
  const ts = now.toISOString().replace(/[-:T.Z]/g, '').slice(0, 14);
  const finalTitle = newTitle || `CLONE ${live.flow.title || slug} ${ts}`;
  const checkoutSlug = `PPL-${ts}101`;
  const merciSlug = `MERCI-${ts}102`;

  console.log(`\nCréation du nouveau BDC :`);
  console.log(`  Titre         : ${finalTitle}`);
  console.log(`  Checkout Slug : ${checkoutSlug}`);
  console.log(`  Merci Slug    : ${merciSlug}`);
  console.log(`  Partenaire    : ${partnerId} (${liveDomain})`);

  const ok = await confirmPrompt(`\nConfirmez-vous la création de ce nouveau Flow sur Pro Funnel BO ?`);
  if (!ok) {
    console.log('Création annulée.');
    return;
  }

  const client = new ProFunnelClient({ partnerId });

  // 1. Création du Flow
  console.log(`\n1. Création du Flow...`);
  const flowPayload = {
    tags: ['TEST', 'SRC', 'VIBECODE'],
    deleted: false,
    title: finalTitle,
    partnerId,
    redirect: null,
    blurMessage: 'Commande en cours',
    inactiveAt: null,
    sfProductDataExtension: live.flow.sfProductDataExtension || '',
    trigger: live.flow.trigger || '',
    businessUnit: null,
    locale: live.flow.locale || 'fr-FR',
    currency: live.flow.currency || 'EUR'
  };
  const flowData = await client.createFlow(flowPayload);
  const flowId = flowData._id;
  console.log(`   ✓ Flow créé : ${flowId}`);

  // 2. Création de l'Étape Checkout
  console.log(`2. Création de l'Étape Checkout...`);
  const checkoutPayload = {
    offres: [],
    paymentMeans: ['SEPA', 'CC'],
    defaultPaymentMean: 'SEPA',
    deleted: false,
    flow: flowId,
    partnerId,
    type: 'checkout',
    slug: checkoutSlug,
    title: 'Offre Spéciale',
    offers: (live.offers || []).map(o => ({
      offer: o._id || o.id,
      sfExternalKey: '',
      sfExternalKeySepa: '',
      leadcode: ''
    })),
    orderBumps: [],
    grapes: [
      {
        datetime: now.toISOString(),
        user: 'Medi',
        content: {
          'gjs-html': live.gjsHtml || '<body id="grapes-iframe-body"></body>',
          'gjs-css': live.gjsCss || ''
        }
      }
    ]
  };
  const checkoutData = await client.createStep(checkoutPayload);
  const checkoutId = checkoutData._id;
  console.log(`   ✓ Checkout créé : ${checkoutId}`);

  // 3. Création de l'Étape Merci
  console.log(`3. Création de l'Étape Merci...`);
  const merciPayload = {
    offres: [],
    paymentMeans: [],
    deleted: false,
    flow: flowId,
    partnerId,
    type: 'thankyou',
    slug: merciSlug,
    title: 'Merci',
    oae: [],
    offers: [],
    orderBumps: [],
    grapes: [
      {
        datetime: now.toISOString(),
        user: 'Medi',
        content: {
          'gjs-html': '<div class="container py-5 text-center"><h1>✓ Commande confirmée</h1><p>Votre confirmation d\'abonnement vous attend dans votre boîte e-mail.</p></div>',
          'gjs-css': 'body { font-family: sans-serif; background: #f8fafc; }'
        }
      }
    ]
  };
  const merciData = await client.createStep(merciPayload);
  const merciId = merciData._id;
  console.log(`   ✓ Merci créé : ${merciId}`);

  // 4. Liaison next = merciSlug
  console.log(`4. Liaison Checkout -> Merci (${merciSlug})...`);
  await client.updateStep(checkoutId, {
    ...checkoutData,
    next: merciSlug
  });
  console.log(`   ✓ Liaison effectuée.`);

  // 5. Touch du flow pour purge cache
  await client.touchFlow(flowId);

  // 6. Pull local automatique
  console.log(`\n5. Initialisation du miroir local...`);
  await cmdPull(`https://${liveDomain}/${checkoutSlug}`);

  console.log(`\n🎉 NOUVEAU BDC CLONÉ AVEC SUCCÈS !`);
  console.log(`   URL Checkout : https://${liveDomain}/${checkoutSlug}?preview=1`);
  console.log(`   URL Merci    : https://${liveDomain}/${merciSlug}?preview=1`);
  console.log(`   Flow BO      : https://pro-funnel-bo.propulse-lab.com/#/flows/${flowId}`);
}

// ──────────────────────────────── MAIN ────────────────────────────────

async function main() {
  const args = process.argv.slice(2);
  const cmd = args[0];

  if (!cmd || cmd === '--help' || cmd === '-h') {
    console.log(`
ppl-bdc — Vibecoder & gérer les Bons de Commande (Pro Funnel) assisté par IA

Usage :
  ppl-bdc resolve <url|slug>             Inspecte un BDC en lecture seule (Flow, Steps, Offres)
  ppl-bdc pull    <url|slug>             Télécharge le miroir local dans bdcs/<slug>/
  ppl-bdc preview <slug> [--port P]      Prévisualise en local avec wrapper Pro Funnel (:8080)
  ppl-bdc audit   <slug>                 Audit statique des règles et garde-fous contractuels
  ppl-bdc push    <slug>                 DRY-RUN : affiche le diff local vs prod
  ppl-bdc push    <slug> --go [--yes]    Publie en PROD (purge le cache Express public)
  ppl-bdc clone   <url|slug> [--title T] Duplique un BDC éprouvé sous de nouveaux slugs uniques
`);
    return;
  }

  const target = args[1];

  switch (cmd) {
    case 'resolve':
      if (!target) die('Usage : ppl-bdc resolve <url|slug>');
      await cmdResolve(target);
      break;
    case 'pull':
      if (!target) die('Usage : ppl-bdc pull <url|slug>');
      await cmdPull(target);
      break;
    case 'preview':
      if (!target) die('Usage : ppl-bdc preview <slug>');
      const portIdx = args.indexOf('--port');
      const port = portIdx !== -1 && args[portIdx + 1] ? Number(args[portIdx + 1]) : 8080;
      await cmdPreview(target, port);
      break;
    case 'audit':
      if (!target) die('Usage : ppl-bdc audit <slug>');
      await cmdAudit(target);
      break;
    case 'push':
      if (!target) die('Usage : ppl-bdc push <slug> [--go]');
      await cmdPush(target, {
        go: args.includes('--go'),
        yes: args.includes('--yes')
      });
      break;
    case 'clone':
      if (!target) die('Usage : ppl-bdc clone <url|slug> [--title <titre>]');
      const titleIdx = args.indexOf('--title');
      const title = titleIdx !== -1 && args[titleIdx + 1] ? args[titleIdx + 1] : '';
      await cmdClone(target, title);
      break;
    default:
      die(`Commande inconnue : ${cmd}. Lancez 'ppl-bdc --help'.`);
  }
}

main().catch(err => {
  die(err.stack || err.message);
});
