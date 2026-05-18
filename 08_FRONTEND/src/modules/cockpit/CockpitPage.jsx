import React from "react";
import CapexHeatmap from "../../components/charts/CapexHeatmap";
import CapexTimeline from "../../components/charts/CapexTimeline";
import CapexWaterfall from "../../components/charts/CapexWaterfall";
import ImportDecisionSankey from "../../components/charts/ImportDecisionSankey";
import RiskMatrix from "../../components/charts/RiskMatrix";
import GlobalAnalyticsFilters from "../../components/filters/GlobalAnalyticsFilters";
import FactMetreGrid from "../../components/grids/FactMetreGrid";
import InsightsPanel from "../../components/analytics/InsightsPanel";
import EnterpriseKpiGrid from "../../components/kpi/EnterpriseKpiGrid";
import { useAnalyticsEngine } from "../../hooks/useAnalyticsEngine";
import AnalyticsCard from "../../ui/AnalyticsCard";
import Skeleton from "../../ui/Skeleton";

export default function CockpitPage() {
  const engine = useAnalyticsEngine("direction");
  const mainPayload = engine.dashboard.data || {};
  const capexPayload = engine.capex.data || {};
  const kpis = { ...(capexPayload.kpis || {}), ...(mainPayload.kpis || {}) };
  const table = mainPayload.table?.length ? mainPayload.table : engine.drilldown.data?.table || [];
  const total = mainPayload.pagination?.total || engine.drilldown.data?.pagination?.total || table.length;
  const barRows = mainPayload.charts?.bar || capexPayload.charts?.bar || [];
  const heatmapRows = engine.heatmap.data?.charts?.heatmap || mainPayload.charts?.heatmap || [];
  const timelineRows = engine.timeline.data?.charts?.timeline || mainPayload.charts?.timeline || [];
  const riskRows = engine.risk.data?.charts?.risk_matrix || heatmapRows || table;

  return (
    <main className="cockpit-page analytics-engine-page">
      <section className="page-hero compact">
        <p className="eyebrow">Cockpit decisionnel immobilier</p>
        <h1>Pilotage CAPEX, risques, scenarios et decisions projet</h1>
        <p>SP2I Analytics Engine orchestre les KPI, les filtres, le drill-down et les decisions import/local en temps reel.</p>
      </section>

      {engine.error ? <div className="app-error">{engine.error.message}</div> : null}

      <GlobalAnalyticsFilters />
      {engine.isFetching ? <div className="live-refresh">Synchronisation du cockpit en cours...</div> : null}

      <EnterpriseKpiGrid kpis={kpis} loading={engine.isLoading} />
      {engine.isLoading ? <Skeleton /> : null}

      <section className="analytics-command-grid">
        <InsightsPanel kpis={kpis} barRows={barRows} table={table} />
        <AnalyticsCard title="Waterfall CAPEX" eyebrow="Direction">
          <CapexWaterfall summary={kpis} />
        </AnalyticsCard>
      </section>

      <section className="bi-dashboard-grid">
        <AnalyticsCard title="Sankey import/local" eyebrow="DecisionEngine">
          <ImportDecisionSankey rows={table} chartRows={barRows} />
        </AnalyticsCard>
        <AnalyticsCard title="Heatmap CAPEX" eyebrow="Lot x famille">
          <CapexHeatmap data={heatmapRows} />
        </AnalyticsCard>
        <AnalyticsCard title="Risk matrix" eyebrow="Pilotage projet">
          <RiskMatrix rows={riskRows} />
        </AnalyticsCard>
        <AnalyticsCard title="Timeline CAPEX" eyebrow="Simulation et economie">
          <CapexTimeline data={timelineRows} />
        </AnalyticsCard>
      </section>

      <AnalyticsCard title="Drill-down lignes CAPEX" eyebrow={`${Number(total || table.length).toLocaleString("fr-FR")} lignes chargees`}>
        <FactMetreGrid rows={table} total={total} />
      </AnalyticsCard>
    </main>
  );
}
