import React from "react";
import AnalyticsCard from "../../ui/AnalyticsCard";
import KpiCard from "../../ui/KpiCard";
import Skeleton from "../../ui/Skeleton";
import { formatMoney } from "../../shared/formatters";
import SimulationToolbar from "../../components/simulation/SimulationToolbar";
import SimulationTable from "../../components/simulation/SimulationTable";
import ScenarioComparison from "../../components/procurement/ScenarioComparison";
import { useAppStore } from "../../store/appStore.jsx";
import { defaultSimulationPayload, simulateCapex } from "../../services/simulationService";
import { compareScenarios, listScenarios } from "../../services/scenarioService";
import { getProjectContext, getScenarioContext } from "../../utils/businessContext";

export default function SimulationPage({ defaultTab = "simulation" }) {
  const [tab, setTab] = React.useState(defaultTab);
  const [scenarioName, setScenarioName] = React.useState(defaultSimulationPayload.scenario_name);
  const [simulation, setSimulation] = React.useState(null);
  const [scenarios, setScenarios] = React.useState([]);
  const [comparison, setComparison] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const { setState } = useAppStore();

  React.useEffect(() => {
    setTab(defaultTab);
  }, [defaultTab]);

  const runSimulation = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await simulateCapex({ ...defaultSimulationPayload, scenario_name: scenarioName });
      setSimulation(result);
      setState((current) => ({ ...current, activeScenario: scenarioName, lastSimulation: result }));
      try {
        const scenarioData = await listScenarios();
        setScenarios(scenarioData.scenarios || []);
      } catch (scenarioError) {
        console.warn("SCENARIOS HISTORY UNAVAILABLE", scenarioError);
        setScenarios([]);
      }
    } catch (apiError) {
      setError(apiError.message);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    runSimulation();
  }, []);

  const runCompare = async () => {
    if (scenarios.length < 2) return;
    const data = await compareScenarios(scenarios[0].scenario_id, scenarios[1].scenario_id);
    setComparison(data.comparison || []);
  };

  const kpi = simulation?.kpi || {};
  const lines = simulation?.lignes || [];
  const criticalLines = lines.filter((line) => String(line.risk_level || "").toUpperCase().includes("HIGH")).length;
  const importedLines = kpi.lignes ? Math.round((Number(kpi.lignes_import || 0) / Number(kpi.lignes || 1)) * 100) : 0;
  const activeScenario = getScenarioContext(scenarioName);
  const activeProject = getProjectContext();

  return (
    <main className="cockpit-page cockpit-page-fit">
      <section className="page-hero compact">
        <p className="eyebrow">Budget & scenarios</p>
        <h1>Tester les options et comparer les decisions projet</h1>
      </section>

      <div className="tab-row">
        <button className={tab === "simulation" ? "active" : ""} onClick={() => setTab("simulation")} type="button">Simulation</button>
        <button className={tab === "scenarios" ? "active" : ""} onClick={() => setTab("scenarios")} type="button">Strategies</button>
        <button className={tab === "history" ? "active" : ""} onClick={() => setTab("history")} type="button">Historique</button>
        <button className={tab === "compare" ? "active" : ""} onClick={() => setTab("compare")} type="button">Comparaison</button>
      </div>

      {error ? <div className="app-error">{error}</div> : null}

      {tab === "simulation" ? (
        <>
          <section className="metric-grid">
            <KpiCard label="Budget local" value={formatMoney(kpi.capex_local)} />
            <KpiCard label="Budget optimise" value={formatMoney(kpi.capex_optimise)} tone="success" />
            <KpiCard label="Economies" value={formatMoney(kpi.economie_nette)} tone="warning" />
            <KpiCard label="Imports recommandes" value={`${importedLines}%`} />
          </section>
          <section className="cockpit-split">
            <AnalyticsCard title="Lignes de la strategie testee" eyebrow={activeScenario.label}>
              <div className="panel-scroll">
                {loading ? <Skeleton /> : <SimulationTable rows={lines} />}
              </div>
            </AnalyticsCard>
            <aside className="context-panel">
              <SimulationToolbar running={loading} onRun={runSimulation} scenarioName={scenarioName} onScenarioNameChange={setScenarioName} />
              <AnalyticsCard title="Synthese de decision" eyebrow="Arbitrage projet">
                <ul className="signal-list">
                  <li>{lines.length} lignes analysees dans la strategie active.</li>
                  <li>{importedLines}% d'imports recommandes par le moteur.</li>
                  <li>{criticalLines} lignes a risque eleve a verifier.</li>
                  <li>Les details financiers restent consolides dans la base projet et le cockpit direction.</li>
                </ul>
              </AnalyticsCard>
            </aside>
          </section>
        </>
      ) : (
        <AnalyticsCard
          title={tab === "history" ? "Historique des strategies" : tab === "compare" ? "Comparer les strategies" : "Strategies disponibles"}
          eyebrow={`${scenarios.length} strategies sauvegardees`}
          action={tab === "compare" ? <button className="primary-action" type="button" onClick={runCompare}>Comparer les 2 derniers</button> : null}
        >
          {tab === "compare" ? (
            <ScenarioComparison rows={comparison} />
          ) : (
            <div className="data-table-wrap panel-scroll">
              <table className="data-table">
                <thead><tr><th>Strategie</th><th>Orientation</th><th>Projet</th><th>Date</th></tr></thead>
                <tbody>
                  {scenarios.map((scenario) => (
                    <tr key={scenario.scenario_id}>
                      <td>{getScenarioContext(scenario.scenario_nom || scenario.name).label}</td>
                      <td>{getScenarioContext(scenario.scenario_type || scenario.scenario_nom).description}</td>
                      <td>{activeProject.label}</td>
                      <td>{scenario.created_at || "-"}</td>
                    </tr>
                  ))}
                  {!scenarios.length ? <tr><td colSpan="4">Lance une simulation pour charger les strategies.</td></tr> : null}
                </tbody>
              </table>
            </div>
          )}
        </AnalyticsCard>
      )}
    </main>
  );
}
