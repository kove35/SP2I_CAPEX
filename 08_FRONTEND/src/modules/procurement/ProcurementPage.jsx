import React from "react";
import AnalyticsCard from "../../ui/AnalyticsCard";
import KpiCard from "../../ui/KpiCard";
import BIChart from "../../components/charts/BIChart";
import ImportDecisionSankey from "../../components/charts/ImportDecisionSankey";
import RiskMatrix from "../../components/charts/RiskMatrix";
import SmartDataGrid from "../../components/grids/SmartDataGrid";
import { useAnalyticsEngine } from "../../hooks/useAnalyticsEngine";
import { useCrossFiltering } from "../../hooks/useCrossFiltering";
import { useWorkflow } from "../../hooks/useWorkflow";
import { exportAnalyticsGainAnalysis, exportAnalyticsProcurementFile } from "../../services/analyticsService";
import { formatCurrency, formatMoney, formatPercent } from "../../shared/formatters";
import { normalizeDecision, normalizeFamily, toBusinessLabel } from "../../utils/analyticsLabels";
import { useAppStore } from "../../store/appStore.jsx";
import { getScenarioContext, PROJECT_CONTEXT } from "../../utils/businessContext";
import { exportProcurementWorkbook, saveLocalProjects } from "../../services/projectService";
import WorkflowGuardEmptyState from "../projects/WorkflowGuardEmptyState";
import SmartWorkflowActions from "../projects/SmartWorkflowActions";

const LANDED_COST_RATES = [
  ["Transport maritime", 0.15],
  ["Assurance", 0.02],
  ["Droits de douane", 0.2],
  ["Frais portuaires", 0.1],
  ["Transport local chantier", 0.05],
];

const STRATEGIES = [
  { label: "100% local", importShare: 0, risk: "Faible", lead: "14 j", description: "Securise les delais, limite les gains." },
  { label: "Equilibre local / import", importShare: 0.45, risk: "Maitrise", lead: "45 j", description: "Cible les lots rentables sans exposer le chantier." },
  { label: "Import agressif", importShare: 0.75, risk: "Eleve", lead: "75 j", description: "Maximise les economies avec pilotage logistique renforce." },
  { label: "Securisation logistique", importShare: 0.55, risk: "Moyen", lead: "60 j", description: "Optimise les achats critiques avec buffers chantier." },
];
const DQE_READY_STATUSES = ["SYNCED", "CERTIFIED", "CERTIFIED_WITH_WARNINGS"];

function displayScope(value) {
  const normalized = String(value || "").trim();
  if (!normalized || normalized.toLowerCase() === "default") return "Projet complet";
  return toBusinessLabel(normalized, "Projet complet");
}

function readDqeVersions(projectId) {
  try {
    const stored = window.localStorage.getItem(`sp2i:dqeVersions:${projectId || PROJECT_CONTEXT.code}`);
    if (stored) {
      const parsed = JSON.parse(stored);
      return Array.isArray(parsed) ? parsed : [];
    }
  } catch {
    return [];
  }

  if ((projectId || PROJECT_CONTEXT.code) === PROJECT_CONTEXT.code) {
    return [{
      id: "seed-dqe-v1",
      version_number: 1,
      file_name: "DQE_PROJECT_SP2I.xlsx",
      status: "SYNCED",
      trust_score: 87,
      normalized_lines_count: 46,
      data_loss_count: 0,
      review_required_count: 0,
      is_active: true,
    }];
  }
  return [];
}

function getProcurementSourceContext(projectId, scenarioCode, lastSimulation) {
  const versions = readDqeVersions(projectId);
  const activeDqe = versions.find((version) => version.is_active && DQE_READY_STATUSES.includes(version.status));
  const scenario = getScenarioContext(scenarioCode);
  return {
    hasActiveDqe: Boolean(activeDqe),
    dqeLabel: activeDqe ? `DQE v${activeDqe.version_number}` : "Aucun DQE actif",
    dqeStatus: activeDqe?.status === "CERTIFIED" ? "Certifie" : activeDqe?.status === "CERTIFIED_WITH_WARNINGS" ? "Certifie avec points a verifier" : activeDqe?.status === "SYNCED" ? "Synchronise" : "Non disponible",
    trustScore: activeDqe?.trust_score,
    lines: activeDqe?.normalized_lines_count,
    dataLoss: activeDqe?.data_loss_count,
    reviewRequired: activeDqe?.review_required_count,
    scenarioLabel: scenario.label,
    scenarioStatus: lastSimulation ? "Simule" : "A lancer",
  };
}

function decisionUiLabel(value) {
  const decision = String(value || "").toUpperCase();
  if (decision === "IMPORT") return "Importer";
  if (decision === "LOCAL") return "Acheter local";
  if (decision === "HYBRIDE" || decision === "HYBRID" || decision === "MIXTE") return "Hybride";
  if (decision === "ESCALATED" || decision === "REVIEW_REQUIRED") return "Escalade direction";
  if (decision === "BLOCKED") return "Bloquant";
  return value || "A arbitrer";
}

function decisionUiClass(value) {
  const decision = String(value || "").toUpperCase();
  if (decision === "MIXTE") return "hybride";
  return decision.toLowerCase().replaceAll("_", "-") || "review-required";
}

function decisionJustification(row) {
  if (row?.justification_humaine) return row.justification_humaine;
  const decision = String(row?.decision_ia || row?.decision_import || "").toUpperCase();
  const roi = Number(row?.roi_import || 0);
  const risk = Number(row?.risque || 0);
  if (decision === "IMPORT") return "Import recommande : ROI positif et risque logistique a confirmer.";
  if (decision === "LOCAL") return "Local recommande : delai chantier, SAV ou gain import insuffisant.";
  if (decision === "HYBRIDE" || decision === "MIXTE") return "Hybride recommande : standard importable, points critiques a conserver ou verifier localement.";
  if (risk >= 70) return "Validation requise : risque achat ou logistique eleve.";
  if (roi > 0) return "Decision a verifier : gain detecte mais validation achat necessaire.";
  return "Validation achat requise avant decision finale.";
}

function procurementRowKey(row, index = 0) {
  return String(
    row?.id_ligne ||
    row?.procurement_action_id ||
    row?.article_id ||
    row?.ifc_guid ||
    `${row?.lot || "lot"}-${row?.designation || "ligne"}-${index}`
  );
}

function rowValue(row) {
  return Number(row.capex_optimise || row.capex_local || row.capex_brut || row.value || 0);
}

function getRows(procurementData, dashboardData) {
  const procurementRows = procurementData?.table || [];
  if (procurementRows.length) return procurementRows;
  return dashboardData?.table || [];
}

function buildSupplierRows(rows = []) {
  const map = new Map();
  rows.forEach((row) => {
    const supplier = normalizeFamily(row.famille || "Classification en attente");
    const decision = normalizeDecision(row.decision_import || "LOCAL");
    const current = map.get(supplier) || {
      supplier,
      country: decision === "IMPORT" ? "Chine / Europe" : "Congo-Brazzaville",
      capex: 0,
      gain: 0,
      rows: 0,
      importRows: 0,
    };
    current.capex += rowValue(row);
    current.gain += Number(row.economie || row.economie_nette || 0);
    current.rows += 1;
    if (decision === "IMPORT") current.importRows += 1;
    map.set(supplier, current);
  });
  return [...map.values()]
    .map((item) => {
      const importRate = item.rows ? item.importRows / item.rows : 0;
      const roi = item.capex ? item.gain / item.capex : 0;
      const lead = importRate > 0.6 ? 75 : importRate > 0.25 ? 45 : 14;
      const reliability = Math.max(62, Math.round(94 - importRate * 18 + roi * 80));
      return {
        ...item,
        importRate,
        roi,
        lead,
        quality: Math.min(98, reliability + 4),
        reliability,
        score: Math.round((reliability + Math.min(100, roi * 500) + (100 - Math.min(lead, 90))) / 3),
      };
    })
    .sort((a, b) => b.capex - a.capex)
    .slice(0, 12);
}

function buildLotRows(rows = []) {
  const map = new Map();
  rows.forEach((row) => {
    const lot = toBusinessLabel(row.lot, "Lot non renseigne");
    const current = map.get(lot) || { lot, capex: 0, gain: 0, rows: 0, importRows: 0 };
    current.capex += rowValue(row);
    current.gain += Number(row.economie || row.economie_nette || 0);
    current.rows += 1;
    if (normalizeDecision(row.decision_import) === "IMPORT") current.importRows += 1;
    map.set(lot, current);
  });
  return [...map.values()].map((item) => ({
    ...item,
    roi: item.capex ? item.gain / item.capex : 0,
    importRate: item.rows ? item.importRows / item.rows : 0,
  })).sort((a, b) => b.gain - a.gain);
}

function landedCostRows(kpis = {}) {
  const importBase = Number(kpis.capex_brut || 0) * Number(kpis.taux_importable || 0) * 0.5;
  return LANDED_COST_RATES.map(([label, rate]) => ({
    label,
    rate,
    value: importBase * rate,
  }));
}

function buildContainerRows(rows = []) {
  const importRows = rows.filter((row) => normalizeDecision(row.decision_import) === "IMPORT");
  const grouped = buildLotRows(importRows).slice(0, 8);
  return grouped.map((item, index) => {
    const capacity = 42_000_000;
    const fill = Math.min(item.capex / capacity, 0.98);
    return {
      id: `CNT-${String(index + 1).padStart(3, "0")}`,
      lot: item.lot,
      capacity,
      fill,
      eta: `${45 + index * 4} j`,
      status: fill > 0.85 ? "A consolider" : "Planifie",
    };
  });
}

function buildInsights(kpis, lots, suppliers) {
  const bestLot = lots[0];
  const bestSupplier = suppliers[0];
  const economy = Number(kpis.economie_nette || 0);
  return [
    bestLot
      ? `${bestLot.lot} concentre ${formatMoney(bestLot.gain)} de gains potentiels a securiser.`
      : "Les gains achat apparaitront apres synchronisation du DQE.",
    `La strategie import represente ${formatPercent(kpis.taux_importable || 0)} des lignes exploitables.`,
    bestSupplier
      ? `${bestSupplier.supplier} est le portefeuille fournisseur prioritaire avec un score ${bestSupplier.score}/100.`
      : "Aucun portefeuille fournisseur prioritaire detecte.",
    economy > 0
      ? `Les arbitrages local/import reduisent le budget de ${formatMoney(economy)}.`
      : "Les economies seront calculees apres alimentation de FACT_METRE.",
  ];
}

function buildActiveAnalysis(rows = [], filters = {}, drilldownTarget = null, globalKpis = {}) {
  const activeLabel = displayScope(filters.lot || filters.famille || filters.importLocal || drilldownTarget?.selectedLabel || "");
  const scopedRows = rows.length ? rows : [];
  const capexLocal = scopedRows.reduce((sum, row) => sum + Number(row.capex_local || row.capex_brut || rowValue(row) || 0), 0);
  const capexImport = scopedRows.reduce((sum, row) => sum + Number(row.capex_import || 0), 0);
  const capexOptimise = scopedRows.reduce((sum, row) => sum + Number(row.capex_optimise || rowValue(row) || 0), 0);
  const gain = scopedRows.reduce((sum, row) => sum + Number(row.economie || row.economie_nette || 0), 0);
  const importRows = scopedRows.filter((row) => normalizeDecision(row.decision_import) === "IMPORT").length;
  const importRate = scopedRows.length ? importRows / scopedRows.length : Number(globalKpis.taux_importable || 0);
  const roi = capexLocal ? gain / capexLocal : Number(globalKpis.roi_import || 0);
  const familyCount = new Map();
  scopedRows.forEach((row) => {
    const family = normalizeFamily(row.famille || "Classification en attente");
    familyCount.set(family, (familyCount.get(family) || 0) + rowValue(row));
  });
  const mainSupplier = displayScope([...familyCount.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] || drilldownTarget?.selectedLabel || "A confirmer");
  const delay = importRate > 0.6 ? 75 : importRate > 0.25 ? 45 : 14;
  const risk = importRate > 0.65 ? "Eleve" : importRate > 0.3 ? "Maitrise" : "Faible";
  const containers = Math.max(1, Math.ceil(capexOptimise / 42_000_000));
  const share = Number(globalKpis.capex_brut || 0) ? capexLocal / Number(globalKpis.capex_brut || 1) : 0;

  return {
    activeLabel,
    capexLocal,
    capexImport,
    capexOptimise,
    gain,
    importRate,
    roi,
    mainSupplier,
    delay,
    risk,
    containers,
    share,
    dependency: delay >= 60 ? "Critique planning" : delay >= 30 ? "A suivre" : "Faible",
    localExtraCost: Math.max(capexLocal - capexOptimise, 0),
  };
}

function buildGainWaterfallOption(items = [], currency = "FCFA") {
  const labels = items.map((item) => item.label);
  let cumulative = 0;
  const helpers = [];
  const bars = [];
  const colors = [];
  const rawValues = [];

  items.forEach((item) => {
    const value = Number(item.value || 0);
    rawValues.push(value);
    if (item.type === "total" || item.type === "final") {
      helpers.push(0);
      bars.push(Math.abs(value));
      cumulative = item.type === "total" ? value : cumulative;
    } else if (value < 0) {
      helpers.push(Math.max(cumulative + value, 0));
      bars.push(Math.abs(value));
      cumulative += value;
    } else {
      helpers.push(Math.max(cumulative, 0));
      bars.push(value);
      cumulative += value;
    }
    colors.push(
      item.type === "gain" ? "#34d399" :
      item.type === "risk" || item.type === "cost" ? "#fb7185" :
      item.type === "final" ? "#f59e0b" :
      "#67e8c9"
    );
  });

  return {
    backgroundColor: "transparent",
    grid: { left: 24, right: 18, top: 20, bottom: 70, containLabel: true },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params = []) => {
        const index = params[1]?.dataIndex ?? 0;
        return `<b>${labels[index]}</b><br/>Montant : ${formatCurrency(Math.abs(rawValues[index] || 0), currency)}`;
      },
    },
    xAxis: {
      type: "category",
      data: labels,
      axisLabel: { color: "#9fb4d1", rotate: 28, fontSize: 10 },
      axisLine: { lineStyle: { color: "rgba(148,163,184,.2)" } },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#9fb4d1", formatter: (value) => `${Math.round(value / 1_000_000)}M` },
      splitLine: { lineStyle: { color: "rgba(148,163,184,.12)" } },
    },
    series: [
      {
        name: "Base",
        type: "bar",
        stack: "waterfall",
        itemStyle: { color: "transparent" },
        emphasis: { disabled: true },
        data: helpers,
      },
      {
        name: "Montant",
        type: "bar",
        stack: "waterfall",
        barWidth: 28,
        data: bars.map((value, index) => ({
          value,
          itemStyle: {
            color: colors[index],
            borderRadius: [5, 5, 0, 0],
            shadowBlur: 12,
            shadowColor: `${colors[index]}55`,
          },
        })),
        label: {
          show: true,
          position: "top",
          color: "#e5edf5",
          fontSize: 10,
          formatter: (params) => formatCurrency(Math.abs(rawValues[params.dataIndex] || 0), currency),
        },
      },
    ],
  };
}

function buildDecisionWaterfallOption(items = [], currency = "FCFA") {
  return buildGainWaterfallOption(items, currency);
}

function GainPotentialCard({ gainAnalysis, fallbackGain, currency, onOpen }) {
  const kpis = gainAnalysis?.kpis || {};
  const gainNet = Number(kpis.gain_net || fallbackGain || 0);
  const confidence = Number(kpis.confiance || 0);
  return (
    <article className="gain-potential-card">
      <div>
        <span>Gain net securisable</span>
        <strong>{formatCurrency(gainNet, currency)}</strong>
        <small>Perimetre : scenario actif. Apres transport, douane, assurance, logistique et risques estimes.</small>
      </div>
      <div className="gain-confidence-ring">
        <b>{formatPercent(confidence)}</b>
        <small>Confiance</small>
      </div>
      <button type="button" onClick={onOpen}>Detail du gain securisable</button>
    </article>
  );
}

function GainDetailDrawer({ analysis, filters, currency, onClose }) {
  const [transportDelta, setTransportDelta] = React.useState(0);
  const [currencyDelta, setCurrencyDelta] = React.useState(0);
  const kpis = analysis?.kpis || {};
  const charts = analysis?.charts || {};
  const metadata = analysis?.metadata || {};
  const adjustedGain = Math.max(
    Number(kpis.gain_net || 0) - Number(kpis.cout_import_final || 0) * (transportDelta / 100) * 0.08 - Number(kpis.capex_import_fob || 0) * (currencyDelta / 100) * 0.05,
    0
  );

  const handleExport = async () => {
    const blob = await exportAnalyticsGainAnalysis(filters);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "SP2I_detail_gain_potentiel.xlsx";
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="gain-detail-overlay" role="presentation" onClick={onClose}>
      <aside className="gain-detail-drawer" role="dialog" aria-modal="true" aria-label="Detail du gain potentiel" onClick={(event) => event.stopPropagation()}>
        <header>
          <div>
            <span>Audit financier SP2I</span>
            <h2>Detail du gain potentiel</h2>
            <p>{metadata.formula}</p>
          </div>
          <button type="button" onClick={onClose}>Fermer</button>
        </header>

        <section className="gain-detail-kpis">
          <span><b>{formatCurrency(kpis.capex_local, currency)}</b> CAPEX local</span>
          <span><b>{formatCurrency(kpis.capex_import_fob, currency)}</b> Import FOB</span>
          <span><b>{formatCurrency(kpis.cout_import_final, currency)}</b> Cout import final</span>
          <span><b>{formatCurrency(kpis.gain_net, currency)}</b> Economie nette</span>
          <span><b>{formatPercent(kpis.roi_net)}</b> ROI net</span>
          <span><b>{formatPercent(kpis.confiance)}</b> Confiance</span>
        </section>

        <section className="gain-detail-grid">
          <article className="gain-detail-panel wide">
            <div className="panel-heading">
              <span>Cascade financiere</span>
              <strong>Du CAPEX local au gain net</strong>
            </div>
            <BIChart option={buildGainWaterfallOption(charts.waterfall || [], currency)} height={300} chartKey={`gain-${kpis.gain_net || 0}-${currency}`} />
          </article>

          <article className="gain-detail-panel">
            <div className="panel-heading">
              <span>Scenarios</span>
              <strong>Fourchette decisionnelle</strong>
            </div>
            <div className="gain-scenario-list">
              {(charts.scenarios || []).map((scenario) => (
                <div key={scenario.label}>
                  <b>{scenario.label}</b>
                  <strong>{formatCurrency(scenario.value, currency)}</strong>
                  <small>{scenario.description}</small>
                </div>
              ))}
            </div>
          </article>

          <article className="gain-detail-panel">
            <div className="panel-heading">
              <span>Sensibilite</span>
              <strong>{formatCurrency(adjustedGain, currency)}</strong>
            </div>
            <label>
              Transport +{transportDelta}%
              <input type="range" min="0" max="40" value={transportDelta} onChange={(event) => setTransportDelta(Number(event.target.value))} />
            </label>
            <label>
              Devise +{currencyDelta}%
              <input type="range" min="0" max="25" value={currencyDelta} onChange={(event) => setCurrencyDelta(Number(event.target.value))} />
            </label>
            <small>Variation possible : {formatCurrency(charts.sensitivity?.min || 0, currency)} a {formatCurrency(charts.sensitivity?.max || 0, currency)}</small>
          </article>
        </section>

        <section className="gain-detail-table">
          <div className="panel-heading">
            <span>Calcul audit-proof</span>
            <strong>Couts inclus dans le gain net</strong>
          </div>
          <table className="data-table">
            <thead><tr><th>Poste</th><th>Montant</th><th>Explication</th></tr></thead>
            <tbody>
              {(analysis?.table || []).map((row) => (
                <tr key={row.label}>
                  <td>{row.label}</td>
                  <td>{formatCurrency(row.value, currency)}</td>
                  <td>{row.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="gain-risk-story">
          <article>
            <div className="panel-heading">
              <span>Risques impactant le gain</span>
              <strong>Impacts financiers potentiels</strong>
            </div>
            {(charts.risks || []).map((risk) => (
              <div className="gain-risk-row" key={risk.label}>
                <span>{risk.label}</span>
                <b>{formatCurrency(risk.impact, currency)}</b>
                <small>{risk.action}</small>
              </div>
            ))}
          </article>
          <article>
            <div className="panel-heading">
              <span>Resume decisionnel</span>
              <strong>Lecture non specialiste</strong>
            </div>
            {(metadata.storytelling || []).map((line) => <p key={line}>{line}</p>)}
            <button type="button" onClick={handleExport}>Exporter detail gain</button>
          </article>
        </section>
      </aside>
    </div>
  );
}

function isHumanValidated(row) {
  const status = String(row?.validation_achat || row?.validation_status || "").toUpperCase();
  return status.includes("VALID") || status.includes("VALIDÉ") || status.includes("VALIDE");
}

function countHumanValidationState(rows = []) {
  const total = rows.length;
  const validated = rows.filter(isHumanValidated).length;
  return {
    total,
    validated,
    pending: Math.max(total - validated, 0),
    completed: total > 0 && validated >= total,
  };
}

function ProcurementLineArbitrage({ data, currency, storageKey, onSelect, onDecisionCommitted }) {
  const [quickSearch, setQuickSearch] = React.useState("");
  const [selectedRow, setSelectedRow] = React.useState(null);
  const [selectedRows, setSelectedRows] = React.useState([]);
  const [manualOverrides, setManualOverrides] = React.useState({});
  const [bulkNotice, setBulkNotice] = React.useState("");
  const [gridApi, setGridApi] = React.useState(null);
  const rows = data?.table || [];
  const kpis = data?.kpis || {};
  React.useEffect(() => {
    if (!storageKey) return;
    try {
      const stored = window.localStorage.getItem(storageKey);
      setManualOverrides(stored ? JSON.parse(stored) : {});
    } catch {
      setManualOverrides({});
    }
  }, [storageKey]);
  const decisionRows = React.useMemo(
    () => rows.map((row, index) => {
      const key = procurementRowKey(row, index);
      return {
        ...row,
        __sp2i_key: key,
        ...(manualOverrides[key] || {}),
      };
    }),
    [rows, manualOverrides]
  );
  const selectedImpact = React.useMemo(() => selectedRows.reduce((acc, row) => {
    acc.gain += Number(row.gain_net || row.economie || row.economie_nette || 0);
    acc.value += rowValue(row);
    acc.risk = Math.max(acc.risk, Number(row.risque || 0));
    acc.lots.add(row.lot || row.famille || "Lot a qualifier");
    return acc;
  }, { gain: 0, value: 0, risk: 0, lots: new Set() }), [selectedRows]);
  const columns = React.useMemo(() => [
    { field: "designation", headerName: "Désignation travaux", minWidth: 280, pinned: "left", tooltipField: "designation", filter: "agTextColumnFilter" },
    { field: "quantite", headerName: "Quantité DQE", width: 120, type: "numericColumn" },
    { field: "unite", headerName: "Unité", width: 90 },
    { field: "fournisseur_local", headerName: "Fournisseur local", minWidth: 190, filter: "agSetColumnFilter" },
    { field: "pays_local", headerName: "Pays achat local", minWidth: 150, filter: "agSetColumnFilter" },
    { field: "prix_local", headerName: "Prix local", minWidth: 140, valueFormatter: ({ value }) => formatCurrency(value, currency), type: "numericColumn" },
    { field: "fournisseur_chine", headerName: "Fournisseur Chine", minWidth: 210, filter: "agSetColumnFilter" },
    { field: "port_chine", headerName: "Port d'embarquement", minWidth: 160, filter: "agSetColumnFilter" },
    { field: "fob_chine", headerName: "FOB Chine", minWidth: 130, valueFormatter: ({ value }) => formatCurrency(value, currency), type: "numericColumn" },
    { field: "landed_cost_chine", headerName: "Coût rendu chantier", minWidth: 170, valueFormatter: ({ value }) => formatCurrency(value, currency), type: "numericColumn" },
    { field: "gain_net", headerName: "Économie nette", minWidth: 140, valueFormatter: ({ value }) => formatCurrency(value, currency), type: "numericColumn" },
    { field: "roi_import", headerName: "ROI import", minWidth: 120, valueFormatter: ({ value }) => formatPercent(value), type: "numericColumn" },
    { field: "risque", headerName: "Risque achat", minWidth: 120, valueFormatter: ({ value }) => `${Math.round(Number(value || 0))}/100`, type: "numericColumn" },
    { field: "delai", headerName: "Délai estimé", minWidth: 115, valueFormatter: ({ value }) => `${Math.round(Number(value || 0))} j`, type: "numericColumn" },
    {
      field: "decision_ia",
      headerName: "Décision proposée",
      minWidth: 130,
      pinned: "right",
      cellRenderer: ({ value }) => <span className={`decision-badge ${decisionUiClass(value)}`}>{decisionUiLabel(value)}</span>,
      filter: "agSetColumnFilter",
    },
    {
      field: "validation_achat",
      headerName: "Validation humaine",
      minWidth: 145,
      pinned: "right",
      valueGetter: ({ data: row }) => row?.validation_achat || "En attente",
      cellRenderer: ({ value }) => <span className={`validation-badge ${String(value || "").includes("Validé") ? "approved" : String(value || "").includes("Escalade") ? "escalated" : "pending"}`}>{value || "En attente"}</span>,
      filter: "agSetColumnFilter",
    },
    { field: "approval_status", headerName: "Workflow approval", minWidth: 150, valueGetter: ({ data: row }) => row?.approval_status || "Non déclenché", filter: "agSetColumnFilter" },
    { field: "score_confiance_ia", headerName: "Confiance IA", minWidth: 130, valueFormatter: ({ value }) => `${Math.round(Number(value || 0))}/100`, type: "numericColumn" },
    {
      field: "decision_reasons",
      headerName: "Justification IA",
      minWidth: 220,
      valueGetter: ({ data: row }) => (row?.decision_reasons || []).map((reason) => reason.label).join(" | ") || decisionJustification(row),
      tooltipValueGetter: ({ value }) => value,
    },
  ], [currency]);

  const handleSelect = (row) => {
    setSelectedRow(row);
    onSelect?.(row);
  };
  const clearSelection = React.useCallback(() => {
    gridApi?.deselectAll?.();
    setSelectedRows([]);
    setBulkNotice("");
  }, [gridApi]);
  const applyBulkDecision = React.useCallback((decision, label, approvalStatus, justification) => {
    if (!selectedRows.length) return;
    const selectedKeys = new Set(selectedRows.map((row) => row.__sp2i_key));
    setManualOverrides((current) => {
      const next = { ...current };
      const nextRows = decisionRows.map((row) => {
        if (!selectedKeys.has(row.__sp2i_key)) return row;
        const override = {
          decision_ia: decision,
          decision_import: decision,
          validation_achat: label,
          approval_status: approvalStatus,
          justification_humaine: justification,
        };
        next[row.__sp2i_key] = override;
        return { ...row, ...override };
      });
      if (storageKey) {
        window.localStorage.setItem(storageKey, JSON.stringify(next));
      }
      onDecisionCommitted?.({
        decision,
        label,
        selectedCount: selectedRows.length,
        validation: countHumanValidationState(nextRows),
      });
      return next;
    });
    setBulkNotice(`${selectedRows.length} ligne(s) arbitrée(s) : ${label}. Workflow approval déclenché.`);
  }, [decisionRows, onDecisionCommitted, selectedRows, storageKey]);

  return (
    <section className="line-arbitrage-shell">
      <header className="line-arbitrage-header">
        <div>
          <span>Vue strategique par famille</span>
          <strong>Arbitrage fournisseur ligne par ligne</strong>
          <small>{Number(kpis.nb_lignes || decisionRows.length || 0).toLocaleString("fr-FR")} lignes | Gain après coût rendu chantier {formatCurrency(kpis.gain_net_total, currency)} | ROI scénario {formatPercent(kpis.roi_moyen)}</small>
        </div>
        <div className="line-arbitrage-kpis">
          <i>IMPORT {kpis.nb_import || 0}</i>
        <i>HYBRIDE / A ARBITRER {kpis.nb_hybride || 0}</i>
          <i>Risque {Math.round(Number(kpis.risque_moyen || 0))}/100</i>
        </div>
        <input value={quickSearch} onChange={(event) => setQuickSearch(event.target.value)} placeholder="Filtrer par lot, fournisseur, désignation ou port..." />
      </header>

      {selectedRows.length ? (
        <div className="procurement-bulk-toolbar" data-testid="procurement-bulk-toolbar">
          <div>
            <strong>{selectedRows.length} ligne(s) sélectionnée(s)</strong>
            <span>{formatCurrency(selectedImpact.gain, currency)} d'économie potentielle | {selectedImpact.lots.size} lot(s) | risque max {Math.round(selectedImpact.risk)}/100</span>
          </div>
          <button type="button" onClick={() => applyBulkDecision("IMPORT", "Validé achat - Import fournisseur", "Approval procurement déclenché", "Validation humaine : importer les lignes sélectionnées pour sécuriser le gain CAPEX.")}>Valider import</button>
          <button type="button" onClick={() => applyBulkDecision("LOCAL", "Validé achat - Garder local", "Approval procurement déclenché", "Validation humaine : conserver les lignes sélectionnées en achat local pour protéger le planning chantier.")}>Garder local</button>
          <button type="button" onClick={() => applyBulkDecision("HYBRIDE", "Validé achat - Mode hybride", "Approval procurement déclenché", "Validation humaine : basculer les lignes sélectionnées en stratégie hybride local/import.")}>Passer en hybride</button>
          <button type="button" className="danger" onClick={() => applyBulkDecision("ESCALATED", "Escalade direction requise", "Validation direction requise", "Escalade humaine : arbitrage direction requis avant engagement fournisseur.")}>Escalader direction</button>
          <button type="button" className="ghost" onClick={clearSelection}>Annuler sélection</button>
        </div>
      ) : null}
      {bulkNotice ? <div className="procurement-bulk-notice">{bulkNotice}</div> : null}

      <SmartDataGrid
        rows={decisionRows}
        columns={columns}
        height={430}
        quickFilterText={quickSearch}
        onRowSelected={handleSelect}
        getRowClass={({ data: row }) => (selectedRow?.id_ligne && row?.id_ligne === selectedRow.id_ligne ? "sp2i-row-selected" : "")}
        rowClassRules={{
          "sp2i-row-import": ({ data: row }) => row?.decision_ia === "IMPORT",
          "sp2i-row-risk": ({ data: row }) => Number(row?.risque || 0) >= 70,
        }}
        gridOptions={{
          onGridReady: (event) => setGridApi(event.api),
          getRowId: ({ data }) => data.__sp2i_key,
          rowSelection: {
            mode: "multiRow",
            checkboxes: true,
            headerCheckbox: true,
            enableClickSelection: false,
          },
          selectionColumnDef: {
            pinned: "left",
            width: 56,
          },
          onSelectionChanged: (event) => {
            setSelectedRows(event.api.getSelectedRows());
          },
        }}
      />

      <aside className="line-arbitrage-detail">
        {selectedRow ? (
          <>
            <div>
              <span>Detail ligne</span>
              <strong>{selectedRow.designation}</strong>
            </div>
            <div className="supplier-comparison-grid">
              <article>
                <span>LOCAL</span>
                <strong>{selectedRow.fournisseur_local}</strong>
                <p>{selectedRow.pays_local} | {selectedRow.delai_local} j | Qualite {selectedRow.qualite_locale}/100</p>
                <b>{formatCurrency(selectedRow.prix_local, currency)}</b>
              </article>
              <article>
                <span>CHINE</span>
                <strong>{selectedRow.fournisseur_chine}</strong>
                <p>Port {selectedRow.port_chine} | MOQ {selectedRow.moq_chine} | {selectedRow.certifications_chine}</p>
                <b>{formatCurrency(selectedRow.landed_cost_chine, currency)}</b>
              </article>
            </div>
            <p>{selectedRow.storytelling}</p>
            <div className="decision-reason-list">
              <span className="warning">Validation achat : {selectedRow.validation_achat || "En attente"}</span>
              <span className="neutral">Justification : {decisionJustification(selectedRow)}</span>
              {(selectedRow.decision_reasons || []).map((reason) => (
                <span className={reason.type} key={reason.label}>{reason.type === "positive" ? "OK" : reason.type === "warning" ? "!" : "-"} {reason.label}</span>
              ))}
            </div>
            <dl>
              <div><dt>Maritime</dt><dd>{formatCurrency(selectedRow.landed_cost_detail?.maritime, currency)}</dd></div>
              <div><dt>Douane</dt><dd>{formatCurrency(selectedRow.landed_cost_detail?.douane, currency)}</dd></div>
              <div><dt>Assurance</dt><dd>{formatCurrency(selectedRow.landed_cost_detail?.assurance, currency)}</dd></div>
              <div><dt>Logistique locale</dt><dd>{formatCurrency(selectedRow.landed_cost_detail?.logistique_locale, currency)}</dd></div>
              <div><dt>Marge securite</dt><dd>{formatCurrency(selectedRow.landed_cost_detail?.marge_securite, currency)}</dd></div>
            </dl>
          </>
        ) : (
          <p>Selectionner une ligne pour ouvrir le detail fournisseur local vs Chine, le landed cost, la timeline et la recommandation IA.</p>
        )}
      </aside>
    </section>
  );
}

function DecisionAssistantSummary({ workflow, kpis, rows, procurementValidation, currency, onExport, exporting }) {
  const total = Number(procurementValidation.decisions_count ?? rows.length ?? 0);
  const validated = Number(procurementValidation.validated_decisions_count || 0);
  const pending = Number(procurementValidation.pending_decisions_count ?? procurementValidation.to_arbitrate_count ?? Math.max(total - validated, 0));
  const blocked = Number(procurementValidation.blocked_decisions_count || 0);
  const gain = Number(kpis.economie_nette || kpis.gain_net_total || 0);
  const risk = Math.round(Number(kpis.risque_moyen || 0));
  const importCount = rows.filter((row) => normalizeDecision(row.decision_import) === "IMPORT").length;
  const localCount = rows.filter((row) => normalizeDecision(row.decision_import) === "LOCAL").length;
  const hybridCount = rows.filter((row) => ["HYBRIDE", "MIXTE"].includes(normalizeDecision(row.decision_import))).length;
  const nextAction = workflow?.procurement?.status === "REVIEW_REQUIRED"
    ? "Valider les décisions import critiques"
    : pending
      ? "Sélectionner les lignes à arbitrer"
      : "Exporter le dossier achat";

  return (
    <section className="procurement-decision-assistant">
      <div className="decision-focus-main">
        <p className="eyebrow">Assistant de décision achat</p>
        <h1>Que faut-il décider maintenant ?</h1>
        <p>{nextAction}. SP2I affiche uniquement les impacts nécessaires pour valider, conserver en local ou escalader.</p>
        <div className="decision-focus-actions">
          <button type="button" onClick={onExport} disabled={exporting}>
            {exporting ? "Génération..." : "Exporter le dossier direction"}
          </button>
          <span>{pending.toLocaleString("fr-FR")} décision(s) en attente</span>
        </div>
      </div>
      <div className="decision-focus-metrics" data-testid="procurement-decision-summary">
        <article className={pending ? "warning" : "ready"}>
          <span>À décider</span>
          <strong>{pending.toLocaleString("fr-FR")}</strong>
          <small>{validated.toLocaleString("fr-FR")} validée(s)</small>
        </article>
        <article>
          <span>Gain sécurisable</span>
          <strong>{formatCurrency(gain, currency)}</strong>
          <small>après coût rendu chantier</small>
        </article>
        <article className={risk >= 70 || blocked ? "danger" : "neutral"}>
          <span>Risque max</span>
          <strong>{blocked ? `${blocked} blocage(s)` : `${risk}/100`}</strong>
          <small>à surveiller avant commande</small>
        </article>
        <article>
          <span>Orientation</span>
          <strong>{importCount} import · {localCount} local</strong>
          <small>{hybridCount} hybride / à arbitrer</small>
        </article>
      </div>
    </section>
  );
}

function DecisionGuide({ rows, kpis, lotRows, currency, onLotClick }) {
  const riskyRows = rows.filter((row) => Number(row.risque || 0) >= 70).length;
  const importRows = rows.filter((row) => normalizeDecision(row.decision_import) === "IMPORT").length;
  const gain = Number(kpis.economie_nette || kpis.gain_net_total || 0);
  const topLots = lotRows.slice(0, 3);

  return (
    <section className="procurement-decision-guide">
      <article>
        <span>Décision proposée</span>
        <strong>{gain > 0 ? "Valider l'import sur les lignes à ROI positif" : "Revoir les lignes avant engagement"}</strong>
        <p>{importRows} ligne(s) orientée(s) import. Sélectionnez les lignes dans la table, puis appliquez une décision humaine en lot.</p>
      </article>
      <article className={riskyRows ? "warning" : ""}>
        <span>Point d'attention</span>
        <strong>{riskyRows ? `${riskyRows} ligne(s) à risque élevé` : "Aucun blocage critique détecté"}</strong>
        <p>Escaladez uniquement les lignes avec risque douane, ETA ou fournisseur non confirmé.</p>
      </article>
      <article>
        <span>Priorités</span>
        <div className="decision-priority-list">
          {topLots.map((lot) => (
            <button type="button" key={lot.lot} onClick={() => onLotClick(lot.lot)}>
              {lot.lot} · {formatCurrency(lot.gain, currency)}
            </button>
          ))}
          {!topLots.length ? <small>Synchronisez le DQE pour calculer les priorités achat.</small> : null}
        </div>
      </article>
    </section>
  );
}

function FamilyStrategicCockpit({ data, currency, onOpenGain, onExport }) {
  const kpis = data?.kpis || {};
  const charts = data?.charts || {};
  const metadata = data?.metadata || {};
  const comparison = charts.comparison || {};
  const activeTitle = displayScope(metadata.family_scope || "Famille selectionnee");

  if (!data?.table?.length) {
    return null;
  }

  return (
    <section className="family-cockpit-page">
      <header className="family-cockpit-hero">
        <div>
          <span>Cockpit strategique famille</span>
          <h2>Cockpit strategique - {activeTitle}</h2>
          <p>{metadata.storytelling?.[0]}</p>
        </div>
        <div className="family-cockpit-actions">
          <button type="button" onClick={onOpenGain}>Detail du gain</button>
          <button type="button" onClick={onExport}>Générer le dossier procurement direction {activeTitle}</button>
        </div>
      </header>

      <div className="family-kpi-grid">
        <span><b>{formatCurrency(kpis.capex_local, currency)}</b> CAPEX local</span>
        <span><b>{formatCurrency(kpis.capex_chine_rendu_chantier, currency)}</b> Chine rendu chantier</span>
        <span><b>{formatCurrency(kpis.gain_net_total, currency)}</b> Gain apres cout rendu chantier</span>
        <span title="ROI import = economie nette / CAPEX local"><b>{formatPercent(kpis.roi_moyen)}</b> ROI scenario</span>
        <span><b>{kpis.nb_lignes || 0}</b> Lignes</span>
        <span><b>{kpis.nb_fournisseurs || 0}</b> Fournisseurs</span>
        <span><b>{Math.round(Number(comparison.china?.lead_time || 0))} j</b> Delai moyen Chine</span>
        <span><b>{Math.round(Number(kpis.risque_moyen || 0))}/100</b> Risque moyen</span>
        <span><b>{formatCurrency(kpis.cout_logistique, currency)}</b> Cout logistique</span>
        <span><b>{formatCurrency(kpis.cout_douane, currency)}</b> Cout douane</span>
        <span><b>{kpis.containers || 0}</b> Containers estimes a confirmer</span>
        <span><b>{formatPercent(kpis.part_capex_projet)}</b> Part projet</span>
      </div>

      <section className="family-story-card">
        <div>
          <span>Resume IA decisionnel</span>
          {(metadata.storytelling || []).map((line) => <p key={line}>{line}</p>)}
          <p>Decision validee : en attente de validation achat humaine.</p>
        </div>
        <div className="hybrid-strategy-card">
          <span>Mode hybride</span>
          <strong>Importer le standard, garder le critique en local</strong>
          <p>IMPORT : lignes a ROI positif et faible risque. LOCAL : composants critiques delai/SAV. HYBRIDE : lots techniques avec volume importable mais dependance chantier.</p>
        </div>
      </section>

      <section className="family-comparison-grid">
        <article>
          <span>LOCAL</span>
          <strong>{formatCurrency(comparison.local?.cost, currency)}</strong>
          <p>Delai {comparison.local?.lead_time || 0} j | Qualite {comparison.local?.quality || 0}/100 | Risque {comparison.local?.risk || 0}/100</p>
          <small>{comparison.local?.availability}</small>
        </article>
        <article>
          <span>CHINE</span>
          <strong>{formatCurrency(comparison.china?.cost, currency)}</strong>
          <p>Delai {comparison.china?.lead_time || 0} j | Qualite {comparison.china?.quality || 0}/100 | Risque {comparison.china?.risk || 0}/100</p>
          <small>{comparison.china?.availability}</small>
        </article>
        <article className="wide">
          <span>Waterfall gain famille</span>
          <BIChart option={buildDecisionWaterfallOption(charts.waterfall || [], currency)} height={260} chartKey={`family-waterfall-${activeTitle}-${currency}`} />
        </article>
      </section>

      <section className="family-logistics-grid">
        <article>
          <span>Timeline import</span>
          {(charts.timeline || []).map((step) => (
            <div key={step.step}>
              <b>{step.step}</b>
              <small>{step.days} j | Risque {step.risk}</small>
            </div>
          ))}
        </article>
        <article>
          <span>Logistique a consolider</span>
          <strong>Containers estimes : a confirmer</strong>
          <p>{charts.containers?.cbm || 0} CBM estimes. {charts.containers?.mutualisation || "Consolidation par lot et fournisseur requise."}</p>
          <b>{formatCurrency(charts.containers?.logistics_cost, currency)} de cout logistique</b>
        </article>
      </section>
    </section>
  );
}

function ActiveProcurementAnalysis({ analysis, activeChips, drilldownTarget, onReset, onClose, onTab }) {
  const path = drilldownTarget?.path?.length
    ? drilldownTarget.path
    : ["Budget", analysis.importRate > 0.2 ? "Import" : "Local", analysis.activeLabel].filter(Boolean);

  return (
    <section className="active-analysis-bar">
      <div className="analysis-breadcrumb">
        <span>Analyse active</span>
        <strong>{path.join(" -> ")}</strong>
      </div>
      <div className="analysis-chip-row">
        {activeChips.map((chip) => <i key={`${chip.key}-${chip.value}`}>{chip.label}: {chip.value}</i>)}
        {!activeChips.length ? <i>Vue globale</i> : null}
      </div>
      <div className="analysis-actions">
        <button type="button" onClick={onReset}>Retour vue globale</button>
        <button type="button" onClick={onClose}>Fermer drill-down</button>
      </div>
      <div className="analysis-kpi-strip">
        <span><b>{formatMoney(analysis.capexLocal)}</b> CAPEX lot</span>
        <span><b>{formatMoney(analysis.gain)}</b> Gain net securisable</span>
        <span title="ROI import = economie nette / CAPEX local"><b>{formatPercent(analysis.roi)}</b> ROI scenario</span>
        <span><b>{analysis.delay} j</b> Delai</span>
        <span><b>{analysis.risk}</b> Risque</span>
        <span><b>{analysis.containers}</b> estimation logistique a confirmer</span>
      </div>
      <div className="analysis-story">
        <p>
          {analysis.activeLabel || "Le perimetre selectionne"} represente {formatPercent(analysis.share)} du budget.
          Le potentiel import est {analysis.importRate > 0.5 ? "eleve" : "selectif"} avec un gain estime a {formatMoney(analysis.gain)}.
          Fournisseur/famille prioritaire : {analysis.mainSupplier}. Impact chantier : {analysis.dependency}.
        </p>
        <div>
          <button type="button" onClick={() => onTab("import")}>Importer ce lot</button>
          <button type="button" onClick={() => onTab("import")}>Conserver local</button>
          <button type="button" onClick={() => onTab("suppliers")}>Voir fournisseurs</button>
          <button type="button" onClick={() => onTab("containers")}>Voir logistique</button>
          <button type="button" onClick={() => onTab("strategy")}>Mode hybride</button>
        </div>
      </div>
    </section>
  );
}

export default function ProcurementPage() {
  const [tab, setTab] = React.useState(new URLSearchParams(window.location.search).get("tab") || "import");
  const [analysisPanelClosed, setAnalysisPanelClosed] = React.useState(false);
  const [gainDrawerOpen, setGainDrawerOpen] = React.useState(false);
  const [exportNotice, setExportNotice] = React.useState("");
  const [exportingWorkbook, setExportingWorkbook] = React.useState(false);
  const { activeChips, clearDrilldown, drilldownTarget, filters, applyFilter, applyFilters, applyDrilldown, reset } = useCrossFiltering();
  const analytics = useAnalyticsEngine("procurement");
  const { state, setState } = useAppStore();
  const { workflow } = useWorkflow(state.activeProjectDetails?.id || state.activeProject, state.activeProjectDetails);
  const setupDone = workflow.steps.find((step) => step.id === "configuration")?.state === "done";
  const scenarioReady = workflow.scenario?.is_ready || workflow.steps.find((step) => step.id === "scenarios")?.state === "done";
  const procurementStatus = workflow.procurement?.status || workflow.steps.find((step) => step.id === "procurement")?.status;
  const procurementValidation = workflow.procurement || {};

  React.useEffect(() => {
    setTab(new URLSearchParams(window.location.search).get("tab") || "import");
  }, [window.location.search]);

  React.useEffect(() => {
    if (drilldownTarget?.openedAt) setAnalysisPanelClosed(false);
  }, [drilldownTarget?.openedAt]);

  const procurementData = analytics.procurement.data;
  const gainAnalysisData = analytics.gainAnalysis.data;
  const supplierIntelligence = analytics.suppliers.data;
  const procurementLines = analytics.procurementLines.data;
  const scenarioData = analytics.procurementScenarios.data;
  const currencyData = analytics.currency.data;
  const importRiskData = analytics.importRisks.data;
  const dashboardData = analytics.dashboard.data;
  const riskRows = analytics.risk.data?.charts?.risk_matrix || [];
  const sankeyRows = procurementData?.charts?.sankey || dashboardData?.charts?.sankey || [];
  const rows = React.useMemo(() => getRows(procurementData, dashboardData), [procurementData, dashboardData]);
  const kpis = procurementData?.kpis || dashboardData?.kpis || {};
  const supplierRows = React.useMemo(() => supplierIntelligence?.table?.length ? supplierIntelligence.table : buildSupplierRows(rows), [rows, supplierIntelligence]);
  const lotRows = React.useMemo(() => buildLotRows(rows), [rows]);
  const containerRows = React.useMemo(() => buildContainerRows(rows), [rows]);
  const costRows = React.useMemo(() => landedCostRows(kpis), [kpis]);
  const insights = React.useMemo(() => buildInsights(kpis, lotRows, supplierRows), [kpis, lotRows, supplierRows]);
  const importRate = Number(kpis.taux_importable || 0);
  const activeCurrency = filters.devise || gainAnalysisData?.metadata?.currency || "FCFA";
  const roiImport = Number(kpis.roi_import || 0);
  const gainSecurisable = Number(gainAnalysisData?.kpis?.gain_net || kpis.economie_nette || 0);
  const localLines = rows.filter((row) => normalizeDecision(row.decision_import) === "LOCAL").length;
  const importLines = rows.filter((row) => normalizeDecision(row.decision_import) === "IMPORT").length;
  const hybridLines = rows.filter((row) => ["HYBRIDE", "MIXTE"].includes(normalizeDecision(row.decision_import))).length;
  const currentSimulation = state.lastSimulationProject === (state.activeProject || PROJECT_CONTEXT.code) ? state.lastSimulation : null;
  const sourceContext = React.useMemo(
    () => getProcurementSourceContext(state.activeProject || PROJECT_CONTEXT.code, state.activeScenario, currentSimulation),
    [state.activeProject, state.activeScenario, currentSimulation]
  );
  const activeScopeLabel = displayScope(filters.lot || filters.famille || filters.importLocal || "Projet complet");
  const totalCost = costRows.reduce((sum, row) => sum + row.value, 0);
  const activeAnalysis = React.useMemo(
    () => buildActiveAnalysis(rows, filters, drilldownTarget, kpis),
    [rows, filters, drilldownTarget, kpis]
  );
  const hasActiveAnalysis = !analysisPanelClosed && Boolean(activeChips.length || drilldownTarget);
  const resetAnalysis = () => {
    setAnalysisPanelClosed(false);
    reset();
  };
  const closeAnalysis = () => {
    setAnalysisPanelClosed(true);
    clearDrilldown();
  };

  const handleProcurementExport = async () => {
    setExportingWorkbook(true);
    if (!sourceContext.hasActiveDqe || !currentSimulation) {
      setExportNotice("Dossier exportable en version provisoire. Certaines references necessitent encore validation DQE ou scenario.");
    } else {
      setExportNotice("Dossier achat exporte avec source DQE, scenario actif, hypotheses et validations en attente.");
    }
    try {
      await exportProcurementWorkbook(state.activeProject, state.activeProjectDetails?.name || sourceContext.scenarioLabel);
    } catch (error) {
      try {
        const blob = await exportAnalyticsProcurementFile(filters);
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "SP2I_dossier_achat_chine.xlsx";
        link.click();
        URL.revokeObjectURL(url);
        setExportNotice("Export backend indisponible. Dossier achat analytique exporte en fallback.");
      } catch {
        setExportNotice(error?.message || "Export indisponible pour le moment.");
      }
    } finally {
      setExportingWorkbook(false);
    }
  };

  const handleDecisionCommitted = React.useCallback(({ validation, selectedCount, decision, label }) => {
    const total = Number(validation?.total ?? rows.length ?? 0);
    const validated = Number(validation?.validated ?? 0);
    const pending = Math.max(total - validated, 0);
    const completed = total > 0 && pending === 0;
    const patch = {
      procurement_decisions_count: total,
      procurement_validated_decisions_count: validated,
      procurement_pending_decisions_count: pending,
      procurement_to_arbitrate_count: pending,
      procurement_review_required_count: pending,
      procurement_ready: completed,
      procurement_review_required: !completed,
      procurement_status: completed ? "READY" : "REVIEW_REQUIRED",
      workflow_status: completed ? "PROCUREMENT_READY" : "PROCUREMENT_REVIEW_REQUIRED",
      procurement_export_available: completed,
      procurement_orders_count: 0,
    };

    setState((current) => {
      const activeProjectDetails = current.activeProjectDetails
        ? { ...current.activeProjectDetails, ...patch }
        : current.activeProjectDetails;
      const activeProjectId = String(current.activeProjectDetails?.id || "");
      const activeWorkspaceKey = String(current.activeProject || "");

      try {
        const stored = window.localStorage.getItem("sp2i:projects");
        const projects = stored ? JSON.parse(stored) : [];
        if (Array.isArray(projects)) {
          saveLocalProjects(projects.map((project) => {
            const sameProject =
              String(project.id || "") === activeProjectId ||
              String(project.workspace_key || project.id || "") === activeWorkspaceKey;
            return sameProject ? { ...project, ...patch } : project;
          }));
        }

        const eventsKey = `sp2i:workflowEvents:${activeWorkspaceKey || activeProjectId || "default"}`;
        const existingEvents = JSON.parse(window.localStorage.getItem(eventsKey) || "[]");
        const eventBase = {
          at: new Date().toISOString(),
          source: "procurement_page",
          selected_count: selectedCount,
          decision,
          label,
          validated_decisions_count: validated,
          decisions_count: total,
        };
        const events = [
          { type: "PROCUREMENT_LINE_VALIDATED", ...eventBase },
          ...(completed ? [{ type: "PROCUREMENT_ARBITRAGE_COMPLETED", ...eventBase }] : []),
          ...(Array.isArray(existingEvents) ? existingEvents : []),
        ];
        window.localStorage.setItem(eventsKey, JSON.stringify(events.slice(0, 50)));
      } catch {
        // Local persistence is best-effort; React state remains authoritative for the current session.
      }

      return { ...current, activeProjectDetails };
    });
  }, [rows.length, setState]);

  const handleLotClick = (lot) => {
    applyFilters({ lot });
    applyDrilldown({ lot }, { source: "procurement", title: `Analyse achat - ${lot}`, metric: "Arbitrage local/import" });
  };

  return (
    <main className="cockpit-page cockpit-page-fit procurement-center procurement-decision-page">
      {analytics.error ? <div className="app-error">Approvisionnement indisponible : {analytics.error.message}</div> : null}
      {exportNotice ? <div className="app-warning">{exportNotice}</div> : null}

      {!setupDone ? (
        <WorkflowGuardEmptyState
          title="Configuration projet requise"
          message="Ce projet doit etre configure avant de poursuivre le workflow CAPEX."
          actionLabel="Configurer le projet"
          actionRoute="/app/projects"
          severity="blocking"
          currentStep={workflow.label}
          requiredStep="Configuration projet"
          testId="procurement-empty-state"
        />
      ) : null}

      <DecisionAssistantSummary
        workflow={workflow}
        kpis={kpis}
        rows={rows}
        procurementValidation={procurementValidation}
        currency={activeCurrency}
        onExport={handleProcurementExport}
        exporting={exportingWorkbook}
      />

      <section className="procurement-decision-context">
        <div>
          <span>Source</span>
          <strong>{sourceContext.dqeLabel}</strong>
          <small>{sourceContext.hasActiveDqe ? `${sourceContext.dqeStatus} - ${sourceContext.lines ?? "-"} lignes exploitables` : "DQE a valider"}</small>
        </div>
        <div>
          <span>Scenario</span>
          <strong>{sourceContext.scenarioLabel}</strong>
          <small>{sourceContext.scenarioStatus} - {activeScopeLabel}</small>
        </div>
        <label>
          Devise
          <select value={activeCurrency} onChange={(event) => applyFilter("devise", event.target.value)}>
            {(currencyData?.charts?.currencies || [
              { code: "FCFA", label: "Franc CFA" },
              { code: "USD", label: "Dollar americain" },
              { code: "EUR", label: "Euro" },
            ]).map((currency) => (
              <option key={currency.code} value={currency.code}>{currency.code} - {currency.label}</option>
            ))}
          </select>
        </label>
      </section>

      <SmartWorkflowActions
        workflow={workflow}
        module="procurement"
        simulation={currentSimulation}
        procurement={{
          ...procurementValidation,
          decisions_count: procurementValidation.decisions_count || rows.length,
          review_required_count: procurementValidation.review_required_count || procurementValidation.to_arbitrate_count,
        }}
        kpis={{ ...kpis, gainSecurisable, nb_lignes: rows.length }}
        onNavigate={(route) => {
          window.history.pushState({}, "", route);
          window.dispatchEvent(new PopStateEvent("popstate"));
        }}
      />

      {setupDone && !scenarioReady ? (
        <WorkflowGuardEmptyState
          title="Aucun scenario actif"
          message="Aucun scenario actif. Lancez une simulation avant de preparer l'approvisionnement."
          actionLabel="Simuler la strategie CAPEX"
          actionRoute="/app/simulation"
          currentStep={workflow.steps.find((step) => step.id === "scenarios")?.status}
          requiredStep="Scenario CAPEX"
          testId="procurement-empty-state"
        />
      ) : null}
      {setupDone && scenarioReady && procurementStatus === "REQUIRED" ? (
        <div className="app-warning">Le scenario est disponible. Preparez les arbitrages achat pour generer les decisions import/local.</div>
      ) : null}
      {setupDone && scenarioReady && procurementStatus === "REVIEW_REQUIRED" ? (
        <div className="app-warning">Arbitrages achat generes. Validation humaine requise avant preparation chantier.</div>
      ) : null}
      {setupDone && scenarioReady && ["READY", "EXPORTABLE"].includes(procurementStatus) ? (
        <div className="app-success">Approvisionnement pret pour preparation chantier. Le dossier achat peut etre exploite.</div>
      ) : null}

      <DecisionGuide rows={rows} kpis={kpis} lotRows={lotRows} currency={activeCurrency} onLotClick={handleLotClick} />

      <section className="procurement-scope-note compact" data-testid="procurement-validation-summary">
        <span>Decisions : {Number(procurementValidation.decisions_count || rows.length || 0).toLocaleString("fr-FR")}</span>
        <span>Validees : {Number(procurementValidation.validated_decisions_count || 0).toLocaleString("fr-FR")}</span>
        <span>En attente : {Number(procurementValidation.pending_decisions_count || 0).toLocaleString("fr-FR")}</span>
        <span>A arbitrer : {Number(procurementValidation.to_arbitrate_count || 0).toLocaleString("fr-FR")}</span>
        <span>Bloquees : {Number(procurementValidation.blocked_decisions_count || 0).toLocaleString("fr-FR")}</span>
      </section>

      {hasActiveAnalysis ? (
        <ActiveProcurementAnalysis
          analysis={activeAnalysis}
          activeChips={activeChips}
          drilldownTarget={drilldownTarget}
          onReset={resetAnalysis}
          onClose={closeAnalysis}
          onTab={setTab}
        />
      ) : null}

      {gainDrawerOpen ? <GainDetailDrawer analysis={gainAnalysisData} filters={filters} currency={activeCurrency} onClose={() => setGainDrawerOpen(false)} /> : null}

      <section className="procurement-decision-workbench">
        <AnalyticsCard title="Arbitrage fournisseur par ligne" eyebrow="Decision humaine">
          <ProcurementLineArbitrage
            data={procurementLines}
            currency={activeCurrency}
            storageKey={`sp2i:procurementManualArbitrage:${state.activeProject || PROJECT_CONTEXT.code}:${workflow.scenario?.scenario_id || state.activeScenario || "default"}`}
            onDecisionCommitted={handleDecisionCommitted}
            onSelect={(row) => {
              applyFilters({ famille: row.famille, lot: row.lot });
              applyDrilldown({ famille: row.famille, lot: row.lot }, {
                source: "procurement-lines",
                title: `${row.decision_ia} - ${row.designation}`,
                metric: formatCurrency(row.gain_net, activeCurrency),
              });
            }}
          />
        </AnalyticsCard>
      </section>

      <details className="procurement-evidence-panel">
        <summary>Voir les preuves avancees</summary>
        <div className="tab-row compact">
          <button className={tab === "import" ? "active" : ""} onClick={() => setTab("import")} type="button">Repartition</button>
          <button className={tab === "costs" || tab === "cashflow" ? "active" : ""} onClick={() => setTab("costs")} type="button">Cout rendu</button>
          <button className={tab === "suppliers" ? "active" : ""} onClick={() => setTab("suppliers")} type="button">Fournisseurs</button>
          <button className={tab === "containers" ? "active" : ""} onClick={() => setTab("containers")} type="button">Logistique</button>
          <button className={tab === "risks" ? "active" : ""} onClick={() => setTab("risks")} type="button">Risques</button>
          <button className={tab === "strategy" || tab === "moq" ? "active" : ""} onClick={() => setTab("strategy")} type="button">Strategie</button>
        </div>
        {tab === "import" ? (
          <AnalyticsCard title="Repartition des achats" eyebrow="Preuve">
            <ImportDecisionSankey rows={rows} sankeyRows={sankeyRows} />
          </AnalyticsCard>
        ) : null}
        {tab === "suppliers" ? (
          <AnalyticsCard title="Portefeuille fournisseurs" eyebrow="Preuve">
            <div className="data-table-wrap panel-scroll">
              <table className="data-table">
                <thead><tr><th>Fournisseur / famille</th><th>Pays / port</th><th>Score</th><th>Confiance</th><th>Delai</th><th>FOB / ROI</th><th>Budget</th></tr></thead>
                <tbody>
                  {supplierRows.map((supplier) => (
                    <tr key={supplier.supplier} onClick={() => applyFilters({ famille: supplier.supplier })}>
                      <td>{supplier.supplier}</td>
                      <td>{supplier.country || "CN"} | {supplier.port || "Shanghai"}</td>
                      <td><span className="procurement-badge">{supplier.score}/100</span></td>
                      <td>{supplier.supplier_confidence_score || supplier.quality}/100</td>
                      <td>{supplier.lead_time_days || supplier.lead} j</td>
                      <td>{supplier.fob_usd ? `${supplier.fob_usd} USD FOB` : formatPercent(supplier.roi)}</td>
                      <td>{formatMoney(supplier.capex_scope || supplier.capex)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </AnalyticsCard>
        ) : null}
        {tab === "containers" ? (
          <AnalyticsCard title="Logistique import a consolider" eyebrow="Preuve">
            <p className="procurement-prudent-note">Estimation provisoire : a consolider par lot, fournisseur et volume CBM avant commande.</p>
            <div className="procurement-card-grid">
              {containerRows.map((container) => (
                <article className="procurement-mini-card" key={container.id}>
                  <span>{container.id}</span>
                  <strong>{container.lot}</strong>
                  <p>Remplissage estime {Math.round(container.fill * 100)}% - ETA {container.eta}</p>
                  <div className="procurement-progress"><i style={{ width: `${Math.round(container.fill * 100)}%` }} /></div>
                  <small>{container.status} - a confirmer logistique</small>
                </article>
              ))}
            </div>
          </AnalyticsCard>
        ) : null}
        {tab === "costs" || tab === "cashflow" ? (
          <AnalyticsCard title="Cout rendu chantier" eyebrow="Preuve">
            <div className="data-table-wrap panel-scroll">
              <table className="data-table">
                <thead><tr><th>Poste logistique</th><th>Taux</th><th>Impact estime</th></tr></thead>
                <tbody>
                  {costRows.map((cost) => (
                    <tr key={cost.label}>
                      <td>{cost.label}</td>
                      <td>{formatPercent(cost.rate)}</td>
                      <td>{formatMoney(cost.value)}</td>
                    </tr>
                  ))}
                  <tr><td><strong>Total couts import</strong></td><td>-</td><td><strong>{formatMoney(totalCost)}</strong></td></tr>
                </tbody>
              </table>
            </div>
          </AnalyticsCard>
        ) : null}
        {tab === "risks" ? (
          <AnalyticsCard title="Risques import" eyebrow="Preuve">
            <div className="procurement-risk-list">
              {(importRiskData?.table || []).map((risk) => (
                <article key={risk.label}>
                  <span>{risk.label}</span>
                  <strong>{formatMoney(risk.impact)}</strong>
                  <small>Probabilite {formatPercent(risk.probability)} - Criticite {risk.criticite}/100</small>
                  <p>{risk.action}</p>
                </article>
              ))}
            </div>
            {importRiskData?.table?.length ? null : <RiskMatrix rows={riskRows} />}
          </AnalyticsCard>
        ) : null}
        {tab === "strategy" || tab === "moq" ? (
          <AnalyticsCard title="Strategies achat" eyebrow="Preuve">
            <div className="procurement-card-grid">
              {(scenarioData?.table?.length ? scenarioData.table : STRATEGIES).map((strategy) => {
                const estimatedGain = strategy.gain_net ?? Number(kpis.economie_nette || 0) * strategy.importShare;
                return (
                  <article className="procurement-mini-card strategy" key={strategy.label || strategy.code}>
                    <span>{strategy.risk} - Qualite {strategy.quality || "-"}</span>
                    <strong>{strategy.label}</strong>
                    <p>{strategy.description || `Scenario achat avec cout rendu chantier ${formatCurrency(strategy.budget, activeCurrency)}.`}</p>
                    <b>{formatCurrency(estimatedGain, activeCurrency)} de gain cible</b>
                    <small>Delai moyen {strategy.lead || strategy.lead_time} j - ROI {formatPercent(strategy.roi || 0)}</small>
                  </article>
                );
              })}
            </div>
          </AnalyticsCard>
        ) : null}
      </details>
    </main>
  );

}
