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
  ["capex", "Budget travaux"],
  ["procurement", "Achats"],
  ["logistics", "Logistique"],
  ["risks", "Risques"],
  ["heatmaps", "Zones couteuses"],
  ["drilldown", "Analyse detaillee"],
  ["timeline", "Evolution"],
  ["monitoring", "Etat du systeme"],
];

const dashboardCopy = {
  direction: "Cockpit executif pour piloter budget, economies, risques et arbitrages local/import.",
  capex: "Lecture financiere claire des investissements immobiliers et des economies possibles.",
  procurement: "Analyse des achats, de l'importabilite, des fournisseurs et des decisions local/import.",
  logistics: "Vue logistique du projet pour securiser les livraisons, les couts et les delais.",
  risks: "Carte decisionnelle des risques, de la criticite et du potentiel d'economie.",
  heatmaps: "Repere les lots, familles ou zones qui concentrent le plus de budget.",
  drilldown: "Analyse detaillee des lignes budgetaires avec selection interactive et filtres globaux.",
  timeline: "Evolution des scenarios, des economies et des decisions dans le temps.",
  monitoring: "Etat du systeme, qualite des donnees, base projet et coherence des indicateurs.",
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
  const sankeyRows = engine.procurement.data?.charts?.sankey || mainPayload.charts?.sankey || [];
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
        <p className="eyebrow">SP2I Decision Intelligence</p>
        <h1>Pilotage immobilier pour les decisions budgetaires</h1>
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
      {engine.isFetching ? <div className="live-refresh">Mise a jour des indicateurs en cours...</div> : null}

      {dashboard === "monitoring" ? (
        <AnalyticsHealthPage qa={engine.qa} />
      ) : (
        <>
          <EnterpriseKpiGrid kpis={kpis} loading={engine.isLoading} />

          {engine.isLoading ? <Skeleton rows={4} /> : null}

          <section className="analytics-command-grid">
            <InsightsPanel kpis={kpis} barRows={barRows} table={table} />
            <AnalyticsCard title="Du budget initial au budget optimise" eyebrow="Avant / apres arbitrage">
              <CapexWaterfall summary={kpis} />
            </AnalyticsCard>
          </section>

          <section className="bi-dashboard-grid">
            <AnalyticsCard title="Repartition des achats local / import" eyebrow="Decisions par lots">
              <ImportDecisionSankey rows={table} chartRows={barRows} sankeyRows={sankeyRows} />
            </AnalyticsCard>
            <AnalyticsCard title="Zones les plus couteuses" eyebrow="Lots et familles">
              <CapexHeatmap data={heatmapRows} />
            </AnalyticsCard>
            <AnalyticsCard title="Carte des risques projet" eyebrow="Probabilite et impact">
              <RiskMatrix rows={riskRows} />
            </AnalyticsCard>
            <AnalyticsCard title="Evolution financiere du projet" eyebrow="Scenarios et economies">
              <CapexTimeline data={timelineRows} />
            </AnalyticsCard>
          </section>

          <AnalyticsCard title="Analyse detaillee des lignes budgetaires" eyebrow="Tableau operationnel">
            <FactMetreGrid rows={table} total={total} />
          </AnalyticsCard>
        </>
      )}
    </main>
  );
}
