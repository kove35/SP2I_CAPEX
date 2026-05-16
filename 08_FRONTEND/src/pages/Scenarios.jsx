import React from "react";
import KpiCard from "../components/kpi/KpiCard";
import ScenarioComparison from "../components/procurement/ScenarioComparison";
import { compareScenarios, listScenarios } from "../services/scenarioService";

export default function Scenarios() {
  const [scenarios, setScenarios] = React.useState([]);
  const [scenarioA, setScenarioA] = React.useState("");
  const [scenarioB, setScenarioB] = React.useState("");
  const [comparison, setComparison] = React.useState([]);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    listScenarios()
      .then((data) => {
        const items = data.scenarios || [];
        setScenarios(items);
        setScenarioA(items[0]?.scenario_id || "");
        setScenarioB(items[1]?.scenario_id || "");
      })
      .catch((apiError) => setError(apiError.message));
  }, []);

  const compare = async () => {
    if (!scenarioA || !scenarioB) return;
    setError("");
    try {
      const data = await compareScenarios(scenarioA, scenarioB);
      setComparison(data.comparison || []);
    } catch (apiError) {
      setError(apiError.message);
    }
  };

  React.useEffect(() => {
    if (scenarioA && scenarioB) compare();
  }, [scenarioA, scenarioB]);

  return (
    <main className="page analytics-page">
      <header className="entete-page">
        <p>Scenarios</p>
        <h1>Comparaison CAPEX historisee</h1>
      </header>

      {error ? <div className="analytics-error">{error}</div> : null}

      <section className="analytics-toolbar">
        <label>
          Scenario A
          <select value={scenarioA} onChange={(event) => setScenarioA(event.target.value)}>
            {scenarios.map((scenario) => (
              <option key={scenario.scenario_id} value={scenario.scenario_id}>
                {scenario.scenario_nom}
              </option>
            ))}
          </select>
        </label>
        <label>
          Scenario B
          <select value={scenarioB} onChange={(event) => setScenarioB(event.target.value)}>
            {scenarios.map((scenario) => (
              <option key={scenario.scenario_id} value={scenario.scenario_id}>
                {scenario.scenario_nom}
              </option>
            ))}
          </select>
        </label>
        <button type="button" onClick={compare}>Comparer</button>
      </section>

      <section className="analytics-grid three">
        <KpiCard label="Scenarios disponibles" value={scenarios.length} />
        <KpiCard label="Comparaison" value={comparison.length ? "Active" : "En attente"} tone="success" />
        <KpiCard label="Source" value="PostgreSQL" />
      </section>

      <section className="analytics-card">
        <div className="section-title">
          <h2>BASELINE vs IMPORT vs LOCAL</h2>
          <span>v_kpi_scenario</span>
        </div>
        <ScenarioComparison rows={comparison} />
      </section>
    </main>
  );
}
