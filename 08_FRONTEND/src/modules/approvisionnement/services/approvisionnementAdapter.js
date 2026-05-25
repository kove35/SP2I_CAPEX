const ORDER_STATUSES = ["Brouillon", "Consultation", "Validée", "Commandée", "En transit", "Livrée", "Retard"];

function number(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function asArray(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.table)) return payload.table;
  if (Array.isArray(payload?.rows)) return payload.rows;
  if (Array.isArray(payload?.decisions)) return payload.decisions;
  if (Array.isArray(payload?.actions)) return payload.actions;
  return [];
}

function normalizeDecision(value) {
  const normalized = String(value || "").toUpperCase();
  if (normalized.includes("IMPORT")) return "IMPORT";
  if (normalized.includes("HYBRID") || normalized.includes("HYBRIDE") || normalized.includes("MIXTE")) return "HYBRID";
  return "LOCAL";
}

function riskLevel(scoreOrLabel) {
  const label = String(scoreOrLabel || "").toUpperCase();
  const score = number(scoreOrLabel, Number.NaN);
  if (label.includes("CRITICAL") || label.includes("CRITIQUE") || score >= 75) return "Critique";
  if (label.includes("HIGH") || label.includes("ELEVE") || label.includes("ÉLEVÉ") || score >= 58) return "Élevé";
  if (label.includes("MEDIUM") || label.includes("MOYEN") || score >= 35) return "Moyen";
  return "Maîtrisé";
}

function priorityFromRisk(risk) {
  if (risk === "Critique") return "CRITICAL";
  if (risk === "Élevé") return "HIGH";
  if (risk === "Moyen") return "MEDIUM";
  return "LOW";
}

function statusFromDecision(row, index) {
  const validation = String(row.validation_status || "").toUpperCase();
  if (validation === "VALIDATED") return "Validée";
  if (validation === "BLOCKED") return "Retard";
  if (validation === "REVIEW_REQUIRED" || validation === "TO_ARBITRATE") return "Consultation";
  if (row.status) return row.status;
  return ORDER_STATUSES[index % 4];
}

function rowAmount(row) {
  return number(
    row.estimated_import_cost ||
    row.estimated_local_cost ||
    row.capex_optimise ||
    row.capex_local ||
    row.capex_brut ||
    row.amount ||
    row.value
  );
}

export function buildApprovisionnementOrders({ decisions = [], procurementLines = [], procurement = [], dashboard = [] }) {
  const source = decisions.length ? decisions : procurementLines.length ? procurementLines : procurement.length ? procurement : dashboard;
  return source.slice(0, 180).map((row, index) => {
    const decision = normalizeDecision(row.validated_decision || row.proposed_decision || row.ai_decision || row.decision_import || row.decision_ia);
    const risk = riskLevel(row.risk_level || row.risque || row.risk_score || row.GLOBAL_RISK_SCORE);
    return {
      id: row.id || row.simulation_line_id || row.id_ligne || `cmd-${index + 1}`,
      reference: row.reference || `CMD-${String(index + 1).padStart(4, "0")}`,
      lot: row.lot || "Lot non renseigné",
      family: row.family || row.famille || "Famille à qualifier",
      designation: row.designation || row.article || row.label || "Ligne achat",
      supplier: row.supplier_selected || row.fournisseur || row.fournisseur_chine || (decision === "IMPORT" ? "Import consolidé" : "Marché local"),
      amount: rowAmount(row),
      status: statusFromDecision(row, index),
      decision,
      transportMode: decision === "IMPORT" ? "Maritime" : decision === "HYBRID" ? "Mixte" : "Local",
      etaDays: number(row.delivery_eta_days || row.lead_time_total || row.lead_time_days, decision === "IMPORT" ? 68 : 18),
      risk,
      priority: priorityFromRisk(risk),
      validationStatus: row.validation_status || "PENDING",
    };
  });
}

export function buildApprovisionnementSuppliers(orders = []) {
  const suppliers = new Map();
  orders.forEach((order) => {
    const current = suppliers.get(order.supplier) || {
      name: order.supplier,
      country: order.decision === "IMPORT" ? "International" : "Congo-Brazzaville",
      category: order.family,
      amount: 0,
      orders: 0,
      criticalOrders: 0,
      etaTotal: 0,
      incidents: 0,
    };
    current.amount += order.amount;
    current.orders += 1;
    current.etaTotal += order.etaDays;
    if (["Critique", "Élevé"].includes(order.risk)) current.criticalOrders += 1;
    if (["Retard", "Consultation"].includes(order.status)) current.incidents += 1;
    suppliers.set(order.supplier, current);
  });
  return [...suppliers.values()].map((supplier) => {
    const averageEta = supplier.orders ? supplier.etaTotal / supplier.orders : 0;
    const reliability = Math.max(38, Math.round(96 - supplier.incidents * 9 - supplier.criticalOrders * 5));
    return {
      ...supplier,
      averageEta,
      reliability,
      trustScore: Math.max(30, reliability - Math.round(averageEta / 10)),
      dependency: supplier.criticalOrders > 0 && supplier.orders <= 2 ? "Dépendance critique" : "Portefeuille maîtrisé",
    };
  }).sort((a, b) => b.amount - a.amount);
}

export function buildApprovisionnementRisks({ orders = [], importRisks = [], riskRows = [] }) {
  const explicitRisks = importRisks.length ? importRisks : riskRows;
  if (explicitRisks.length) {
    return explicitRisks.slice(0, 24).map((row, index) => ({
      id: row.id || `risk-${index + 1}`,
      lot: row.lot || row.label || "Lot à surveiller",
      label: row.label || row.risque_type || row.risk_type || "Risque approvisionnement",
      impact: number(row.impact || row.capex_expose || row.capex_local || row.value),
      probability: number(row.probability || row.probabilite || row.global_risk_score, 42),
      criticality: number(row.criticite || row.criticality || row.global_risk_score, 42),
      action: row.action || "Qualifier le risque et confirmer le plan de mitigation.",
    }));
  }
  return orders
    .filter((order) => ["Critique", "Élevé"].includes(order.risk))
    .slice(0, 24)
    .map((order, index) => ({
      id: `risk-order-${order.id || index}`,
      lot: order.lot,
      label: order.risk === "Critique" ? "Commande critique" : "Délai à surveiller",
      impact: order.amount,
      probability: order.risk === "Critique" ? 76 : 58,
      criticality: order.risk === "Critique" ? 82 : 62,
      action: `Sécuriser ${order.supplier} et confirmer ETA ${order.etaDays} j.`,
    }));
}

export function buildApprovisionnementTimeline(orders = [], actions = []) {
  const averageEta = orders.length ? orders.reduce((sum, order) => sum + order.etaDays, 0) / orders.length : 0;
  const blocked = actions.filter((action) => String(action.status || "").toUpperCase() === "BLOCKED").length;
  return [
    { date: "J+0", jalon: "Commande", scenario: "Approvisionnement", capex: 0, economie: 0, roi: 0, risque: blocked ? 70 : 35 },
    { date: "J+14", jalon: "Fabrication", scenario: "Approvisionnement", capex: orders.length, economie: 0, roi: 0.04, risque: 42 },
    { date: `J+${Math.max(30, Math.round(averageEta * 0.55))}`, jalon: "Maritime", scenario: "Import", capex: orders.length, economie: 0, roi: 0.07, risque: 55 },
    { date: `J+${Math.max(45, Math.round(averageEta * 0.78))}`, jalon: "Port / douane", scenario: "Logistique", capex: orders.length, economie: 0, roi: 0.08, risque: 58 },
    { date: `J+${Math.max(60, Math.round(averageEta))}`, jalon: "Livraison chantier", scenario: "Exécution", capex: orders.length, economie: 0, roi: 0.1, risque: blocked ? 72 : 48 },
  ];
}

export function buildApprovisionnementDashboard(sources = {}) {
  const procurementLines = asArray(sources.procurementLines);
  const procurement = asArray(sources.procurement);
  const dashboard = asArray(sources.dashboard);
  const decisions = asArray(sources.decisions);
  const actions = asArray(sources.executionActions);
  const importRisks = asArray(sources.importRisks);
  const riskRows = asArray(sources.risk);
  const orders = buildApprovisionnementOrders({ decisions, procurementLines, procurement, dashboard });
  const suppliers = buildApprovisionnementSuppliers(orders);
  const risks = buildApprovisionnementRisks({ orders, importRisks, riskRows });
  const timeline = buildApprovisionnementTimeline(orders, actions);
  const committedBudget = orders.reduce((sum, order) => sum + order.amount, 0);
  const launchedOrders = orders.filter((order) => !["Brouillon", "Consultation"].includes(order.status)).length;
  const criticalOrders = orders.filter((order) => ["Critique", "Élevé"].includes(order.risk)).length;
  const activeSuppliers = suppliers.length;
  const averageEta = orders.length ? orders.reduce((sum, order) => sum + order.etaDays, 0) / orders.length : 0;
  const importOrders = orders.filter((order) => order.decision === "IMPORT").length;
  const blockingLots = new Set(orders.filter((order) => ["Critique", "Retard"].includes(order.risk) || order.status === "Retard").map((order) => order.lot)).size;
  const containers = Math.max(0, Math.ceil(importOrders / 18));
  const riskScore = orders.length ? Math.min(100, Math.round((criticalOrders / orders.length) * 100 + averageEta * 0.25)) : 0;
  const workflow = sources.workflow || {};
  const recommendations = [
    containers > 1 ? "Mutualiser les containers des lots import à forte densité CAPEX." : "Conserver une consolidation logistique légère sur les lots import.",
    criticalOrders ? "Prioriser la revue fournisseur sur les commandes critiques avant engagement." : "Les commandes critiques restent limitées sur le périmètre actif.",
    workflow.procurement?.status === "REVIEW_REQUIRED" ? "Valider les arbitrages achat pour fiabiliser le dossier approvisionnement." : "Maintenir le suivi des validations achat et des ETA chantier.",
    workflow.execution?.status === "REQUIRED" ? "Préparer les actions chantier associées aux livraisons sensibles." : "Partager les risques logistiques avec le pilotage chantier.",
  ];

  return {
    kpis: {
      committedBudget,
      launchedOrders,
      criticalOrders,
      activeSuppliers,
      averageEta,
      riskScore,
      blockingLots,
      containers,
    },
    orders,
    suppliers,
    risks,
    timeline,
    logistics: {
      containers,
      importOrders,
      localOrders: orders.filter((order) => order.decision === "LOCAL").length,
      hybridOrders: orders.filter((order) => order.decision === "HYBRID").length,
      averageEta,
      customsStatus: criticalOrders ? "À surveiller" : "Planifié",
      transportCost: Math.round(committedBudget * 0.08),
    },
    recommendations,
    alerts: risks.slice(0, 5),
    metadata: {
      generatedAt: new Date().toISOString(),
      source: decisions.length ? "procurement_decisions" : "analytics_fallback",
    },
  };
}
