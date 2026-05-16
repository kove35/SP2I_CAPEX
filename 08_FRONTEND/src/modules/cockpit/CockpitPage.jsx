import React from "react";
import CapexWaterfall from "../../components/charts/CapexWaterfall";
import ImportDecisionSankey from "../../components/charts/ImportDecisionSankey";
import RiskMatrix from "../../components/charts/RiskMatrix";
import GlobalFilterBar from "../../components/filters/GlobalFilterBar";
import SmartDataGrid from "../../components/grids/SmartDataGrid";
import EnterpriseKpiCard from "../../components/kpi/EnterpriseKpiCard";
import { useDashboardData } from "../../hooks/useDashboardData";
import AnalyticsCard from "../../ui/AnalyticsCard";
import Skeleton from "../../ui/Skeleton";
import { formatMoney } from "../../shared/formatters";
import { defaultSimulationPayload, simulateCapex } from "../../services/simulationService";

export default function CockpitPage() {
  const [simulation, setSimulation] = React.useState(null);
  const [error, setError] = React.useState("");
  const { summary, factMetre, scenarios, isLoading } = useDashboardData();

  React.useEffect(() => {
    simulateCapex({ ...defaultSimulationPayload, scenario_name: "COCKPIT_OVERVIEW" })
      .then(setSimulation)
      .catch((apiError) => setError(`Simulation cockpit indisponible : ${apiError.message}`));
  }, []);

  const kpi = summary.data || simulation?.kpi || {};
  const lines = factMetre.data?.length ? factMetre.data : simulation?.lignes || [];
  const containers = lines.filter((line) => line.container_strategy).length;
  const averageEta = lines.length
    ? Math.round(lines.reduce((sum, line) => sum + Number(line.lead_time_total || 0), 0) / lines.length)
    : 0;
  const scenarioCount = scenarios.data?.scenarios?.length || 0;
  const gridColumns = React.useMemo(
    () => [
      { field: "lot", headerName: "Lot" },
      { field: "famille", headerName: "Famille" },
      { field: "designation", headerName: "Designation", flex: 1, minWidth: 260 },
      { field: "capex_local", headerName: "CAPEX local", type: "numericColumn" },
      { field: "capex_optimise", headerName: "CAPEX optimise", type: "numericColumn" },
      { field: "decision_import", headerName: "Decision" },
    ],
    []
  );

  return (
    <main className="cockpit-page">
      <section className="page-hero compact">
        <p className="eyebrow">Cockpit decisionnel immobilier</p>
        <h1>Pilotage CAPEX, risques, scenarios et decisions projet</h1>
        <p>React orchestre les workflows operationnels. Power BI reste la couche analytique strategique.</p>
      </section>

      {error ? <div className="app-error">{error}</div> : null}

      <GlobalFilterBar />

      <section className="metric-grid enterprise-metric-grid">
        <EnterpriseKpiCard label="CAPEX brut" value={formatMoney(kpi.capex_local)} helper="PostgreSQL Render" />
        <EnterpriseKpiCard label="CAPEX optimise" value={formatMoney(kpi.capex_optimise)} tone="green" helper="Moteur CAPEX" />
        <EnterpriseKpiCard label="Economie nette" value={formatMoney(kpi.economie || kpi.economie_nette)} tone="amber" helper="Ratio des totaux" />
        <EnterpriseKpiCard label="Scenarios" value={scenarioCount} helper="Historisation" />
        <EnterpriseKpiCard label="ETA moyen" value={`${averageEta} j`} tone="cyan" helper={`${containers} moteurs logistiques`} />
      </section>

      {isLoading ? <Skeleton /> : null}

      <section className="dashboard-grid">
        <AnalyticsCard title="Waterfall CAPEX" eyebrow="Direction">
          <CapexWaterfall summary={kpi} />
        </AnalyticsCard>
        <AnalyticsCard title="Matrice import/local" eyebrow="DecisionEngine">
          <ImportDecisionSankey rows={lines} />
        </AnalyticsCard>
        <AnalyticsCard title="Risk matrix" eyebrow="Pilotage projet">
          <RiskMatrix rows={lines} />
        </AnalyticsCard>
        <AnalyticsCard title="Alertes decisionnelles" eyebrow="Pilotage projet">
          <ul className="signal-list">
            <li>CAPEX optimise a valider sur scenario actif</li>
            <li>Criticite chantier a surveiller sur lots techniques</li>
            <li>Dashboards Power BI disponibles pour direction et finance</li>
          </ul>
        </AnalyticsCard>
      </section>
      <AnalyticsCard title="Drill-down lignes CAPEX" eyebrow={`${lines.length} lignes chargees`}>
        <SmartDataGrid rows={lines} columns={gridColumns} height={460} />
      </AnalyticsCard>
    </main>
  );
}
