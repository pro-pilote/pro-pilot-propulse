/**
 * lib/bdc-rules.mjs — Source Unique de Vérité (SSOT) des règles contractuelles BDC Pro Funnel.
 *
 * Valide la conformité DOM/CSS d'un BDC avant déploiement (audit statique)
 * pour interdire toute régression en production (fail-closed).
 */

export const SEVERITY = {
  BLOCKER: 'BLOCKER',
  WARNING: 'WARNING',
  INFO: 'INFO'
};

const CONTRACTUAL_BILLING_IDS = [
  'billing_nom',
  'billing_prenom',
  'billing_email',
  'billing_postalCode',
  'billing_locality',
  'billing_country'
];

/**
 * Audit complet d'un BDC (HTML, CSS et métadonnées de flow).
 * @param {Object} params
 * @param {string} params.html - Contenu GrapesJS HTML (ex: checkout.html)
 * @param {string} params.css - Contenu GrapesJS CSS (ex: checkout.css)
 * @param {Object} params.flowMeta - Métadonnées (flow.json)
 * @param {Object} [params.manifest] - Manifeste du pull pour contrôle de non-régression
 * @returns {{ valid: boolean, findings: Array<{ severity: string, code: string, message: string }> }}
 */
export function auditBdc({ html = '', css = '', flowMeta = {}, manifest = null }) {
  const findings = [];

  const addFinding = (severity, code, message) => {
    findings.push({ severity, code, message });
  };

  // 1. RÈGLE CRITIQUE : Interdiction formelle de <form> ou <form id="mainForm"> dans le layout
  // Le serveur Express wrap déjà le corps avec <form method="POST" id="mainForm">.
  if (/<form[\s>]/i.test(html)) {
    addFinding(
      SEVERITY.BLOCKER,
      'ERR_NESTED_FORM',
      'Balise <form> détectée dans le HTML GrapesJS. Le serveur Express injecte déjà <form id="mainForm"> autour du contenu. Les formulaires imbriqués provoquent le détachement du DOM par le navigateur et brisent la soumission.'
    );
  }

  // 2. RÈGLE CRITIQUE : Isolation à 3 niveaux de #shipping-checkbox
  // Sur les offres virtuelles, le bundle exécute : $("#shipping-checkbox").parent().parent().parent().hide()
  if (html.includes('id="shipping-checkbox"') || html.includes("id='shipping-checkbox'")) {
    const shippingIdx = html.indexOf('shipping-checkbox');
    const beforeShipping = html.slice(0, shippingIdx);
    
    // Compter les balises conteneurs ouvrantes immédiatement parentes
    const parentMatches = [...beforeShipping.matchAll(/<(div|fieldset|section|span)[^>]*>/gi)];
    const last3Parents = parentMatches.slice(-3);
    
    // Vérifier si un conteneur parent porte une classe de facturation ou contient les champs billing
    const hasBillingParent = last3Parents.some(p => 
      /class=["'][^"']*(billing|facturation|main-container)[^"']*/i.test(p[0])
    );

    if (last3Parents.length < 3 || hasBillingParent) {
      addFinding(
        SEVERITY.BLOCKER,
        'ERR_SHIPPING_ISOLATION',
        '#shipping-checkbox n\'est pas enfermé dans 3 conteneurs neutres d\'isolation. Le bundle JS exécute inconditionnellement .parent().parent().parent().hide() sur les offres virtuelles : sans isolation, le 3e parent remonte jusqu\'au bloc facturation et le fait disparaître.'
      );
    }
  }

  // 3. RÈGLE CRITIQUE : Conflit CSS .d-none vs display: block sur les inputs (autocomplétion La Poste)
  // Ne jamais mettre !important sur display: block des inputs ou .form-control
  const displayBlockImportantRegex = /(\.form-control|\.ppl-input|input|select)[^{}]*\{[^{}]*display\s*:\s*block\s*!important/gi;
  if (displayBlockImportantRegex.test(css)) {
    addFinding(
      SEVERITY.BLOCKER,
      'ERR_CSS_DISPLAY_BLOCK_IMPORTANT',
      'Présence de "display: block !important" sur les champs de formulaire ou .form-control. Cette règle supplante .d-none lors de l\'injection du select de ville La Poste (#billing_locality_select) et affiche deux champs ville superposés.'
    );
  }

  // Vérifier la présence de la règle forçant la primauté de .d-none
  if (!/\.d-none[^{}]*\{[^{}]*display\s*:\s*none\s*!important/i.test(css)) {
    addFinding(
      SEVERITY.WARNING,
      'WARN_CSS_D_NONE_PRIORITY',
      'Règle de primauté ".d-none { display: none !important; }" recommandée absente de la feuille de style pour sécuriser l\'autocomplétion La Poste.'
    );
  }

  // 4. RÈGLE CRITIQUE : next step slug obligatoire (jamais d'ObjectId MongoDB)
  const checkoutStep = flowMeta.checkout || flowMeta.steps?.find(s => s.type === 'checkout') || {};
  if (checkoutStep.next) {
    if (/^[a-f0-9]{24}$/i.test(checkoutStep.next)) {
      addFinding(
        SEVERITY.BLOCKER,
        'ERR_NEXT_STEP_IS_OBJECTID',
        `Le champ "next" de l'étape checkout contient un ObjectId MongoDB ("${checkoutStep.next}"). Il doit OBLIGATOIREMENT contenir le slug de l'étape merci (ex: "MERCI-2026..."). Un ObjectId provoque une 404 lors du paiement et fige la commande.`
      );
    } else if (!checkoutStep.next.startsWith('MERCI-') && !checkoutStep.next.includes('-')) {
      addFinding(
        SEVERITY.WARNING,
        'WARN_NEXT_STEP_SLUG_FORMAT',
        `Le slug "next" ("${checkoutStep.next}") ne suit pas le préfixe conventionnel "MERCI-".`
      );
    }
  }

  // 5. RÈGLE CRITIQUE : defaultPaymentMean obligatoire
  if (checkoutStep && !checkoutStep.defaultPaymentMean && !flowMeta.defaultPaymentMean) {
    addFinding(
      SEVERITY.BLOCKER,
      'ERR_MISSING_DEFAULT_PAYMENT_MEAN',
      'Le champ "defaultPaymentMean" est manquant dans la configuration de l\'étape checkout (obligatoire: "SEPA" ou "CC"). Sans ce champ, l\'engine JS front plante avec "Cannot read properties of undefined (reading \'setCustomValidity\')".'
    );
  }

  // 6. RÈGLE CONTRACTUELLE : Présence des IDs DOM contractuels
  const missingBillingIds = CONTRACTUAL_BILLING_IDS.filter(id => !html.includes(`id="${id}"`) && !html.includes(`id='${id}'`));
  if (missingBillingIds.length > 0) {
    addFinding(
      SEVERITY.BLOCKER,
      'ERR_MISSING_CONTRACTUAL_IDS',
      `Identifiants DOM contractuels de facturation manquants : ${missingBillingIds.map(id => `#${id}`).join(', ')}.`
    );
  }

  // Vérifier la présence du bouton de paiement / soumission
  const hasPaymentTrigger = html.includes('id="paymentModalButton"') || 
                            html.includes('class="payment-submit"') ||
                            html.includes('type="submit"');
  if (!hasPaymentTrigger) {
    addFinding(
      SEVERITY.BLOCKER,
      'ERR_MISSING_SUBMIT_TRIGGER',
      'Aucun déclencheur de paiement ou de soumission trouvé (#paymentModalButton ou .payment-submit ou button[type="submit"]).'
    );
  }

  // 7. RÈGLE CONTRACTUELLE : Intégrité des offres (radios name="product" et id="offre-<id>")
  const radioOffersMatches = [...html.matchAll(/name=["']product["'][^>]*id=["']offre-([a-f0-9]{24}|[^"']+)["']/gi)];
  const radioOfferIds = new Set(radioOffersMatches.map(m => m[1]));

  const declaredOffers = (checkoutStep.offers || flowMeta.offers || []).map(o => (typeof o === 'string' ? o : o.offer || o.id || o._id));
  if (declaredOffers.length > 0 && radioOfferIds.size > 0) {
    const undeclaredRadios = [...radioOfferIds].filter(id => !declaredOffers.includes(id));
    if (undeclaredRadios.length > 0) {
      addFinding(
        SEVERITY.BLOCKER,
        'ERR_RADIO_OFFER_MISMATCH',
        `Des radios pointent vers des offres non déclarées dans la step : ${undeclaredRadios.join(', ')}.`
      );
    }
  }

  // 8. RÈGLE DE NON-RÉGRESSION : Vérifier qu'aucun ID présent au pull n'a été supprimé
  if (manifest && Array.isArray(manifest.contractualIds)) {
    const lostIds = manifest.contractualIds.filter(id => !html.includes(`id="${id}"`) && !html.includes(`id='${id}'`));
    if (lostIds.length > 0) {
      addFinding(
        SEVERITY.BLOCKER,
        'ERR_REGRESSION_LOST_IDS',
        `Régression détectée : des IDs DOM présents lors du pull initial ont disparu : ${lostIds.map(id => `#${id}`).join(', ')}.`
      );
    }
  }

  // 9. RÈGLE DE SYNTAXE : Équilibre des balises et commentaires
  const openComments = (html.match(/<!--/g) || []).length;
  const closeComments = (html.match(/-->/g) || []).length;
  if (openComments !== closeComments) {
    addFinding(
      SEVERITY.BLOCKER,
      'ERR_UNBALANCED_HTML_COMMENTS',
      `Déséquilibre dans les commentaires HTML : ${openComments} '<!--' contre ${closeComments} '-->'.`
    );
  }

  // 10. RÈGLE D'UNICITÉ : Pas d'IDs en doublon
  const idMatches = [...html.matchAll(/\bid=["']([^"']+)["']/gi)].map(m => m[1]);
  const seenIds = new Set();
  const duplicateIds = new Set();
  for (const id of idMatches) {
    // Tolérance pour les modales dupliquées internes si expressément gérées, mais signalement strict pour les inputs
    if (seenIds.has(id)) {
      duplicateIds.add(id);
    }
    seenIds.add(id);
  }
  if (duplicateIds.size > 0) {
    const criticalDuplicates = [...duplicateIds].filter(id => id.startsWith('billing_') || id === 'paymentModalButton' || id === 'mainForm');
    if (criticalDuplicates.length > 0) {
      addFinding(
        SEVERITY.BLOCKER,
        'ERR_DUPLICATE_CRITICAL_IDS',
        `Identifiants critiques en doublon dans le DOM : ${criticalDuplicates.map(id => `#${id}`).join(', ')}.`
      );
    } else {
      addFinding(
        SEVERITY.WARNING,
        'WARN_DUPLICATE_IDS',
        `Identifiants HTML dupliqués détectés : ${[...duplicateIds].slice(0, 5).join(', ')}${duplicateIds.size > 5 ? '...' : ''}.`
      );
    }
  }

  const hasBlockers = findings.some(f => f.severity === SEVERITY.BLOCKER);

  return {
    valid: !hasBlockers,
    findings
  };
}

/**
 * Extrait tous les identifiants DOM présents dans un contenu HTML.
 * @param {string} html 
 * @returns {string[]}
 */
export function extractDomIds(html) {
  const matches = [...html.matchAll(/\bid=["']([^"']+)["']/gi)];
  return [...new Set(matches.map(m => m[1]))].sort();
}
