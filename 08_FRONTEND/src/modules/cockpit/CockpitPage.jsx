import React from "react";
import AnalyticsCard from "../../ui/AnalyticsCard";
import KpiCard from "../../ui/KpiCard";
import { formatMoney } from "../../shared/formatters";
import { defaultSimulationPayload, simulateCapex } from "../../services/simulationService";

export default function CockpitPage() {
  const [simulation, setSimulation] = React.useState(null);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    simulateCapex({ ...defaultSimulationPayload, scenario_name: "COCKPIT_OVERVIEW" })
      .then(setSimulation)
      .catch((apiError) => setError(apiError.message));
  }, []);

  const kpi = simulation?.kpi || {};
  const lines = simulation?.lignes || [];
  const containers = lines.filter((line) => line.container_strategy).length;
  const averageEta = lines.length
    ? Math.round(lines.reduce((sum, line) => sum + Number(line.lead_time_total || 0), 0) / lines.length)
    : 0;

  return (
    <main className="cockpit-page">
      <section className="page-hero compact">
        <p className="eyebrow">Cockpit decisionnel immobilier</p>
        <h1>Pilotage CAPEX, risques, scenarios et decisions projet</h1>
        <p>React orchestre les workflows operationnels. Power BI reste la couche analytique strategique.</p>
      </section>

      {error ? <div className="app-error">{error}</div> : null}

      <section className="metric-grid">
        <KpiCard label="CAPEX local" value={formatMoney(kpi.capex_local)} />
        <KpiCard label="CAPEX optimise" value={formatMoney(kpi.capex_optimise)} tone="success" />
        <KpiCard label="Economies" value={formatMoney(kpi.economie_nette)} tone="warning" />
        <KpiCard label="Moteurs optimisation" value={containers} />
        <KpiCard label="ETA moyen" value={`${averageEta} j`} />
      </section>

      <section className="dashboard-grid">
        <AnalyticsCard title="Workflow de pilotage immobilier" eyebrow="DQE vers decision">
          <div className="workflow-rail">
            {["DQE", "Simulation CAPEX", "Decision", "Procurement", "Supply Chain", "Chantier", "Power BI"].map((step) => (
              <span key={step}>{step}</span>
            ))}
          </div>
        </AnalyticsCard>
        <AnalyticsCard title="Alertes decisionnelles" eyebrow="Pilotage projet">
          <ul className="signal-list">
            <li>CAPEX optimise a valider sur scenario actif</li>
            <li>Criticite chantier a surveiller sur lots techniques</li>
            <li>Dashboards Power BI disponibles pour direction et finance</li>
          </ul>
        </AnalyticsCard>
      </section>
    </main>
  );
}
