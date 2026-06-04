import React from "react";
import { Download, RefreshCcw } from "lucide-react";
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
import { useWorkflow } from "../../hooks/useWorkflow";
import { useAppStore } from "../../store/appStore.jsx";
import ProjectQuickActions from "../../components/ProjectQuickActions";
import { demoProjects, getProjectPrimaryAction, getProjectWorkspaceKey, listProjectWorkflowEvents, exportProjectReportPdf } from "../../services/projectService";
import ProjectWorkflowStepper from "../projects/ProjectWorkflowStepper";
import WorkflowGuardEmptyState from "../projects/WorkflowGuardEmptyState";
import AnalyticsCard from "../../ui/AnalyticsCard";
import Skeleton from "../../ui/Skeleton";
import AnalyticsHealthPage from "./AnalyticsHealthPage";
import { formatMoney } from "../../shared/formatters";

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
  if (engine.error && !Object.keys(kpis || {}).length) return null;
  return (
    <>
      <EnterpriseKpiGrid kpis={kpis} loading={engine.isLoading} />
      {engine.isLoading ? <Skeleton rows={3} /> : null}
      <section className="analytics-command-grid">
        <InsightsPanel kpis={kpis} barRows={barRows} table={table} />
        <AnalyticsCard title="Alertes de direction" eyebrow="Priorités à surveiller">
          <RiskMatrix rows={riskRows} />
        </AnalyticsCard>
      </section>
    </>
  );
}

function navigateTo(path) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

function getWorkspaceProject(state) {
  if (state.activeProjectDetails) return state.activeProjectDetails;
  return demoProjects.find((project) => getProjectWorkspaceKey(project) === state.activeProject) || demoProjects[0];
}

function getStep(workflow, id) {
  return workflow.steps?.find((step) => step.id === id) || {};
}

function moduleTone(state) {
  if (state === "done") return "ready";
  if (state === "progress" || state === "todo") return "pending";
  return "blocked";
}

function displayMoney(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) && numeric > 0 ? formatMoney(numeric) : "-";
}

function displayPercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0) return "-";
  return `${(numeric > 1 ? numeric : numeric * 100).toLocaleString("fr-FR", { maximumFractionDigits: 1 })} %`;
}

function buildPilotageAlerts(workflow) {
  const alerts = [];
  const configuration = getStep(workflow, "configuration");
  const dqe = getStep(workflow, "dqe");
  const budget = getStep(workflow, "budget");
  const scenarios = getStep(workflow, "scenarios");
  const procurement = workflow.procurement || {};
  const execution = workflow.execution || {};

  if (configuration.state !== "done") alerts.push("Configuration projet incomplete.");
  if (dqe.state !== "done") alerts.push("DQE absent ou non certifie.");
  if (dqe.state === "done" && budget.state !== "done") alerts.push("Budget non synchronise avec la base projet.");
  if (budget.state === "done" && scenarios.state !== "done") alerts.push("Aucun scénario actif pour arbitrage CAPEX.");
  if (procurement.status === "REVIEW_REQUIRED") alerts.push("Arbitrages achat generes mais validation humaine requise.");
  if (procurement.status === "REQUIRED") alerts.push("Approvisionnement à préparer depuis le scénario actif.");
  if (execution.status === "REQUIRED") alerts.push("Préparation chantier à lancer : actions chantier non encore générées.");
  if (execution.status === "AT_RISK") alerts.push("Préparation chantier à risque : lots critiques ou livraisons à surveiller.");
  if (!alerts.length) alerts.push("Projet prêt pour pilotage direction avec données disponibles.");
  return alerts;
}

function ModuleStatusCard({ title, step, message, actionLabel, actionRoute, detail }) {
  return (
    <article className={`workspace-module-card ${moduleTone(step?.state)}`}>
      <span>{title}</span>
      <strong>{step?.status || "Non disponible"}</strong>
      <p>{message}</p>
      <small>{detail || "-"}</small>
      {actionLabel && actionRoute ? <button type="button" onClick={() => navigateTo(actionRoute)}>{actionLabel}</button> : null}
    </article>
  );
}

function PilotageDecisionSummary({ project, workflow, primaryAction, kpis, state, workflowEvents = [] }) {
  const projectKey = getProjectWorkspaceKey(project);
  const currentSimulation = state.lastSimulationProject === projectKey ? state.lastSimulation : null;
  const dqeStep = getStep(workflow, "dqe");
  const budgetStep = getStep(workflow, "budget");
  const scenarioStep = getStep(workflow, "scenarios");
  const procurementStep = getStep(workflow, "procurement");
  const executionStep = getStep(workflow, "execution");
  const alerts = buildPilotageAlerts(workflow);
  const dqe = workflow.dqe || workflow.activeDqe || {};
  const scenario = workflow.scenario || {};
  const procurement = workflow.procurement || {};
  const execution = workflow.execution || {};
  const scenarioName = scenario.scenario_name || state.activeScenario || "-";

  const directionKpis = [
    ["Budget local", displayMoney(kpis.capex_local || kpis.budget_local)],
    ["Budget optimise", displayMoney(kpis.capex_optimise || kpis.budget_optimise)],
    ["Economie nette", displayMoney(kpis.economie_nette || currentSimulation?.kpi?.economie_nette)],
    ["Taux economie", displayPercent(kpis.taux_economie || kpis.roi || currentSimulation?.kpi?.taux_economie)],
    ["Trust score DQE", dqe.trust_score ? `${dqe.trust_score}/100` : "-"],
    ["DQE actif", dqe.normalized_lines_count ? dqe.normalized_lines_count.toLocaleString("fr-FR") : "-"],
    ["Scénario actif", scenarioName],
    ["Approvisionnement", procurement.status || "-"],
    ["Lots critiques", execution.critical_lots_count != null ? execution.critical_lots_count : "-"],
    ["Livraisons à risque", execution.deliveries_to_watch_count != null ? execution.deliveries_to_watch_count : "-"],
  ];

  return (
    <section className="workspace-summary pilotage-decision-summary" data-testid="pilotage-summary">
      <header className="workspace-summary-hero">
        <div>
          <p className="eyebrow">Synthese direction projet</p>
          <h1>{project.name || "Projet CAPEX"}</h1>
          <p>{project.city || "Ville a renseigner"}, {project.country || "Pays a renseigner"} · {project.client_name || "Client a renseigner"}</p>
        </div>
        <div className="workspace-summary-status">
          <span>{workflow.status || "Workflow"}</span>
          <strong>{workflow.label || "Etat projet"}</strong>
          <small>Confiance DQE : {dqe.trust_score ? `${dqe.trust_score}/100` : "-"}</small>
        </div>
      </header>

      <section className="workspace-next-action">
        <div>
          <span>Decision recommandee</span>
          <strong>{primaryAction.label}</strong>
          <p>{alerts[0]}</p>
        </div>
        <button type="button" className="primary-action" data-testid="pilotage-primary-action" onClick={() => navigateTo(primaryAction.route)}>
          {primaryAction.label}
        </button>
      </section>

      <ProjectWorkflowStepper workflow={workflow} onNavigate={navigateTo} onSetup={() => navigateTo("/app/projects")} />

      <section className="metric-grid pilotage-kpi-grid">
        {directionKpis.map(([label, value]) => (
          <article className="metric-card" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </article>
        ))}
      </section>

      <section className="workspace-module-grid">
        <ModuleStatusCard title="DQE" step={dqeStep} message={dqe.file_name ? `${dqe.file_name} · ${dqe.certification_status || dqe.status}` : "Controle de certification DQE requis."} detail={`Trust score : ${dqe.trust_score ? `${dqe.trust_score}/100` : "-"}`} actionLabel="Auditer le DQE projet" actionRoute="/app/dqe?tab=import" />
        <ModuleStatusCard title="Budget" step={budgetStep} message={workflow.budget?.message || "Etat de synchronisation budget projet."} detail={displayMoney(workflow.budget?.total_amount)} actionLabel="Synchroniser le budget CAPEX" actionRoute="/app/dqe?tab=sync" />
        <ModuleStatusCard title="Scénarios" step={scenarioStep} message={scenario.message || "Scénario CAPEX utilisé pour l’arbitrage."} detail={`${scenario.line_count || "-"} lignes simulées`} actionLabel="Simuler la stratégie CAPEX" actionRoute="/app/simulation" />
        <ModuleStatusCard title="Approvisionnement" step={procurementStep} message={procurement.message || "Etat des arbitrages achat."} detail={`${procurement.decisions_count || "-"} decisions achat`} actionLabel="Analyser les arbitrages achat" actionRoute="/app/procurement" />
        <ModuleStatusCard title="Préparation Chantier" step={executionStep} message={execution.message || "État des actions chantier."} detail={`${execution.actions_count || "-"} actions · ${execution.eta_to_watch_count || "-"} ETA`} actionLabel="Suivre la préparation des lots" actionRoute="/app/site?tab=planning" />
      </section>

      <section className="workspace-summary-footer">
        <div className="workspace-alerts" data-testid="pilotage-alerts">
          <span>Alertes projet</span>
          {alerts.map((alert) => <p key={alert}>{alert}</p>)}
        </div>
        <div>
          <span>Actions rapides</span>
          <ProjectQuickActions onNavigate={navigateTo} />
        </div>
      </section>

      <section className="workspace-alerts" data-testid="workflow-events">
        <span>Historique workflow</span>
        {workflowEvents.length ? workflowEvents.slice(0, 6).map((event) => (
          <p key={event.id || `${event.event_type}-${event.created_at}`}>
            <strong>{event.event_type}</strong> · {event.message || "Evenement workflow"} · {event.created_at ? new Date(event.created_at).toLocaleString("fr-FR") : "-"}
          </p>
        )) : <p>Aucun evenement workflow disponible pour le moment.</p>}
      </section>
    </section>
  );
}

function BudgetWorksView({ engine, kpis, heatmapRows, table, total }) {
  if (engine.error && !Object.keys(kpis || {}).length) return null;
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
      <AnalyticsCard title="Postes exposés" eyebrow="Lignes à surveiller">
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
  const [workflowEvents, setWorkflowEvents] = React.useState([]);
  const { state } = useAppStore();
  const project = getWorkspaceProject(state);
  const [isExportingReport, setIsExportingReport] = React.useState(false);
  const [exportReportError, setExportReportError] = React.useState("");
  const { workflow } = useWorkflow(project?.id || getProjectWorkspaceKey(project), project);
  const primaryAction = getProjectPrimaryAction({ ...project, backendWorkflow: workflow }, state);
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

  React.useEffect(() => {
    if (typeof window === "undefined") return;
    console.log("AnalyticsPage computed kpis", {
      dashboard,
      activeProject: state.activeProject,
      activeScenario: state.activeScenario,
      lastSimulationLines: state.lastSimulation?.kpi?.lignes_simulees,
      mainPayloadKpisNbLignes: mainPayload.kpis?.nb_lignes,
      capexPayloadKpisNbLignes: capexPayload.kpis?.nb_lignes,
      mergedKpisNbLignes: kpis.nb_lignes,
      tableLength: table.length,
      total,
      dashboardQuery: engine.dashboard?.queryKey,
      capexQuery: engine.capex?.queryKey,
      procurementQuery: engine.procurement?.queryKey,
    });
    try {
      const persisted = window.localStorage.getItem("sp2i:appState");
      const appState = persisted ? JSON.parse(persisted) : null;
      console.log("AnalyticsPage localStorage sp2i:appState", appState);
      const session = window.sessionStorage.getItem("sp2i:appState");
      console.log("AnalyticsPage sessionStorage sp2i:appState", session);
      try {
        console.log("AnalyticsPage REACT_QUERY_CACHE", window.__REACT_QUERY_CACHE || null);
      } catch (e) {
        // ignore
      }
    } catch (storageError) {
      console.warn("AnalyticsPage storage parse failed", storageError);
    }
  }, [dashboard, state.activeProject, state.activeScenario, state.lastSimulation, mainPayload.kpis, capexPayload.kpis, kpis.nb_lignes, table.length, total, engine.dashboard?.queryKey, engine.capex?.queryKey, engine.procurement?.queryKey]);

  React.useEffect(() => {
    let cancelled = false;
    listProjectWorkflowEvents(project?.id).then((payload) => {
      if (!cancelled && Array.isArray(payload?.events)) {
        setWorkflowEvents(payload.events);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [project?.id]);

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

  const handleExportReport = async () => {
    setExportReportError("");
    setIsExportingReport(true);
    try {
      await exportProjectReportPdf(project?.id, project?.name || "Projet");
    } catch (error) {
      setExportReportError(error?.message || "Export rapport indisponible pour le moment.");
    } finally {
      setIsExportingReport(false);
    }
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
        <button type="button" className="icon-text-button" onClick={handleExportReport} disabled={isExportingReport} data-testid="export-report-button">
          <Download size={15} />
          {isExportingReport ? "Export en cours..." : "Exporter rapport projet"}
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
      <PilotageDecisionSummary project={project} workflow={workflow} primaryAction={primaryAction} kpis={kpis} state={state} workflowEvents={workflowEvents} />
      {workflow.status !== "ACTIVE" ? (
        <WorkflowGuardEmptyState
          title="Donnees de pilotage partielles"
          message="Les donnees de pilotage sont partielles. Completez le workflow projet pour fiabiliser les indicateurs."
          actionLabel={primaryAction.label}
          actionRoute={primaryAction.route}
          severity="info"
          currentStep={workflow.label}
          requiredStep="Pilotage fiable"
          testId="workflow-empty-state"
        />
      ) : null}

      {renderDashboard()}
    </main>
  );
}
