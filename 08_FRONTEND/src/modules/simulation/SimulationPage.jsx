import React from "react";
import AnalyticsCard from "../../ui/AnalyticsCard";
import KpiCard from "../../ui/KpiCard";
import Skeleton from "../../ui/Skeleton";
import { formatMoney } from "../../shared/formatters";
import SimulationToolbar from "../../components/simulation/SimulationToolbar";
import SimulationTable from "../../components/simulation/SimulationTable";
import ScenarioComparison from "../../components/procurement/ScenarioComparison";
import { useAppStore } from "../../store/appStore.jsx";
import { defaultSimulationPayload, getSimulationAnalyticsPreview, simulateCapex } from "../../services/simulationService";
import { compareScenarios, listScenarios } from "../../services/scenarioService";
import { getProjectContext, getScenarioContext, PROJECT_CONTEXT } from "../../utils/businessContext";
import { getProjectWorkflow } from "../../services/projectService";
import WorkflowGuardEmptyState from "../projects/WorkflowGuardEmptyState";

const SIMULATION_TIMEOUT_MS = Number(import.meta.env.VITE_ANALYTICS_TIMEOUT_MS || 18000);
const DQE_SYNCED_STATUSES = ["SYNCED", "CERTIFIED", "CERTIFIED_WITH_WARNINGS"];

function withTimeout(promise, timeoutMs, label) {
  return Promise.race([
    promise,
    new Promise((_, reject) => {
      window.setTimeout(() => reject(new Error(`${label} ne repond pas assez vite. Snapshot analytics affiche. Synchronisation arriere-plan en cours.`)), timeoutMs);
    }),
  ]);
}

function riskLabel(value) {
  const score = Number(value || 0);
  if (score >= 70) return "Eleve";
  if (score >= 50) return "Moyen";
  return "Maitrise";
}

function scenarioRiskLabel(lines = []) {
  if (!lines.length) return "A evaluer";
  const highRisk = lines.filter((line) => String(line.risk_level || "").toLowerCase().includes("eleve") || String(line.risk_level || "").toLowerCase().includes("high")).length;
  if (highRisk > 0) return "Eleve";
  const mediumRisk = lines.filter((line) => String(line.risk_level || "").toLowerCase().includes("moyen") || String(line.risk_level || "").toLowerCase().includes("medium")).length;
  return mediumRisk > 0 ? "Moyen" : "Maitrise";
}

function formatPercent(value) {
  if (!Number.isFinite(value)) return "-";
  return `${value.toLocaleString("fr-FR", { maximumFractionDigits: 1 })} %`;
}

function readDqeVersions(projectId) {
  try {
    const stored = window.localStorage.getItem(`sp2i:dqeVersions:${projectId || PROJECT_CONTEXT.code}`);
    if (stored) {
      const parsed = JSON.parse(stored);
      return Array.isArray(parsed) ? parsed : [];
    }
  } catch {
    return [];
  }

  if ((projectId || PROJECT_CONTEXT.code) === PROJECT_CONTEXT.code) {
    return [{
      id: "seed-dqe-v1",
      version_number: 1,
      file_name: "DQE_PROJECT_SP2I.xlsx",
      status: "SYNCED",
      trust_score: 87,
      normalized_lines_count: 46,
      data_loss_count: 0,
      review_required_count: 0,
      is_active: true,
    }];
  }

  return [];
}

function getDqeSummary(projectId) {
  const versions = readDqeVersions(projectId);
  const active = versions.find((version) => version.is_active && DQE_SYNCED_STATUSES.includes(version.status));
  return {
    active,
    hasActiveDqe: Boolean(active),
    label: active ? `DQE v${active.version_number}` : "Aucun DQE actif",
    status: active?.status === "CERTIFIED" ? "Certifie" : active?.status === "CERTIFIED_WITH_WARNINGS" ? "Certifie avec points a verifier" : active?.status === "SYNCED" ? "Synchronise" : "Non disponible",
    trustScore: active?.trust_score,
    lines: active?.normalized_lines_count,
    dataLoss: active?.data_loss_count,
    reviewRequired: active?.review_required_count,
  };
}

function mapPreviewLine(row) {
  return {
    ...row,
    id_ligne: row.id_ligne || `${row.lot || "ligne"}-${row.designation}`,
    decision_finale: row.decision_ia || row.decision_import || "A etudier",
    economie_nette: Number(row.gain_net || row.economie_nette || 0),
    risk_level: riskLabel(row.risque),
    container_strategy: row.containers ? `${row.containers} container(s)` : "A consolider",
    lead_time_total: row.delai || row.lead_time_total || row.lead_time_days || 0,
  };
}

function buildSimulationFromPreview(preview, scenarioName) {
  const kpis = preview?.kpis || {};
  const rows = (preview?.table || []).map(mapPreviewLine);
  const capexLocal = Number(kpis.capex_local || rows.reduce((sum, row) => sum + Number(row.prix_local || 0), 0));
  const capexOptimise = Number(kpis.capex_chine_rendu_chantier || rows.reduce((sum, row) => sum + Number(row.landed_cost_chine || 0), 0));
  const economie = Number(kpis.gain_net_total || rows.reduce((sum, row) => sum + Number(row.economie_nette || 0), 0));

  return {
    status: "SUCCESS",
    scenario_name: scenarioName,
    kpi: {
      capex_local: capexLocal,
      capex_optimise: capexOptimise,
      economie_nette: economie,
      lignes: Number(kpis.nb_lignes || rows.length),
      lignes_import: Number(kpis.nb_import || rows.filter((row) => row.decision_finale === "IMPORT").length),
    },
    lignes: rows,
    metadata: {
      source: "analytics-procurement-lines",
      engine: preview?.metadata?.engine || "SP2I Analytics Engine",
    },
  };
}

export default function SimulationPage({ defaultTab = "simulation" }) {
  const [tab, setTab] = React.useState(defaultTab);
  const [scenarioName, setScenarioName] = React.useState(defaultSimulationPayload.scenario_name);
  const [simulation, setSimulation] = React.useState(null);
  const [scenarios, setScenarios] = React.useState([]);
  const [comparison, setComparison] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [notice, setNotice] = React.useState("");
  const { state, setState } = useAppStore();
  const dqeSummary = React.useMemo(() => getDqeSummary(state.activeProject || PROJECT_CONTEXT.code), [state.activeProject]);
  const workflow = React.useMemo(
    () => getProjectWorkflow(state.activeProjectDetails || { id: state.activeProject, workspace_key: state.activeProject }, state),
    [state]
  );
  const setupDone = workflow.steps.find((step) => step.id === "configuration")?.state === "done";
  const budgetDone = workflow.steps.find((step) => step.id === "budget")?.state === "done";

  React.useEffect(() => {
    setTab(defaultTab);
  }, [defaultTab]);

  const runSimulation = async () => {
    if (!dqeSummary.hasActiveDqe) {
      setError("Aucune version DQE active disponible. Importez et validez un DQE avant de lancer une simulation.");
      return;
    }

    setLoading(true);
    setError("");
    setNotice("");
    try {
      const result = await withTimeout(
        simulateCapex({ ...defaultSimulationPayload, scenario_name: scenarioName, persist: false }),
        SIMULATION_TIMEOUT_MS,
        "La simulation temps reel"
      );
      const hasUsableResult = Number(result?.kpi?.capex_local || 0) > 0 && Array.isArray(result?.lignes) && result.lignes.length > 0;

      if (!hasUsableResult) {
        throw new Error("La simulation a retourne un resultat vide.");
      }

      setSimulation(result);
      setState((current) => ({ ...current, activeScenario: scenarioName, lastSimulation: result }));
    } catch (apiError) {
      try {
        const preview = await withTimeout(
          getSimulationAnalyticsPreview({}, { devise: "FCFA" }),
          SIMULATION_TIMEOUT_MS,
          "Le relais analytics"
        );
        const fallback = buildSimulationFromPreview(preview, scenarioName);
        setSimulation(fallback);
        setState((current) => ({ ...current, activeScenario: scenarioName, lastSimulation: fallback }));
        setNotice(apiError.message || "Affichage des dernieres donnees synchronisees.");
      } catch (previewError) {
        setError(previewError.message || apiError.message);
      }
    } finally {
      setLoading(false);
      withTimeout(listScenarios(), 8000, "L'historique des strategies")
        .then((scenarioData) => {
          setScenarios(scenarioData.scenarios || []);
        })
        .catch((scenarioError) => {
          console.warn("SCENARIOS HISTORY UNAVAILABLE", scenarioError);
          setScenarios([]);
        });
    }
  };

  React.useEffect(() => {
    if (dqeSummary.hasActiveDqe) runSimulation();
  }, [dqeSummary.hasActiveDqe]);

  const runCompare = async () => {
    if (scenarios.length < 2) return;
    const data = await compareScenarios(scenarios[0].scenario_id, scenarios[1].scenario_id);
    setComparison(data.comparison || []);
  };

  const kpi = simulation?.kpi || {};
  const lines = simulation?.lignes || [];
  const analyzedLines = Number(kpi.lignes || lines.length || 0);
  const importLineCount = Number(kpi.lignes_import || lines.filter((row) => String(row.decision_finale || row.decision_import || "").toUpperCase() === "IMPORT").length);
  const criticalLines = lines.filter((line) => String(line.risk_level || "").toLowerCase().includes("eleve") || String(line.risk_level || "").toLowerCase().includes("high")).length;
  const localBudget = Number(kpi.capex_local || 0);
  const optimizedBudget = Number(kpi.capex_optimise || 0);
  const savings = Number(kpi.economie_nette || Math.max(localBudget - optimizedBudget, 0));
  const savingsRate = localBudget ? (savings / localBudget) * 100 : NaN;
  const scenarioRisk = scenarioRiskLabel(lines);
  const scenarioStatus = simulation ? "Simule" : "Brouillon";
  const activeScenario = getScenarioContext(scenarioName);
  const activeProject = getProjectContext(state.activeProject);
  const simulationDisabledReason = !dqeSummary.hasActiveDqe
    ? "Importez et validez un DQE avant de lancer une simulation."
    : "";

  return (
    <main className="cockpit-page cockpit-page-fit">
      <section className="page-hero compact">
        <p className="eyebrow">Budget & scenarios</p>
        <h1>Simuler les scenarios CAPEX et arbitrer les decisions projet</h1>
        <p>Comparez les hypotheses import/local, mesurez les economies et preparez les decisions d'achat du projet.</p>
      </section>

      <div className="tab-row">
        <button className={tab === "simulation" ? "active" : ""} onClick={() => setTab("simulation")} type="button">Simuler</button>
        <button className={tab === "scenarios" ? "active" : ""} onClick={() => setTab("scenarios")} type="button">Hypotheses</button>
        <button className={tab === "compare" ? "active" : ""} onClick={() => setTab("compare")} type="button">Comparer</button>
        <button className={tab === "history" ? "active" : ""} onClick={() => setTab("history")} type="button">Historique</button>
      </div>

      {error ? <div className="app-error">{error}</div> : null}
      {notice ? <div className="app-warning">{notice}</div> : null}
      {!setupDone ? (
        <WorkflowGuardEmptyState
          title="Configuration projet requise"
          message="Ce projet doit etre configure avant de poursuivre le workflow CAPEX."
          actionLabel="Configurer le projet"
          actionRoute="/app/projects"
          severity="blocking"
          currentStep={workflow.label}
          requiredStep="Configuration projet"
          testId="scenario-empty-state"
        />
      ) : !dqeSummary.hasActiveDqe ? (
        <WorkflowGuardEmptyState
          title="Aucun DQE actif"
          message="Aucun DQE actif. Importez et certifiez un DQE avant de lancer une simulation."
          actionLabel="Importer un DQE"
          actionRoute="/app/dqe?tab=import"
          currentStep={workflow.steps.find((step) => step.id === "dqe")?.status}
          requiredStep="DQE certifie"
          testId="scenario-empty-state"
        />
      ) : !budgetDone ? (
        <WorkflowGuardEmptyState
          title="Budget non synchronise"
          message="Le budget doit etre synchronise avant de lancer les scenarios."
          actionLabel="Synchroniser le budget"
          actionRoute="/app/dqe?tab=sync"
          currentStep={workflow.steps.find((step) => step.id === "budget")?.status}
          requiredStep="Budget synchronise"
          testId="scenario-empty-state"
        />
      ) : null}
      <section className={`scenario-source-strip ${dqeSummary.hasActiveDqe ? "ready" : "blocked"}`}>
        <div>
          <strong>Source donnees : {dqeSummary.label}</strong>
          <span>
            {dqeSummary.hasActiveDqe
              ? `${dqeSummary.status} · Trust score ${dqeSummary.trustScore ?? "-"}/100 · ${dqeSummary.lines ?? "-"} lignes exploitables`
              : "Aucun DQE actif. Importez et validez un DQE avant de lancer une simulation."}
          </span>
        </div>
        <div>
          <strong>Gouvernance</strong>
          <span>
            {dqeSummary.hasActiveDqe
              ? `${dqeSummary.dataLoss ?? 0} perte stricte · ${dqeSummary.reviewRequired ?? 0} revue bloquante`
              : "Gouvernance indisponible sans version DQE active"}
          </span>
        </div>
        {!dqeSummary.hasActiveDqe ? <button type="button" className="primary-action secondary-action" onClick={() => { window.history.pushState({}, "", "/app/dqe?tab=import"); window.dispatchEvent(new PopStateEvent("popstate")); }}>Importer un DQE</button> : null}
      </section>

      {tab === "simulation" ? (
        <>
          <section className="metric-grid">
            <KpiCard label="Budget local" value={formatMoney(localBudget)} />
            <KpiCard label="Budget optimise" value={formatMoney(optimizedBudget)} tone="success" />
            <KpiCard label="Economie nette" value={formatMoney(savings)} tone="warning" />
            <KpiCard label="Taux economie" value={formatPercent(savingsRate)} />
            <KpiCard label="Lignes analysees" value={analyzedLines || "-"} />
            <KpiCard label="Risque scenario" value={scenarioRisk} tone={scenarioRisk === "Eleve" ? "warning" : "success"} />
          </section>
          <section className="cockpit-split">
            <AnalyticsCard title="Lignes d'arbitrage du scenario" eyebrow={`${activeScenario.label} · ${scenarioStatus}`}>
              <div className="panel-scroll">
                {loading ? <Skeleton /> : <SimulationTable rows={lines} />}
              </div>
            </AnalyticsCard>
            <aside className="context-panel">
              <AnalyticsCard title="Scenario actif" eyebrow="Decision projet">
                <ul className="signal-list">
                  <li>Strategie active : {activeScenario.label}</li>
                  <li>Statut scenario : {scenarioStatus}</li>
                  <li>Source : {dqeSummary.label}</li>
                  <li>Risque : {scenarioRisk}</li>
                </ul>
              </AnalyticsCard>
              <AnalyticsCard title="Hypotheses" eyebrow="Parametres CAPEX">
                <SimulationToolbar running={loading} onRun={runSimulation} scenarioName={scenarioName} onScenarioNameChange={setScenarioName} disabled={!dqeSummary.hasActiveDqe} disabledReason={simulationDisabledReason} />
              </AnalyticsCard>
              <AnalyticsCard title="Impact estime" eyebrow="Resultat scenario">
                <ul className="signal-list">
                  <li>Economie estimee : {formatMoney(savings)}</li>
                  <li>Taux economie : {formatPercent(savingsRate)}</li>
                  <li>Lignes analysees : {analyzedLines || "-"}</li>
                  <li>Risque : {scenarioRisk.toLowerCase()}</li>
                </ul>
              </AnalyticsCard>
              <AnalyticsCard title="Synthese de decision" eyebrow="Arbitrage projet">
                <ul className="signal-list">
                  <li>{analyzedLines || 0} lignes analysees.</li>
                  <li>{importLineCount} lignes orientees import.</li>
                  <li>{formatMoney(savings)} d'economie nette estimee.</li>
                  <li>{criticalLines} ligne(s) a risque eleve.</li>
                  <li>Decision : {criticalLines ? "validation requise avant arbitrage." : "scenario exploitable pour comparaison."}</li>
                </ul>
                <button className="primary-action secondary-action" type="button" disabled={!simulation} onClick={() => { window.history.pushState({}, "", "/app/procurement"); window.dispatchEvent(new PopStateEvent("popstate")); }}>
                  Preparer l'approvisionnement
                </button>
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
