import React from "react";
import { ArrowRight, CheckCircle2, Download, FilterX, RefreshCcw, Sparkles, Trophy } from "lucide-react";
import Skeleton from "../../ui/Skeleton";
import { formatMoney, formatPercent } from "../../shared/formatters";
import { useProcurementCockpit } from "../../hooks/useProcurementCockpit";
import { useProcurementCockpitStore } from "../../stores/procurementCockpitStore";
import ProcurementKpiStrip from "../../components/procurementCockpit/ProcurementKpiStrip";
import ProcurementCockpitGrid from "../../components/procurementCockpit/ProcurementCockpitGrid";
import ProcurementStoryPanel from "../../components/procurementCockpit/ProcurementStoryPanel";
import {
  ChartPanel,
  buildBenchmarkOption,
  buildHeatmapOption,
  buildScenarioOption,
  buildWaterfallOption,
} from "../../components/procurementCockpit/ProcurementCockpitCharts";

const DASHBOARDS = [
  ["direction", "Direction"],
  ["procurement", "Procurement Intelligence"],
  ["financial", "Financial Sanity"],
  ["scenario", "Scenario Intelligence"],
  ["explainability", "Explainability"],
  ["roi", "ROI Intelligence"],
  ["risk", "Risk Intelligence"],
];

function number(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function filterRowsByContext(rows = [], filters = {}, selectedLine = null) {
  const lot = selectedLine?.lot || filters.lot;
  const famille = selectedLine?.famille || filters.famille;
  const supplier = selectedLine?.supplier || filters.fournisseur;
  const decision = filters.importLocal || filters.decisionImport;
  return rows.filter((row) => {
    if (lot && row.lot !== lot) return false;
    if (famille && row.famille !== famille) return false;
    if (supplier && row.supplier !== supplier) return false;
    if (decision && row.decision !== String(decision).toUpperCase()) return false;
    return true;
  });
}

function groupRows(rows = [], key) {
  const map = new Map();
  rows.forEach((row) => {
    const label = row[key] || "Non renseigne";
    const current = map.get(label) || { label, amount: 0, gain: 0, risk: 0, procurement: 0, confidence: 0, anomalies: 0, rows: 0, importRows: 0 };
    current.amount += number(row.amount);
    current.gain += number(row.gain);
    current.risk += number(row.risk_score);
    current.procurement += number(row.procurement_score);
    current.confidence += number(row.financial_confidence_score);
    current.anomalies += number(row.anomaly_score) >= 30 ? 1 : 0;
    current.importRows += row.decision === "IMPORT" ? 1 : 0;
    current.rows += 1;
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

function buildScopedData(data, filters, selectedLine) {
  const lines = filterRowsByContext(data?.lines || [], filters, selectedLine);
  const source = lines.length ? lines : data?.lines || [];
  const capexBrut = source.reduce((sum, row) => sum + number(row.capex_local || row.amount), 0);
  const capexOptimise = source.reduce((sum, row) => sum + number(row.amount), 0);
  const gain = source.reduce((sum, row) => sum + number(row.gain), 0);
  const avg = (key) => source.length ? source.reduce((sum, row) => sum + number(row[key]), 0) / source.length : 0;
  return {
    ...data,
    lines: source,
    lots: groupRows(source, "lot"),
    families: groupRows(source, "famille"),
    suppliers: groupRows(source, "supplier"),
    kpis: {
      ...(data?.kpis || {}),
      capexBrut: capexBrut || data?.kpis?.capexBrut,
      capexOptimise: capexOptimise || data?.kpis?.capexOptimise,
      gain: gain || data?.kpis?.gain,
      roi: capexBrut ? gain / capexBrut : data?.kpis?.roi,
      procurementScore: avg("procurement_score") || data?.kpis?.procurementScore,
      financialConfidence: avg("financial_confidence_score") || data?.kpis?.financialConfidence,
      anomalyScore: avg("anomaly_score") || data?.kpis?.anomalyScore,
      riskScore: avg("risk_score") || data?.kpis?.riskScore,
      anomalyCount: source.filter((row) => number(row.anomaly_score) >= 30).length,
      lineCount: source.length,
      importRate: source.length ? source.filter((row) => row.decision === "IMPORT").length / source.length : data?.kpis?.importRate,
    },
  };
}

function exportPowerBiPayload(data) {
  const payload = {
    generated_at: new Date().toISOString(),
    kpis: data?.kpis || {},
    families: data?.families || [],
    lots: data?.lots || [],
    lines: data?.lines || [],
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "sp2i_procurement_powerbi_payload.json";
  link.click();
  URL.revokeObjectURL(url);
}

function ExecutiveDashboard({ data, onDimensionClick }) {
  const kpis = data?.kpis || {};
  return (
    <section className="procurement-dashboard-grid">
      <ChartPanel title="Waterfall CAPEX" eyebrow="Direction" option={buildWaterfallOption(kpis)} height={300} />
      <ChartPanel
        title="Heatmap anomalies"
        eyebrow="Financial sanity"
        option={buildHeatmapOption(data?.families || [])}
        height={300}
        onEvents={{ click: (params) => onDimensionClick?.("famille", data?.families?.[params?.data?.[1]]?.label) }}
      />
      <ChartPanel
        title="Benchmark famille"
        eyebrow="Procurement scoring"
        option={buildBenchmarkOption(data?.families || [])}
        height={300}
        onEvents={{ click: (params) => onDimensionClick?.("famille", params.name) }}
      />
      <ChartPanel title="Scenario comparison" eyebrow="Decision board" option={buildScenarioOption(data?.scenarios || [], kpis)} height={380} />
    </section>
  );
}

function ScenarioComparisonDeck({ kpis = {}, onScenario }) {
  const scenarios = [
    { code: "CONSERVATEUR", label: "Conservateur", roi: number(kpis.roi) * 0.72, risk: 28, gain: number(kpis.gain) * 0.72, procurement: number(kpis.procurementScore) * 0.96 },
    { code: "EQUILIBRE", label: "Equilibre", roi: number(kpis.roi) * 1.04, risk: 42, gain: number(kpis.gain) * 1.05, procurement: number(kpis.procurementScore) * 1.02 },
    { code: "AGRESSIF", label: "Agressif", roi: number(kpis.roi) * 1.34, risk: 68, gain: number(kpis.gain) * 1.26, procurement: number(kpis.procurementScore) * 0.92 },
  ];
  const best = scenarios.reduce((winner, scenario) => scenario.gain - scenario.risk * 250000 > winner.gain - winner.risk * 250000 ? scenario : winner, scenarios[0]);
  return (
    <section className="scenario-comparison-deck">
      {scenarios.map((scenario) => (
        <button className={`scenario-card ${scenario.code === best.code ? "best" : ""}`} type="button" key={scenario.code} onClick={() => onScenario?.(scenario)}>
          <span>{scenario.code === best.code ? <Trophy size={14} /> : <CheckCircle2 size={14} />} {scenario.label}</span>
          <strong>{formatMoney(scenario.gain)}</strong>
          <small>ROI {formatPercent(scenario.roi)} | Risque {Math.round(scenario.risk)}/100 | Procurement {Math.round(scenario.procurement)}/100</small>
          <em>{scenario.code === best.code ? "Best compromise" : scenario.risk > 60 ? "Optimisation agressive" : "Marge de securite"}</em>
        </button>
      ))}
    </section>
  );
}

function FocusDashboard({ data, activeDashboard, onDimensionClick }) {
  const lots = data?.lots || [];
  const families = data?.families || [];
  const suppliers = data?.suppliers || [];
  const rows = activeDashboard === "procurement" ? suppliers : activeDashboard === "risk" ? lots : families;
  const title = {
    procurement: "Sourcing analytics",
    financial: "Ranges financiers et anomalies",
    scenario: "Comparaison scenarios",
    explainability: "Panneaux explainability",
    roi: "ROI analytics",
    risk: "Matrices de risques",
  }[activeDashboard] || "Pilotage detaille";

  return (
    <section className="procurement-focus-grid">
      <article className="procurement-panel focus-table">
        <header>
          <span>{title}</span>
          <strong>Vue cross-filtered</strong>
        </header>
        <div className="procurement-table-lite">
          <table>
            <thead><tr><th>Dimension</th><th>CAPEX</th><th>Gain</th><th>ROI</th><th>Risque</th><th>Confiance</th></tr></thead>
            <tbody>
              {rows.slice(0, 12).map((row) => (
                <tr key={row.label || row.supplier} onClick={() => onDimensionClick?.(activeDashboard === "procurement" ? "fournisseur" : activeDashboard === "risk" ? "lot" : "famille", row.label || row.supplier)}>
                  <td>{row.label || row.supplier}</td>
                  <td>{formatMoney(row.amount || row.capex || row.capex_scope)}</td>
                  <td>{formatMoney(row.gain)}</td>
                  <td>{formatPercent(row.roi)}</td>
                  <td>{Math.round(row.risk || row.risk_score || 0)}/100</td>
                  <td>{Math.round(row.confidence || row.procurement || row.score || 0)}/100</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
      <ChartPanel title={title} eyebrow={activeDashboard} option={activeDashboard === "scenario" ? buildScenarioOption(data?.scenarios, data?.kpis) : activeDashboard === "risk" || activeDashboard === "financial" ? buildHeatmapOption(rows) : buildBenchmarkOption(rows)} height={activeDashboard === "scenario" ? 420 : 360} />
    </section>
  );
}

export default function ProcurementIntelligenceCockpit() {
  const { data, isLoading, isFetching, error, refetch, crossFiltering, activeChips } = useProcurementCockpit();
  const { activeDashboard, selectedLine, setActiveDashboard, setSelectedLine, resetCockpitSelection } = useProcurementCockpitStore();
  const scopedData = React.useMemo(
    () => buildScopedData(data, crossFiltering.filters, selectedLine),
    [data, crossFiltering.filters, selectedLine]
  );
  const rows = scopedData?.lines || [];
  const executiveNarrative = React.useMemo(() => {
    const kpis = scopedData?.kpis || {};
    const scenario = Number(kpis.riskScore || 0) > 60 ? "CONSERVATEUR" : Number(kpis.roi || 0) > 0.12 ? "AGRESSIF CONTROLE" : "EQUILIBRE";
    const anomalyText = Number(kpis.anomalyCount || 0) > 0 ? `${kpis.anomalyCount} alerte(s) a qualifier` : "aucune alerte critique dominante";
    return `Scenario ${scenario}: ${formatMoney(kpis.gain || 0)} d'economies potentielles, ROI ${formatPercent(kpis.roi || 0)}, ${anomalyText}.`;
  }, [scopedData?.kpis]);
  const breadcrumbs = React.useMemo(
    () => [
      "Cockpit",
      crossFiltering.filters.lot,
      crossFiltering.filters.famille,
      crossFiltering.filters.fournisseur,
      selectedLine?.designation,
    ].filter(Boolean),
    [crossFiltering.filters.famille, crossFiltering.filters.fournisseur, crossFiltering.filters.lot, selectedLine]
  );

  const handleDimensionClick = React.useCallback((key, value) => {
    if (!value) return;
    crossFiltering.applyDrilldown({ [key]: value }, { source: "procurement-cockpit", title: value, metric: key });
  }, [crossFiltering]);

  const handleRowSelect = (row) => {
    setSelectedLine(row);
    crossFiltering.applyDrilldown(
      { lot: row.lot, famille: row.famille, fournisseur: row.supplier },
      { source: "procurement-intelligence", title: row.designation, metric: formatMoney(row.amount) }
    );
  };

  const resetAll = () => {
    resetCockpitSelection();
    crossFiltering.reset();
  };

  const handleKpiClick = (key) => {
    if (key === "anomalyCount") setActiveDashboard("financial");
    if (key === "riskScore") setActiveDashboard("risk");
    if (key === "roi") setActiveDashboard("roi");
    if (key === "procurementScore" || key === "importRate") setActiveDashboard("procurement");
  };

  return (
    <main className="procurement-enterprise-page">
      <section className="procurement-enterprise-hero">
        <div>
          <p className="eyebrow">Procurement Intelligence Cockpit</p>
          <h1>Decision cockpit CAPEX</h1>
          <p>Arbitrage executif achats, ROI, risques et anomalies.</p>
        </div>
        <div className="procurement-hero-actions">
          <button type="button" onClick={() => refetch()}><RefreshCcw size={16} /> Actualiser</button>
          <button type="button" onClick={resetAll}><FilterX size={16} /> Reinitialiser</button>
          <button type="button" onClick={() => exportPowerBiPayload(data)}><Download size={16} /> Export BI</button>
        </div>
      </section>

      {error ? <div className="app-error">Cockpit indisponible : {error.message}</div> : null}
      {isFetching ? <div className="live-refresh">Synchronisation des dashboards procurement...</div> : null}
      {isLoading ? <Skeleton /> : null}

      <nav className="procurement-dashboard-tabs" aria-label="Dashboards procurement">
        {DASHBOARDS.map(([key, label]) => (
          <button key={key} type="button" className={activeDashboard === key ? "active" : ""} onClick={() => setActiveDashboard(key)}>
            {label}
          </button>
        ))}
      </nav>

      {activeChips.length ? (
        <section className="procurement-filter-strip">
          {activeChips.map((chip) => <span key={`${chip.key}-${chip.value}`}>{chip.label}: {chip.value}</span>)}
        </section>
      ) : null}

      <section className="procurement-context-ribbon">
        <div className="procurement-breadcrumbs">
          {breadcrumbs.map((item, index) => (
            <React.Fragment key={`${item}-${index}`}>
              {index ? <ArrowRight size={13} /> : null}
              <span>{item}</span>
            </React.Fragment>
          ))}
        </div>
        <strong>{rows.length.toLocaleString("fr-FR")} ligne(s) dans le contexte actif</strong>
      </section>

      <section className="procurement-executive-ribbon">
        <Sparkles size={16} />
        <strong>{executiveNarrative}</strong>
        <span>Dashboard {activeDashboard} synchronise avec les filtres actifs.</span>
      </section>

      <ProcurementKpiStrip kpis={scopedData?.kpis} loading={isLoading} onKpiClick={handleKpiClick} />

      <ScenarioComparisonDeck kpis={scopedData?.kpis} onScenario={(scenario) => {
        setActiveDashboard("scenario");
        crossFiltering.applyDrilldown({ scenario: scenario.code }, { source: "scenario-comparison", title: scenario.label, metric: formatMoney(scenario.gain) });
      }} />

      {activeDashboard === "direction"
        ? <ExecutiveDashboard data={scopedData} onDimensionClick={handleDimensionClick} />
        : <FocusDashboard data={scopedData} activeDashboard={activeDashboard} onDimensionClick={handleDimensionClick} />}

      <section className="procurement-workbench">
        <ProcurementCockpitGrid rows={rows} onSelect={handleRowSelect} />
        <ProcurementStoryPanel data={scopedData} selectedLine={selectedLine} onExport={() => exportPowerBiPayload(scopedData)} />
      </section>
    </main>
  );
}
