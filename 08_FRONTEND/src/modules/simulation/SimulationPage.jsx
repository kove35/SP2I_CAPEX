import React from "react";
import { ArrowRight, CheckCircle2, Clock3, ShieldAlert, Sparkles, TriangleAlert } from "lucide-react";
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
import { getProjectWorkflow, getBudgetStatus, isBudgetSynced } from "../../services/projectService";
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
  if (!lines.length) return "À évaluer";
  const highRisk = lines.filter((line) => String(line.risk_level || "").toLowerCase().includes("eleve") || String(line.risk_level || "").toLowerCase().includes("high")).length;
  if (highRisk > 0) return "Eleve";
  const mediumRisk = lines.filter((line) => String(line.risk_level || "").toLowerCase().includes("moyen") || String(line.risk_level || "").toLowerCase().includes("medium")).length;
  return mediumRisk > 0 ? "Moyen" : "Maitrise";
}

function formatPercent(value) {
  if (!Number.isFinite(value)) return "-";
  return `${value.toLocaleString("fr-FR", { maximumFractionDigits: 1 })} %`;
}

function navigateTo(route) {
  window.history.pushState({}, "", route);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

function RiskBadge({ value }) {
  const normalized = String(value || "").toLowerCase();
  const tone = normalized.includes("eleve") || normalized.includes("élevé") ? "high" : normalized.includes("moyen") ? "medium" : "low";
  return <span className={`scenario-risk-badge ${tone}`}>{value}</span>;
}

function CopilotMetric({ label, value, detail, tone = "neutral" }) {
  return (
    <div className={`copilot-metric ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {detail ? <small>{detail}</small> : null}
    </div>
  );
}

function RecommendationLine({ icon: Icon, tone = "ok", children }) {
  return (
    <li className={`recommendation-line ${tone}`}>
      <Icon size={16} />
      <span>{children}</span>
    </li>
  );
}

function ScenarioDecisionCopilot({
  activeScenario,
  loading,
  runSimulation,
  scenarioName,
  setScenarioName,
  dqeSummary,
  simulationDisabledReason,
  localBudget,
  savings,
  savingsRate,
  analyzedLines,
  importLineCount,
  dqeLineCount,
  simulatedLineCount,
  importableLineCount,
  retainedLineCount,
  criticalLines,
  scenarioRisk,
  simulation,
}) {
  const roi = localBudget ? (savings / localBudget) * 100 : NaN;
  const estimatedLeadTime = simulation ? "45-70 j" : "-";
  const planningImpact = criticalLines > 0 ? "À sécuriser" : simulation ? "Maîtrisé" : "À évaluer";
  const deliveryRisk = scenarioRisk === "Eleve" ? "Livraison critique" : scenarioRisk === "Moyen" ? "Surveillance" : "Maîtrisé";
  const isViable = Boolean(simulation && savings >= 0 && criticalLines === 0);
  const isReviewNeeded = Boolean(simulation && (criticalLines > 0 || scenarioRisk !== "Maitrise"));

  return (
    <aside className="scenario-decision-copilot" aria-label="Copilote décisionnel SP2I">
      <section className="copilot-block config">
        <div className="copilot-block-heading">
          <span>1 · Configurer</span>
          <strong>Que teste-t-on ?</strong>
        </div>
        <SimulationToolbar
          running={loading}
          onRun={runSimulation}
          scenarioName={scenarioName}
          onScenarioNameChange={setScenarioName}
          disabled={!dqeSummary.hasActiveDqe}
          disabledReason={simulationDisabledReason}
        />
      </section>

      {simulation ? (
        <>
          <section className="copilot-block impact">
            <div className="copilot-block-heading">
              <span>2 · Simuler / analyser</span>
              <strong>Impact simulé</strong>
            </div>
            <div className="copilot-metric-grid">
              <CopilotMetric label="Économie nette" value={formatMoney(savings)} tone="success" />
              <CopilotMetric label="ROI import" value={formatPercent(roi)} detail="économie / CAPEX local" />
              <CopilotMetric label="Taux économie" value={formatPercent(savingsRate)} />
              <CopilotMetric label="DQE / simulées" value={`${dqeLineCount || "-"} / ${simulatedLineCount || "-"}`} detail={`${importableLineCount} importables · ${retainedLineCount} retenues`} />
            </div>
            <div className="copilot-ops-grid">
              <span><Clock3 size={15} /> Délai logistique <strong>{estimatedLeadTime}</strong></span>
              <span><ShieldAlert size={15} /> Risque livraison <RiskBadge value={deliveryRisk} /></span>
              <span><TriangleAlert size={15} /> Lots critiques <strong>{criticalLines || 0}</strong></span>
              <span><ArrowRight size={15} /> Impact planning <strong>{planningImpact}</strong></span>
            </div>
          </section>

          <section className="copilot-block recommendation">
            <div className="copilot-block-heading">
              <span>3 · Décider</span>
              <strong>Recommandation SP2I</strong>
            </div>
            <div className="copilot-ai-card">
              <div>
                <Sparkles size={18} />
                <strong>{isViable ? "Scénario viable" : isReviewNeeded ? "Validation requise" : "Simulation à lancer"}</strong>
              </div>
              <p>
                {isViable
                  ? "Le scénario présente une économie exploitable avec un risque opérationnel maîtrisé."
                  : "Le scénario est exploitable, mais certains arbitrages doivent être sécurisés avant engagement achat."}
              </p>
            </div>
            <ul className="recommendation-list">
              <RecommendationLine icon={CheckCircle2}>Stratégie active : {activeScenario.label}</RecommendationLine>
              <RecommendationLine icon={savings >= 0 ? CheckCircle2 : TriangleAlert} tone={savings >= 0 ? "ok" : "warn"}>
                Économie {savings >= 0 ? "positive" : "à challenger"} : {formatMoney(savings)}
              </RecommendationLine>
              <RecommendationLine icon={scenarioRisk === "Eleve" ? TriangleAlert : CheckCircle2} tone={scenarioRisk === "Eleve" ? "warn" : "ok"}>
                Risque global : {scenarioRisk.toLowerCase()}
              </RecommendationLine>
              <RecommendationLine icon={criticalLines ? TriangleAlert : CheckCircle2} tone={criticalLines ? "warn" : "ok"}>
                {criticalLines ? "Vérifier les lots critiques avant approvisionnement." : "Aucun lot critique détecté dans la simulation."}
              </RecommendationLine>
            </ul>
          </section>
        </>
      ) : (
        <section className="copilot-block recommendation">
          <div className="copilot-block-heading">
            <span>2 · En attente</span>
            <strong>Simulation non lancée</strong>
          </div>
          <div className="copilot-ai-card">
            <div>
              <Sparkles size={18} />
              <strong>Prêt à simuler</strong>
            </div>
            <p>Configurez la stratégie {activeScenario.label}, puis lancez explicitement la simulation pour calculer les KPI, recommandations et arbitrages.</p>
          </div>
        </section>
      )}

      <section className="copilot-final-action">
        <div>
          <span>4 · Exécuter</span>
          <strong>Décision CAPEX prête pour achat</strong>
          <small>{simulation ? "Transférer les arbitrages vers le cockpit Approvisionnement." : "Lancez une simulation pour débloquer cette étape."}</small>
        </div>
        <button className="primary-action procurement-ready-action" type="button" disabled={!simulation} onClick={() => navigateTo("/app/procurement")}>
          Préparer l’approvisionnement
          <ArrowRight size={17} />
        </button>
      </section>
    </aside>
  );
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

function getCurrentProjectKey(state) {
  return state.activeProject || PROJECT_CONTEXT.code;
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
  const budgetStatus = getBudgetStatus(workflow);
  const budgetDone = budgetStatus === "SYNCED" || isBudgetSynced(workflow);

  React.useEffect(() => {
    setTab(defaultTab);
  }, [defaultTab]);

  React.useEffect(() => {
    setSimulation(null);
    setNotice("");
    setError("");
    setState((current) => {
      const projectKey = getCurrentProjectKey(current);
      if (!current.lastSimulation || current.lastSimulationProject === projectKey) return current;
      return { ...current, lastSimulation: null, lastSimulationProject: null };
    });
  }, [state.activeProject]);

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
      setState((current) => ({ ...current, activeScenario: scenarioName, lastSimulation: result, lastSimulationProject: getCurrentProjectKey(current) }));
      setNotice("Simulation du scénario lancée.");
    } catch (apiError) {
      try {
        const preview = await withTimeout(
          getSimulationAnalyticsPreview({}, { devise: "FCFA" }),
          SIMULATION_TIMEOUT_MS,
          "Le relais analytics"
        );
        const fallback = buildSimulationFromPreview(preview, scenarioName);
        setSimulation(fallback);
        setState((current) => ({ ...current, activeScenario: scenarioName, lastSimulation: fallback, lastSimulationProject: getCurrentProjectKey(current) }));
        setNotice(apiError.message || "Simulation du scénario lancée depuis les dernières données synchronisées.");
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

  const runCompare = async () => {
    if (scenarios.length < 2) return;
    const data = await compareScenarios(scenarios[0].scenario_id, scenarios[1].scenario_id);
    setComparison(data.comparison || []);
  };

  const kpi = simulation?.kpi || {};
  const lines = simulation?.lignes || [];
  const lineCounts = simulation?.metadata?.line_counts || {};
  const dqeLineCount = Number(kpi.lignes_dqe || lineCounts.dqe || dqeSummary.lines || 0);
  const simulatedLineCount = Number(kpi.lignes_simulees || lineCounts.simulees || kpi.lignes || lines.length || 0);
  const importableLineCount = Number(kpi.lignes_importables || lineCounts.importables || kpi.procurement?.LIGNES_IMPORTABLES || 0);
  const retainedLineCount = Number(kpi.lignes_retenues || lineCounts.retenues || kpi.lignes_import || lines.filter((row) => String(row.decision_finale || row.decision_import || "").toUpperCase() === "IMPORT").length);
  const arbitratedLineCount = Number(kpi.lignes_arbitrees || lineCounts.arbitrees || lines.filter((row) => row.decision_finale || row.decision_import).length);
  const analyzedLines = simulatedLineCount || Number(kpi.lignes || lines.length || 0);
  const importLineCount = retainedLineCount;
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
          title={budgetStatus === "SYNC_FAILED" ? "Synchronisation du budget echouee" : budgetStatus === "PARTIAL_SYNC" ? "Synchronisation partielle" : "Budget non synchronise"}
          message={
            budgetStatus === "SYNC_FAILED"
              ? "La synchronisation du budget a echoue. Relancez la synchronisation avant de tester un scenario."
              : budgetStatus === "PARTIAL_SYNC"
                ? "La synchronisation du budget est partielle. Verifiez la synchronisation avant de tester un scenario."
                : "Le budget doit etre synchronise avant de lancer les scenarios."
          }
          actionLabel={
            budgetStatus === "SYNC_FAILED"
              ? "Relancer la synchronisation"
              : budgetStatus === "PARTIAL_SYNC"
                ? "Verifier la synchronisation"
                : "Synchroniser le budget"
          }
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
        {!dqeSummary.hasActiveDqe ? <button type="button" className="primary-action secondary-action" onClick={() => navigateTo("/app/dqe?tab=import")}>Importer un DQE</button> : null}
      </section>

      {tab === "simulation" ? (
        <>
          {simulation ? (
            <section className="metric-grid">
              <KpiCard label="Budget local" value={formatMoney(localBudget)} />
              <KpiCard label="Budget optimise" value={formatMoney(optimizedBudget)} tone="success" />
              <KpiCard label="Economie nette" value={formatMoney(savings)} tone="warning" />
              <KpiCard label="Taux economie" value={formatPercent(savingsRate)} />
              <KpiCard label="Lignes DQE" value={dqeLineCount || "-"} />
              <KpiCard label="Lignes simulées" value={simulatedLineCount || "-"} />
              <KpiCard label="Importables" value={importableLineCount || "-"} />
              <KpiCard label="Retenues" value={retainedLineCount || "-"} />
              <KpiCard label="Arbitrées" value={arbitratedLineCount || "-"} />
              <KpiCard label="Risque scenario" value={scenarioRisk} tone={scenarioRisk === "Eleve" ? "warning" : "success"} />
            </section>
          ) : (
            <section className="metric-grid">
              <KpiCard label="Statut scénario" value="À lancer" />
              <KpiCard label="Source DQE" value={dqeLineCount || "-"} />
              <KpiCard label="Budget" value={budgetDone ? "Synchronisé" : "À synchroniser"} />
            </section>
          )}
          <section className="cockpit-split">
            <AnalyticsCard title="Lignes d'arbitrage du scenario" eyebrow={`${activeScenario.label} · ${scenarioStatus}`}>
              <div className="panel-scroll">
                {loading ? <Skeleton /> : <SimulationTable rows={lines} />}
              </div>
            </AnalyticsCard>
            <ScenarioDecisionCopilot
              activeScenario={activeScenario}
              loading={loading}
              runSimulation={runSimulation}
              scenarioName={scenarioName}
              setScenarioName={setScenarioName}
              dqeSummary={dqeSummary}
              simulationDisabledReason={simulationDisabledReason}
              localBudget={localBudget}
              savings={savings}
              savingsRate={savingsRate}
              analyzedLines={analyzedLines}
              importLineCount={importLineCount}
              dqeLineCount={dqeLineCount}
              simulatedLineCount={simulatedLineCount}
              importableLineCount={importableLineCount}
              retainedLineCount={retainedLineCount}
              criticalLines={criticalLines}
              scenarioRisk={scenarioRisk}
              simulation={simulation}
            />
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
