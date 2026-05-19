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
  direction: "Synthese courte pour suivre les indicateurs essentiels et les alertes de direction.",
  capex: "Lecture financiere detaillee du budget travaux, des economies et des postes les plus couteux.",
  procurement: "Analyse des achats, de l'importabilite, des fournisseurs et des decisions local/import.",
  logistics: "Vue logistique du projet pour securiser les livraisons, les couts et les delais.",
  risks: "Carte decisionnelle des risques, de la criticite et du potentiel d'economie.",
  heatmaps: "Repere les lots, familles ou zones qui concentrent le plus de budget.",
  drilldown: "Analyse detaillee des lignes budgetaires avec selection interactive et filtres globaux.",
  timeline: "Evolution des strategies, des economies et des decisions dans le temps.",
  monitoring: "Etat du systeme, qualite des donnees, base projet et coherence des indicateurs.",
};

function DirectionIndicatorsView({ engine, kpis, barRows, table, riskRows }) {
  return (
    <>
      <EnterpriseKpiGrid kpis={kpis} loading={engine.isLoading} />
      {engine.isLoading ? <Skeleton rows={3} /> : null}
      <section className="analytics-command-grid">
        <InsightsPanel kpis={kpis} barRows={barRows} table={table} />
        <AnalyticsCard title="Alertes de direction" eyebrow="Priorites a surveiller">
          <RiskMatrix rows={riskRows} />
        </AnalyticsCard>
      </section>
    </>
  );
}

function BudgetWorksView({ engine, kpis, heatmapRows, table, total }) {
  return (
    <>
      <EnterpriseKpiGrid kpis={kpis} loading={engine.isLoading} />
      {engine.isLoading ? <Skeleton rows={3} /> : null}
      <section className="analytics-command-grid">
        <AnalyticsCard title="Du budget initial au budget optimise" eyebrow="Lecture financiere">
          <CapexWaterfall summary={kpis} />
        </AnalyticsCard>
        <AnalyticsCard title="Postes les plus couteux" eyebrow="Concentration budgetaire">
          <CapexHeatmap data={heatmapRows} rows={table} />
        </AnalyticsCard>
      </section>
      <AnalyticsCard title="Lignes budgetaires du projet" eyebrow={`${Number(total || table.length).toLocaleString("fr-FR")} postes analyses`}>
        <FactMetreGrid rows={table} total={total} />
      </AnalyticsCard>
    </>
  );
}

function ProcurementView({ table, barRows, sankeyRows }) {
  return (
    <section className="bi-dashboard-grid">
      <AnalyticsCard title="Repartition des achats local / import" eyebrow="Arbitrages par lots">
        <ImportDecisionSankey rows={table} chartRows={barRows} sankeyRows={sankeyRows} />
      </AnalyticsCard>
      <AnalyticsCard title="Analyse detaillee des achats" eyebrow="Postes concernes">
        <FactMetreGrid rows={table} total={table.length} />
      </AnalyticsCard>
    </section>
  );
}

function RiskView({ riskRows, table }) {
  return (
    <>
      <AnalyticsCard title="Carte des risques projet" eyebrow="Impact et probabilite">
        <RiskMatrix rows={riskRows} />
      </AnalyticsCard>
      <AnalyticsCard title="Postes exposes" eyebrow="Lignes a surveiller">
        <FactMetreGrid rows={table} total={table.length} />
      </AnalyticsCard>
    </>
  );
}

function CostMapView({ heatmapRows, table }) {
  return (
    <>
      <AnalyticsCard title="Cartographie des couts" eyebrow="Lots et familles metier">
        <CapexHeatmap data={heatmapRows} rows={table} />
      </AnalyticsCard>
      <AnalyticsCard title="Details des zones couteuses" eyebrow="Postes budgetaires">
        <FactMetreGrid rows={table} total={table.length} />
      </AnalyticsCard>
    </>
  );
}

function DetailView({ table, total }) {
  return (
    <AnalyticsCard title="Analyse detaillee des lignes budgetaires" eyebrow={`${Number(total || table.length).toLocaleString("fr-FR")} postes disponibles`}>
      <FactMetreGrid rows={table} total={total} />
    </AnalyticsCard>
  );
}

function TimelineView({ timelineRows, kpis }) {
  return (
    <section className="analytics-command-grid">
      <AnalyticsCard title="Evolution financiere du projet" eyebrow="Strategies et economies">
        <CapexTimeline data={timelineRows} />
      </AnalyticsCard>
      <AnalyticsCard title="Budget final projete" eyebrow="Trajectoire budgetaire">
        <CapexWaterfall summary={kpis} />
      </AnalyticsCard>
    </section>
  );
}

function LogisticsView({ table, timelineRows }) {
  return (
    <section className="analytics-command-grid">
      <AnalyticsCard title="Impact logistique sur le projet" eyebrow="Delais et livraisons">
        <CapexTimeline data={timelineRows} />
      </AnalyticsCard>
      <AnalyticsCard title="Postes sensibles aux delais" eyebrow="Approvisionnement">
        <FactMetreGrid rows={table} total={table.length} />
      </AnalyticsCard>
    </section>
  );
}

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

  const renderDashboard = () => {
    if (dashboard === "monitoring") return <AnalyticsHealthPage qa={engine.qa} />;
    if (dashboard === "direction") {
      return <DirectionIndicatorsView engine={engine} kpis={kpis} barRows={barRows} table={table} riskRows={riskRows} />;
    }
    if (dashboard === "capex") {
      return <BudgetWorksView engine={engine} kpis={kpis} heatmapRows={heatmapRows} table={table} total={total} />;
    }
    if (dashboard === "procurement") {
      return <ProcurementView table={table} barRows={barRows} sankeyRows={sankeyRows} />;
    }
    if (dashboard === "logistics") {
      return <LogisticsView table={table} timelineRows={timelineRows} />;
    }
    if (dashboard === "risks") {
      return <RiskView riskRows={riskRows} table={table} />;
    }
    if (dashboard === "heatmaps") {
      return <CostMapView heatmapRows={heatmapRows} table={table} />;
    }
    if (dashboard === "drilldown") {
      return <DetailView table={table} total={total} />;
    }
    if (dashboard === "timeline") {
      return <TimelineView timelineRows={timelineRows} kpis={kpis} />;
    }
    return <DirectionIndicatorsView engine={engine} kpis={kpis} barRows={barRows} table={table} riskRows={riskRows} />;
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

      {renderDashboard()}
    </main>
  );
}
