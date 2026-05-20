import {
  getAnalyticsCapex,
  getAnalyticsDashboard,
  getAnalyticsDrilldown,
  getAnalyticsGainAnalysis,
  getAnalyticsHeatmap,
  getAnalyticsImportRisks,
  getAnalyticsProcurement,
  getAnalyticsProcurementLines,
  getAnalyticsProcurementScenarios,
  getAnalyticsRisk,
  getAnalyticsSuppliers,
  getAnalyticsTimeline,
} from "./analyticsService";

const FAMILY_MAP = [
  ["electric", "ELECTRICITE"],
  ["cable", "ELECTRICITE"],
  ["groupe", "ELECTRICITE"],
  ["plomb", "PLOMBERIE"],
  ["pvc", "PLOMBERIE"],
  ["pompe", "PLOMBERIE"],
  ["clim", "HVAC"],
  ["split", "HVAC"],
  ["vrv", "HVAC"],
  ["alu", "MENUISERIE_ALU"],
  ["bois", "MENUISERIE_BOIS"],
  ["carrel", "REVETEMENTS"],
  ["peinture", "REVETEMENTS"],
  ["beton", "GROS_OEUVRE"],
  ["acier", "GROS_OEUVRE"],
  ["vrd", "VRD"],
  ["medical", "EQUIPEMENTS_MEDICAUX"],
  ["camera", "SECURITE"],
  ["ascenseur", "ASCENSEURS"],
  ["cuisine", "CUISINE_PROFESSIONNELLE"],
  ["mobilier", "MOBILIER"],
  ["reseau", "RESEAUX_IT"],
  ["solaire", "ENERGIE_SOLAIRE"],
  ["facade", "FACADE"],
  ["charpente", "CHARPENTE"],
  ["etanche", "ETANCHEITE"],
];

const PRICE_RANGES = {
  ELECTRICITE: [15000, 40000000],
  PLOMBERIE: [2500, 12000000],
  HVAC: [450000, 120000000],
  MENUISERIE_ALU: [180000, 1400000],
  MENUISERIE_BOIS: [180000, 8500000],
  REVETEMENTS: [4500, 90000],
  GROS_OEUVRE: [22000, 1400000],
  VRD: [4500, 220000],
  EQUIPEMENTS_MEDICAUX: [550000, 250000000],
  SECURITE: [45000, 12000000],
  ASCENSEURS: [28000000, 95000000],
  CUISINE_PROFESSIONNELLE: [2500000, 55000000],
  MOBILIER: [65000, 800000],
  RESEAUX_IT: [85000, 4500000],
  ENERGIE_SOLAIRE: [120000, 45000000],
  HYDRAULIQUE: [850000, 65000000],
  FACADE: [12000, 1400000],
  CHARPENTE: [280000, 3200000],
  ETANCHEITE: [18000, 95000],
  AMENAGEMENTS_EXTERIEURS: [8000, 3500000],
};

function number(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function rowAmount(row) {
  return number(row.capex_optimise || row.capex_local || row.capex_brut || row.prix_total_ht || row.value);
}

function classifyFamily(row) {
  const source = `${row.famille || ""} ${row.designation || ""} ${row.lot || ""}`.toLowerCase();
  const match = FAMILY_MAP.find(([keyword]) => source.includes(keyword));
  return match?.[1] || String(row.famille || "NON_CLASSE").toUpperCase().replaceAll(" ", "_");
}

function normalizeLine(row, index) {
  const family = classifyFamily(row);
  const amount = rowAmount(row);
  const [minPrice, maxPrice] = PRICE_RANGES[family] || [0, Math.max(amount * 1.4, 1)];
  const gain = number(row.economie || row.economie_nette || row.gain_net);
  const risk = number(row.risk_score || row.risque || row.GLOBAL_RISK_SCORE, 38 + (index % 5) * 9);
  const decision = String(row.decision_import || row.decision_ia || row.DECISION_FINALE || (gain > 0 ? "IMPORT" : "LOCAL")).toUpperCase();
  const anomalyScore = amount && (amount < minPrice * 0.25 || amount > maxPrice * 1.25) ? 72 : amount < minPrice || amount > maxPrice ? 38 : Math.max(0, risk - 68);
  const financialConfidence = Math.max(8, Math.min(98, 94 - anomalyScore * 0.65));
  const procurementScore = Math.max(15, Math.min(98, number(row.procurement_score || row.PROCUREMENT_SCORE, 70) - risk * 0.12 + (decision === "IMPORT" ? 6 : 0)));
  const roi = amount ? gain / amount : number(row.roi_import || row.ROI);
  return {
    ...row,
    id: row.id_ligne || row.simulation_line_id || `line-${index}`,
    lot: row.lot || "Lot non renseigne",
    famille: family,
    supplier: row.fournisseur || row.fournisseur_chine || row.fournisseur_local || (decision === "IMPORT" ? "Import Chine" : "Marche local"),
    amount,
    gain,
    roi,
    risk_score: risk,
    decision,
    anomaly_score: anomalyScore,
    financial_confidence_score: financialConfidence,
    procurement_score: procurementScore,
    semantic_confidence_score: number(row.semantic_confidence_score, family === "NON_CLASSE" ? 42 : 86),
    benchmark_min: minPrice,
    benchmark_max: maxPrice,
    alert: anomalyScore >= 60 ? "Critique" : anomalyScore >= 30 ? "A surveiller" : "OK",
  };
}

function groupBy(rows, key) {
  const map = new Map();
  rows.forEach((row) => {
    const label = row[key] || "Non renseigne";
    const current = map.get(label) || { label, amount: 0, gain: 0, risk: 0, procurement: 0, confidence: 0, anomalies: 0, rows: 0, importRows: 0 };
    current.amount += row.amount;
    current.gain += row.gain;
    current.risk += row.risk_score;
    current.procurement += row.procurement_score;
    current.confidence += row.financial_confidence_score;
    current.anomalies += row.anomaly_score >= 30 ? 1 : 0;
    current.rows += 1;
    if (row.decision === "IMPORT") current.importRows += 1;
    map.set(label, current);
  });
  return [...map.values()].map((item) => ({
    ...item,
    risk: item.rows ? item.risk / item.rows : 0,
    procurement: item.rows ? item.procurement / item.rows : 0,
    confidence: item.rows ? item.confidence / item.rows : 0,
    importRate: item.rows ? item.importRows / item.rows : 0,
    roi: item.amount ? item.gain / item.amount : 0,
  })).sort((a, b) => b.amount - a.amount);
}

export async function getProcurementCockpit(filters = {}) {
  const requests = [
    getAnalyticsDashboard(filters, "direction"),
    getAnalyticsCapex(filters),
    getAnalyticsProcurement(filters),
    getAnalyticsProcurementLines(filters),
    getAnalyticsSuppliers(filters),
    getAnalyticsProcurementScenarios(filters),
    getAnalyticsGainAnalysis(filters),
    getAnalyticsRisk(filters),
    getAnalyticsHeatmap(filters),
    getAnalyticsTimeline(filters),
    getAnalyticsDrilldown(filters),
    getAnalyticsImportRisks(filters),
  ];
  const results = await Promise.allSettled(requests);
  const [
    dashboard,
    capex,
    procurement,
    procurementLines,
    suppliers,
    scenarios,
    gainAnalysis,
    risks,
    heatmap,
    timeline,
    drilldown,
    importRisks,
  ] = results.map((result) => result.status === "fulfilled" ? result.value : {});

  const rawRows = procurementLines?.table?.length
    ? procurementLines.table
    : procurement?.table?.length
      ? procurement.table
      : dashboard?.table?.length
        ? dashboard.table
        : drilldown?.table || [];
  const lines = rawRows.map(normalizeLine);
  const byLot = groupBy(lines, "lot");
  const byFamily = groupBy(lines, "famille");
  const bySupplier = groupBy(lines, "supplier");
  const capexBrut = lines.reduce((sum, row) => sum + number(row.capex_local || row.amount), 0) || number(capex?.kpis?.capex_brut || dashboard?.kpis?.capex_brut);
  const capexOptimise = lines.reduce((sum, row) => sum + row.amount, 0) || number(capex?.kpis?.capex_optimise || dashboard?.kpis?.capex_optimise);
  const gain = lines.reduce((sum, row) => sum + row.gain, 0) || number(gainAnalysis?.kpis?.gain_net || procurement?.kpis?.economie_nette || dashboard?.kpis?.economie_nette);
  const anomalyCount = lines.filter((row) => row.anomaly_score >= 30).length;
  const avg = (key) => lines.length ? lines.reduce((sum, row) => sum + number(row[key]), 0) / lines.length : 0;

  return {
    metadata: { generatedAt: new Date().toISOString(), currency: "FCFA", source: "analytics-existing-payloads" },
    kpis: {
      capexBrut,
      capexOptimise,
      gain,
      roi: capexBrut ? gain / capexBrut : 0,
      procurementScore: avg("procurement_score"),
      financialConfidence: avg("financial_confidence_score"),
      anomalyScore: avg("anomaly_score"),
      riskScore: avg("risk_score"),
      anomalyCount,
      lineCount: lines.length,
      importRate: lines.length ? lines.filter((row) => row.decision === "IMPORT").length / lines.length : 0,
    },
    lines,
    lots: byLot,
    families: byFamily,
    suppliers: suppliers?.table?.length ? suppliers.table : bySupplier,
    scenarios: scenarios?.table || scenarios?.rankings || [],
    gainAnalysis,
    risks,
    heatmap,
    timeline,
    importRisks,
  };
}
