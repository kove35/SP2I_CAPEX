import React from "react";
import AnalyticsCard from "../../ui/AnalyticsCard";
import KpiCard from "../../ui/KpiCard";
import ImportDecisionSankey from "../../components/charts/ImportDecisionSankey";
import RiskMatrix from "../../components/charts/RiskMatrix";
import { useAnalyticsEngine } from "../../hooks/useAnalyticsEngine";
import { useCrossFiltering } from "../../hooks/useCrossFiltering";
import { formatMoney, formatPercent } from "../../shared/formatters";
import { normalizeDecision, normalizeFamily, toBusinessLabel } from "../../utils/analyticsLabels";

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
  const activeLabel = filters.lot || filters.famille || filters.importLocal || drilldownTarget?.selectedLabel || "";
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
  const mainSupplier = [...familyCount.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] || drilldownTarget?.selectedLabel || "A confirmer";
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
        <span><b>{formatMoney(analysis.gain)}</b> Gain potentiel</span>
        <span><b>{formatPercent(analysis.roi)}</b> ROI</span>
        <span><b>{analysis.delay} j</b> Delai</span>
        <span><b>{analysis.risk}</b> Risque</span>
        <span><b>{analysis.containers}</b> container(s)</span>
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
          <button type="button" onClick={() => onTab("containers")}>Voir containers</button>
          <button type="button" onClick={() => onTab("strategy")}>Mode hybride</button>
        </div>
      </div>
    </section>
  );
}

export default function ProcurementPage() {
  const [tab, setTab] = React.useState(new URLSearchParams(window.location.search).get("tab") || "import");
  const [analysisPanelClosed, setAnalysisPanelClosed] = React.useState(false);
  const { activeChips, clearDrilldown, drilldownTarget, filters, applyFilters, applyDrilldown, reset } = useCrossFiltering();
  const analytics = useAnalyticsEngine("procurement");

  React.useEffect(() => {
    setTab(new URLSearchParams(window.location.search).get("tab") || "import");
  }, [window.location.search]);

  React.useEffect(() => {
    if (drilldownTarget?.openedAt) setAnalysisPanelClosed(false);
  }, [drilldownTarget?.openedAt]);

  const procurementData = analytics.procurement.data;
  const dashboardData = analytics.dashboard.data;
  const riskRows = analytics.risk.data?.charts?.risk_matrix || [];
  const sankeyRows = procurementData?.charts?.sankey || dashboardData?.charts?.sankey || [];
  const rows = React.useMemo(() => getRows(procurementData, dashboardData), [procurementData, dashboardData]);
  const kpis = procurementData?.kpis || dashboardData?.kpis || {};
  const supplierRows = React.useMemo(() => buildSupplierRows(rows), [rows]);
  const lotRows = React.useMemo(() => buildLotRows(rows), [rows]);
  const containerRows = React.useMemo(() => buildContainerRows(rows), [rows]);
  const costRows = React.useMemo(() => landedCostRows(kpis), [kpis]);
  const insights = React.useMemo(() => buildInsights(kpis, lotRows, supplierRows), [kpis, lotRows, supplierRows]);
  const importRate = Number(kpis.taux_importable || 0);
  const roiImport = Number(kpis.roi_import || 0);
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

  const handleLotClick = (lot) => {
    applyFilters({ lot });
    applyDrilldown({ lot }, { source: "procurement", title: `Analyse achat - ${lot}`, metric: "Arbitrage local/import" });
  };

  return (
    <main className="cockpit-page cockpit-page-fit procurement-center">
      <section className="page-hero compact procurement-hero">
        <p className="eyebrow">Approvisionnement strategique</p>
        <h1>Arbitrer local, import, fournisseurs et logistique pour proteger le budget travaux</h1>
        <p>Centre decisionnel achat connecte aux donnees DQE, aux economies CAPEX et au risque chantier.</p>
      </section>

      <div className="tab-row">
        <button className={tab === "import" ? "active" : ""} onClick={() => setTab("import")} type="button">Arbitrage local / import</button>
        <button className={tab === "suppliers" ? "active" : ""} onClick={() => setTab("suppliers")} type="button">Fournisseurs</button>
        <button className={tab === "containers" ? "active" : ""} onClick={() => setTab("containers")} type="button">Containers</button>
        <button className={tab === "costs" || tab === "cashflow" ? "active" : ""} onClick={() => setTab("costs")} type="button">Cout rendu chantier</button>
        <button className={tab === "risks" ? "active" : ""} onClick={() => setTab("risks")} type="button">Risques import</button>
        <button className={tab === "strategy" || tab === "moq" ? "active" : ""} onClick={() => setTab("strategy")} type="button">Strategies achat</button>
      </div>

      {analytics.error ? <div className="app-error">Approvisionnement indisponible : {analytics.error.message}</div> : null}

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

      <section className="metric-grid">
        <KpiCard label="ROI import" value={formatPercent(roiImport)} tone={roiImport > 0.1 ? "success" : "neutral"} />
        <KpiCard label="Gain potentiel" value={formatMoney(kpis.economie_nette)} tone="success" />
        <KpiCard label="Taux importable" value={formatPercent(importRate)} />
        <KpiCard label="Budget optimise" value={formatMoney(kpis.capex_optimise)} />
        <KpiCard label="Lignes achat" value={Number(kpis.nb_lignes || rows.length || 0).toLocaleString("fr-FR")} tone="warning" />
      </section>

      <section className="procurement-insights">
        {insights.map((insight) => <article key={insight}>{insight}</article>)}
      </section>

      <section className="cockpit-split">
        {tab === "import" ? (
          <AnalyticsCard title="Repartition des achats" eyebrow="Lots vers fournisseurs et arbitrage">
            <ImportDecisionSankey rows={rows} sankeyRows={sankeyRows} />
          </AnalyticsCard>
        ) : null}

        {tab === "suppliers" ? (
          <AnalyticsCard title="Portefeuille fournisseurs" eyebrow="Mini ERP sourcing">
            <div className="data-table-wrap panel-scroll">
              <table className="data-table">
                <thead><tr><th>Fournisseur / famille</th><th>Pays</th><th>Score</th><th>Qualite</th><th>Delai</th><th>ROI</th><th>Budget</th></tr></thead>
                <tbody>
                  {supplierRows.map((supplier) => (
                    <tr key={supplier.supplier} onClick={() => applyFilters({ famille: supplier.supplier })}>
                      <td>{supplier.supplier}</td>
                      <td>{supplier.country}</td>
                      <td><span className="procurement-badge">{supplier.score}/100</span></td>
                      <td>{supplier.quality}/100</td>
                      <td>{supplier.lead} j</td>
                      <td>{formatPercent(supplier.roi)}</td>
                      <td>{formatMoney(supplier.capex)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </AnalyticsCard>
        ) : null}

        {tab === "containers" ? (
          <AnalyticsCard title="Cockpit containers" eyebrow="Mutualisation et capacite">
            <div className="procurement-card-grid">
              {containerRows.map((container) => (
                <article className="procurement-mini-card" key={container.id}>
                  <span>{container.id}</span>
                  <strong>{container.lot}</strong>
                  <p>Remplissage {Math.round(container.fill * 100)}% | ETA {container.eta}</p>
                  <div className="procurement-progress"><i style={{ width: `${Math.round(container.fill * 100)}%` }} /></div>
                  <small>{container.status}</small>
                </article>
              ))}
            </div>
          </AnalyticsCard>
        ) : null}

        {tab === "costs" || tab === "cashflow" ? (
          <AnalyticsCard title="Cout rendu chantier" eyebrow="Maritime, douane, port et livraison locale">
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
                  <tr>
                    <td><strong>Total couts import</strong></td>
                    <td>-</td>
                    <td><strong>{formatMoney(totalCost)}</strong></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </AnalyticsCard>
        ) : null}

        {tab === "risks" ? (
          <AnalyticsCard title="Cartographie des risques import" eyebrow="Fournisseur, douane, maritime, qualite">
            <RiskMatrix rows={riskRows} />
          </AnalyticsCard>
        ) : null}

        {tab === "strategy" || tab === "moq" ? (
          <AnalyticsCard title="Simulation strategique achat" eyebrow="Comparer les politiques d'approvisionnement">
            <div className="procurement-card-grid">
              {STRATEGIES.map((strategy) => {
                const estimatedGain = Number(kpis.economie_nette || 0) * strategy.importShare;
                return (
                  <article className="procurement-mini-card strategy" key={strategy.label}>
                    <span>{strategy.risk}</span>
                    <strong>{strategy.label}</strong>
                    <p>{strategy.description}</p>
                    <b>{formatMoney(estimatedGain)} de gain cible</b>
                    <small>Delai moyen {strategy.lead}</small>
                  </article>
                );
              })}
            </div>
          </AnalyticsCard>
        ) : null}

        <aside className="context-panel">
          <AnalyticsCard title="Priorites achat" eyebrow="Decision intelligence">
            <ul className="signal-list">
              {lotRows.slice(0, 5).map((lot) => (
                <li key={lot.lot}>
                  <button className="link-button" type="button" onClick={() => handleLotClick(lot.lot)}>
                    {lot.lot} : {formatMoney(lot.gain)} de gain, {formatPercent(lot.importRate)} import.
                  </button>
                </li>
              ))}
              {!lotRows.length ? <li>Synchroniser le DQE pour alimenter les priorites achat.</li> : null}
            </ul>
          </AnalyticsCard>
          <AnalyticsCard title="Recommandation SP2I" eyebrow="Storytelling IA">
            <ul className="signal-list">
              <li>Importer les lots a ROI positif avec un risque logistique sous controle.</li>
              <li>Conserver en local les familles sensibles au delai chantier.</li>
              <li>Mutualiser les containers sur les lots a forte densite CAPEX.</li>
              <li>Remonter les risques critiques vers le cockpit direction.</li>
            </ul>
          </AnalyticsCard>
        </aside>
      </section>
    </main>
  );
}
