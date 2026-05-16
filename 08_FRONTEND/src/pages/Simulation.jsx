import React from "react";
import KpiCard from "../components/kpi/KpiCard";
import RiskCard from "../components/kpi/RiskCard";
import SimpleBarChart from "../components/charts/SimpleBarChart";
import SimulationToolbar from "../components/simulation/SimulationToolbar";
import SimulationTable from "../components/simulation/SimulationTable";
import { defaultSimulationPayload, simulateCapex } from "../services/simulationService";

function money(value) {
  return `${Number(value || 0).toLocaleString("fr-FR", { maximumFractionDigits: 0 })} FCFA`;
}

export default function Simulation() {
  const [scenarioName, setScenarioName] = React.useState(defaultSimulationPayload.scenario_name);
  const [result, setResult] = React.useState(null);
  const [error, setError] = React.useState("");
  const [loading, setLoading] = React.useState(false);

  const runSimulation = async () => {
    setLoading(true);
    setError("");
    try {
      const payload = {
        ...defaultSimulationPayload,
        scenario_name: scenarioName,
      };
      const data = await simulateCapex(payload);
      setResult(data);
    } catch (apiError) {
      setError(apiError.message);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    runSimulation();
  }, []);

  const kpi = result?.kpi || {};
  const rows = result?.lignes || [];
  const averageRisk = rows.length
    ? Math.round(rows.reduce((sum, row) => sum + Number(row.global_risk_score || 0), 0) / rows.length)
    : 0;
  const averageEta = rows.length
    ? Math.round(rows.reduce((sum, row) => sum + Number(row.lead_time_total || row.lead_time_days || 0), 0) / rows.length)
    : 0;

  return (
    <main className="page analytics-page">
      <header className="entete-page">
        <p>Cockpit SP2I</p>
        <h1>Simulation CAPEX, decision et logistique</h1>
      </header>

      <SimulationToolbar
        running={loading}
        onRun={runSimulation}
        scenarioName={scenarioName}
        onScenarioNameChange={setScenarioName}
      />

      {error ? <div className="analytics-error">{error}</div> : null}

      <section className="analytics-grid four">
        <KpiCard label="CAPEX local" value={money(kpi.capex_local)} />
        <KpiCard label="CAPEX optimise" value={money(kpi.capex_optimise)} tone="success" />
        <KpiCard label="Economies" value={money(kpi.economie_nette)} tone="warning" />
        <KpiCard label="ETA moyen" value={`${averageEta} j`} help="Simulation backend" />
      </section>

      <section className="analytics-grid two">
        <RiskCard title="Risque global" level={averageRisk >= 60 ? "HIGH" : averageRisk >= 30 ? "MEDIUM" : "LOW"} score={`${averageRisk}/100`} />
        <SimpleBarChart
          title="CAPEX"
          data={[
            { label: "Local", value: kpi.capex_local, display: money(kpi.capex_local) },
            { label: "Optimise", value: kpi.capex_optimise, display: money(kpi.capex_optimise) },
            { label: "Economie", value: kpi.economie_nette, display: money(kpi.economie_nette) },
          ]}
        />
      </section>

      <section className="analytics-card">
        <div className="section-title">
          <h2>Table simulation</h2>
          <span>{result?.metadata?.simulation_id || "Simulation non lancee"}</span>
        </div>
        <SimulationTable rows={rows} />
      </section>
    </main>
  );
}
