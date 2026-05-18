import React from "react";
import { RefreshCcw } from "lucide-react";
import CapexHeatmap from "../../components/charts/CapexHeatmap";
import CapexTimeline from "../../components/charts/CapexTimeline";
import CapexWaterfall from "../../components/charts/CapexWaterfall";
import ImportDecisionSankey from "../../components/charts/ImportDecisionSankey";
import RiskMatrix from "../../components/charts/RiskMatrix";
import InsightsPanel from "../../components/analytics/InsightsPanel";
import GlobalAnalyticsFilters from "../../components/filters/GlobalAnalyticsFilters";
import FactMetreGrid from "../../components/grids/FactMetreGrid";
import EnterpriseKpiGrid from "../../components/kpi/EnterpriseKpiGrid";
import { useAnalyticsEngine } from "../../hooks/useAnalyticsEngine";
import AnalyticsCard from "../../ui/AnalyticsCard";
import Skeleton from "../../ui/Skeleton";
import AnalyticsHealthPage from "./AnalyticsHealthPage";

const dashboards = [
  ["direction", "Direction"],
  ["capex", "CAPEX"],
  ["procurement", "Procurement"],
  ["logistics", "Logistics"],
  ["risks", "Risks"],
  ["heatmaps", "Heatmaps"],
  ["drilldown", "Drill-down"],
  ["timeline", "Timeline"],
  ["monitoring", "Monitoring"],
];

const dashboardCopy = {
  direction: "Cockpit executif pour piloter CAPEX, economie, risque et arbitrages import/local.",
  capex: "Lecture financiere des investissements immobiliers et des optimisations CAPEX.",
  procurement: "Analyse procurement, importabilite, familles fournisseurs et decisions local/import.",
  logistics: "Vue logistique projet et arbitrages operationnels alimentes par le moteur analytics.",
  risks: "Matrice decisionnelle risque, criticite et potentiel d'economie.",
  heatmaps: "Densite CAPEX par lot et famille pour reperer les zones de concentration.",
  drilldown: "Exploration FACT_METRE avec selection interactive et filtres globaux.",
  timeline: "Evolution des simulations, economies et decisions dans le temps.",
  monitoring: "Sante Analytics Engine, PostgreSQL, cache et coherence QA.",
};

function useDashboardFromUrl() {
  const [dashboard, setDashboard] = React.useState(new URLSearchParams(window.location.search).get("dashboard") || "direction");

  React.useEffect(() => {
    const sync = () => setDashboard(new URLSearchParams(window.location.search).get("dashboard") || "direction");
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);

  const updateDashboard = (value) => {
    setDashboard(value);
    const url = `/app/analytics?dashboard=${value}`;
    window.history.pushState({}, "", url);
    window.dispatchEvent(new PopStateEvent("popstate"));
  };

  return [dashboard, updateDashboard];
}

export default function AnalyticsPage() {
  const [dashboard, setDashboard] = useDashboardFromUrl();
  const engine = useAnalyticsEngine(dashboard);
  const mainPayload = engine.dashboard.data || {};
  const capexPayload = engine.capex.data || {};
  const kpis = { ...(capexPayload.kpis || {}), ...(mainPayload.kpis || {}) };
  const table = mainPayload.table?.length ? mainPayload.table : engine.drilldown.data?.table || [];
  const total = mainPayload.pagination?.total || engine.drilldown.data?.pagination?.total || table.length;
  const barRows = mainPayload.charts?.bar || capexPayload.charts?.bar || [];
  const heatmapRows = engine.heatmap.data?.charts?.heatmap || mainPayload.charts?.heatmap || [];
  const timelineRows = engine.timeline.data?.charts?.timeline || mainPayload.charts?.timeline || [];
  const riskRows = engine.risk.data?.charts?.risk_matrix || heatmapRows || [];

  const refreshAll = () => {
    engine.dashboard.refetch();
    engine.capex.refetch();
    engine.procurement.refetch();
    engine.heatmap.refetch();
    engine.risk.refetch();
    engine.timeline.refetch();
    engine.drilldown.refetch();
    engine.qa.refetch();
  };

  return (
    <main className="cockpit-page analytics-engine-page">
      <section className="page-hero compact analytics-engine-hero">
        <p className="eyebrow">SP2I Analytics Engine</p>
        <h1>Decision intelligence immobiliere pilotee par Analytics Engine V1</h1>
        <p>{dashboardCopy[dashboard] || dashboardCopy.direction}</p>
        <button type="button" className="icon-text-button" onClick={refreshAll}>
          <RefreshCcw size={15} />
          Rafraichir
        </button>
      </section>

      <div className="tab-row">
        {dashboards.map(([key, name]) => (
          <button key={key} className={dashboard === key ? "active" : ""} type="button" onClick={() => setDashboard(key)}>
            {name}
          </button>
        ))}
      </div>

      <GlobalAnalyticsFilters />

      {engine.error ? <div className="analytics-error">{engine.error.message}</div> : null}
      {engine.isFetching ? <div className="live-refresh">Synchronisation Analytics Engine en cours...</div> : null}

      {dashboard === "monitoring" ? (
        <AnalyticsHealthPage qa={engine.qa} />
      ) : (
        <>
          <EnterpriseKpiGrid kpis={kpis} loading={engine.isLoading} />

          {engine.isLoading ? <Skeleton rows={4} /> : null}

          <section className="analytics-command-grid">
            <InsightsPanel kpis={kpis} barRows={barRows} table={table} />
            <AnalyticsCard title="Waterfall CAPEX" eyebrow="CAPEX brut vers CAPEX final">
              <CapexWaterfall summary={kpis} />
            </AnalyticsCard>
          </section>

          <section className="bi-dashboard-grid">
            <AnalyticsCard title="Sankey import/local" eyebrow="Decisions par lots">
              <ImportDecisionSankey rows={table} chartRows={barRows} />
            </AnalyticsCard>
            <AnalyticsCard title="Heatmap CAPEX" eyebrow="Lot x famille">
              <CapexHeatmap data={heatmapRows} />
            </AnalyticsCard>
            <AnalyticsCard title="Risk matrix" eyebrow="Probabilite x criticite">
              <RiskMatrix rows={riskRows} />
            </AnalyticsCard>
            <AnalyticsCard title="Timeline CAPEX" eyebrow="Evolution simulation et economie">
              <CapexTimeline data={timelineRows} />
            </AnalyticsCard>
          </section>

          <AnalyticsCard title="Drill-down FACT_METRE" eyebrow="AG Grid decisionnel">
            <FactMetreGrid rows={table} total={total} />
          </AnalyticsCard>
        </>
      )}
    </main>
  );
}
