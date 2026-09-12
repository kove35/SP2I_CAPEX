import React from "react";
import AnalyticsCard from "../../ui/AnalyticsCard";
import KpiCard from "../../ui/KpiCard";
import { useAppStore } from "../../store/appStore.jsx";
import { getScenarioContext, PROJECT_CONTEXT } from "../../utils/businessContext";
import {
  generateProjectExecutionActions,
  listProjectExecutionActions,
} from "../../services/projectService";
import { useWorkflow } from "../../hooks/useWorkflow";
const ActionsWorkflowBoard = React.lazy(() => import("./ActionsWorkflowBoard"));
import WorkflowGuardEmptyState from "../projects/WorkflowGuardEmptyState";
import SmartWorkflowActions from "../projects/SmartWorkflowActions";
import {
  SpatialDrilldownPanel,
  SpatialKpiBand,
  SpatialWorkflowPanel,
  useSpatialIntelligence,
} from "../spatial";
import { hasSpatialCapabilities } from "../spatial/utils/spatialFormatters";
import DataLineageCard, { buildLineageMetric, formatLineageSync } from "../../components/traceability/DataLineageCard";

const DQE_READY_STATUSES = ["SYNCED", "CERTIFIED", "CERTIFIED_WITH_WARNINGS"];

const EXECUTABLE_SCENARIO_STATUSES = ["READY", "SIMULATED", "VALIDATED"];

const scenarioStatusAliases = {
  DONE: "READY",
  READY: "READY",
  SIMULE: "SIMULATED",
  SIMULÉ: "SIMULATED",
  SIMULATED: "SIMULATED",
  VALIDATED: "VALIDATED",
  NOT_STARTED: "NOT_STARTED",
  DRAFT: "DRAFT",
  BLOCKED: "BLOCKED",
  FAILED: "FAILED",
  STALE: "STALE",
};

const siteActions = [
  {
    priority: "Haute",
    lot: "L01 - Gros œuvre et démolition",
    issue: "Arbitrage import/local à sécuriser",
    impact: "Chemin critique",
    owner: "Responsable chantier + achat",
    due: "Cette semaine",
    status: "À traiter",
  },
  {
    priority: "Moyenne",
    lot: "L07 - Électricité",
    issue: "Livraison fournisseur à confirmer",
    impact: "Risque planning moyen",
    owner: "Responsable achat",
    due: "7 jours",
    status: "À surveiller",
  },
  {
    priority: "Moyenne",
    lot: "Menuiserie aluminium",
    issue: "Stockage et séquence de pose à consolider",
    impact: "Risque de saturation site",
    owner: "Conducteur travaux",
    due: "Prochaine réunion chantier",
    status: "À planifier",
  },
];

const deliveries = [
  {
    delivery: "Tableaux et accessoires électriques",
    lot: "Électricité",
    supplier: "Fournisseur à confirmer",
    eta: "14 j",
    need: "10 j",
    gap: "+4 j",
    risk: "Moyen",
    action: "Confirmer fournisseur ou alternative locale",
  },
  {
    delivery: "Équipements plomberie",
    lot: "Plomberie",
    supplier: "Sourcing local/import",
    eta: "21 j",
    need: "18 j",
    gap: "+3 j",
    risk: "Moyen",
    action: "Sécuriser livraison et stockage",
  },
  {
    delivery: "Menuiseries aluminium",
    lot: "Menuiserie",
    supplier: "Fournisseur à valider",
    eta: "35 j",
    need: "25 j",
    gap: "+10 j",
    risk: "Élevé",
    action: "Arbitrage achat requis",
  },
];

const dependencies = [
  {
    upstream: "Gros œuvre",
    downstream: "Électricité",
    type: "Réservations / passages réseaux",
    need: "À confirmer",
    risk: "Moyen",
    action: "Valider planning d’intervention",
  },
  {
    upstream: "Menuiserie",
    downstream: "Finitions",
    type: "Fermeture bâtiment",
    need: "À confirmer",
    risk: "Élevé",
    action: "Sécuriser livraison menuiserie",
  },
  {
    upstream: "Plomberie",
    downstream: "Revêtements",
    type: "Essais réseaux avant fermeture",
    need: "À confirmer",
    risk: "Moyen",
    action: "Programmer contrôle technique",
  },
];

const planningRows = [
  {
    lot: "L01 - Gros œuvre",
    start: "-",
    required: "-",
    eta: "-",
    gap: "-",
    status: "À compléter",
  },
  {
    lot: "L07 - Électricité",
    start: "-",
    required: "10 j",
    eta: "14 j",
    gap: "+4 j",
    status: "À surveiller",
  },
  {
    lot: "Menuiserie aluminium",
    start: "-",
    required: "25 j",
    eta: "35 j",
    gap: "+10 j",
    status: "Critique",
  },
];

const criticalAlerts = [
  {
    lot: "Menuiserie aluminium",
    exposedBudget: "Élevé",
    drift: "Forte",
    action: "Remonter arbitrage achat + planning",
  },
  {
    lot: "Électricité",
    exposedBudget: "Moyen",
    drift: "Moyenne",
    action: "Confirmer délai fournisseur",
  },
  {
    lot: "Gros œuvre",
    exposedBudget: "Élevé",
    drift: "Faible",
    action: "Vérifier dépendances chantier",
  },
];

function readDqeVersions(projectId) {
  try {
    const stored = window.localStorage.getItem(
      `sp2i:dqeVersions:${projectId || PROJECT_CONTEXT.code}`
    );

    if (stored) {
      const parsed = JSON.parse(stored);
      return Array.isArray(parsed) ? parsed : [];
    }
  } catch {
    return [];
  }

  if ((projectId || PROJECT_CONTEXT.code) === PROJECT_CONTEXT.code) {
    return [
      {
        version_number: 1,
        status: "SYNCED",
        trust_score: 87,
        normalized_lines_count: 46,
        data_loss_count: 0,
        review_required_count: 0,
        is_active: true,
      },
    ];
  }

  return [];
}

function normalizeScenarioStatus(status) {
  const rawStatus = String(status || "").toUpperCase();
  return scenarioStatusAliases[rawStatus] || rawStatus;
}

function getExecutionContext(projectId, scenarioCode, lastSimulation, workflowScenario) {
  const activeDqe = readDqeVersions(projectId).find(
    (version) => version.is_active && DQE_READY_STATUSES.includes(version.status)
  );

  const scenario = getScenarioContext(scenarioCode);

  /**
   * IMPORTANT :
   * workflowScenario.status est la source prioritaire.
   * lastSimulation sert seulement de fallback local/demo.
   */
  const rawScenarioStatus =
    workflowScenario?.status ||
    workflowScenario?.state ||
    lastSimulation?.status ||
    lastSimulation?.scenario_status ||
    (lastSimulation ? "SIMULATED" : "NOT_STARTED");

  const scenarioStatus = normalizeScenarioStatus(rawScenarioStatus);

  const scenarioIsExecutable = EXECUTABLE_SCENARIO_STATUSES.includes(scenarioStatus);

  return {
    hasActiveDqe: Boolean(activeDqe),

    dqeLabel: activeDqe ? `DQE v${activeDqe.version_number}` : "Aucun DQE actif",

    dqeStatus:
      activeDqe?.status === "CERTIFIED"
        ? "Certifié"
        : activeDqe?.status === "CERTIFIED_WITH_WARNINGS"
        ? "Certifié avec points à vérifier"
        : activeDqe?.status === "SYNCED"
        ? "Synchronisé"
        : "Non disponible",

    trustScore: activeDqe?.trust_score,
    lines: activeDqe?.normalized_lines_count,
    dataLoss: activeDqe?.data_loss_count,
    reviewRequired: activeDqe?.review_required_count,

    scenarioLabel: scenario.label,

    // Statuts techniques
    scenarioStatus,
    scenarioIsExecutable,

    // Libellés UI
    scenarioTitleLabel: scenarioIsExecutable
      ? "Scénario actif"
      : "Stratégie sélectionnée",

    scenarioStatusLabel: scenarioIsExecutable ? "Simulé" : "À lancer",

    planningImpactLabel: scenarioIsExecutable
      ? "impact planning à consolider"
      : "impact planning non calculé",

    globalRisk: scenarioIsExecutable ? "Moyen" : "À évaluer",
  };
}

function navigate(path) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

function DataTable({ columns, rows, empty }) {
  return (
    <div className="data-table-wrap panel-scroll">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${row.lot || row.delivery || row.upstream || "row"}-${index}`}>
              {columns.map((column) => (
                <td key={column.key}>{row[column.key] || "-"}</td>
              ))}
            </tr>
          ))}

          {!rows.length ? (
            <tr>
              <td colSpan={columns.length}>{empty}</td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}

function PreparationAssistantHeader({ stage, title, message, metrics }) {
  return (
    <section className={`site-prep-assistant ${stage}`}>
      <div>
        <p className="eyebrow">Préparation Chantier</p>
        <h1>{title}</h1>
        <p>{message}</p>
      </div>
      <div className="site-prep-stage-metrics">
        {metrics.map((metric) => (
          <article key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
            <small>{metric.help}</small>
          </article>
        ))}
      </div>
    </section>
  );
}

function PreparationContextStrip({ context, activeScope }) {
  return (
    <section className={`site-prep-context ${context.hasActiveDqe ? "ready" : "blocked"}`}>
      <div>
        <span>Source</span>
        <strong>{context.dqeLabel}</strong>
        <small>
          {context.hasActiveDqe
            ? `${context.dqeStatus} - ${context.lines ?? "-"} lignes`
            : "DQE a valider"}
        </small>
      </div>
      <div>
        <span>Scenario</span>
        <strong>{context.scenarioLabel}</strong>
        <small>{context.scenarioStatusLabel} - {context.planningImpactLabel}</small>
      </div>
      <div>
        <span>Etape active</span>
        <strong>{activeScope}</strong>
        <small>{context.globalRisk}</small>
      </div>
    </section>
  );
}

function mapExecutionAction(action) {
  const priorityLabels = {
    LOW: "Basse",
    MEDIUM: "Moyenne",
    HIGH: "Haute",
    CRITICAL: "Critique",
  };

  const statusLabels = {
    TO_DO: "À traiter",
    IN_PROGRESS: "En cours",
    DONE: "Terminé",
    AT_RISK: "À risque",
    BLOCKED: "Bloqué",
    CANCELLED: "Annulé",
  };

  return {
    priority: priorityLabels[action.priority] || action.priority || "Moyenne",
    lot: action.lot || action.family || "-",
    issue: action.problem || action.title || "Action chantier à planifier",
    impact: action.impact || "-",
    owner: action.responsible_name || action.responsible_role || "Responsable chantier",
    due: action.due_date
      ? new Date(action.due_date).toLocaleDateString("fr-FR")
      : "À planifier",
    status: statusLabels[action.status] || action.status || "À traiter",
  };
}

export default function SiteExecutionPage() {
  const [tab, setTab] = React.useState(
    new URLSearchParams(window.location.search).get("tab") || "planning"
  );

  const [remoteActions, setRemoteActions] = React.useState([]);
  const [remoteActionsRaw, setRemoteActionsRaw] = React.useState([]);
  const { state } = useAppStore();

  const { workflow, workflowState } = useWorkflow(state.activeProjectDetails?.id || state.activeProject, state.activeProjectDetails);

  const setupDone =
    workflow.steps.find((step) => step.id === "configuration")?.state === "done";

  const procurementReady =
    workflow.procurement?.is_ready ||
    workflow.steps.find((step) => step.id === "procurement")?.state === "done";

  const executionStatus = workflow.execution?.status || "BLOCKED";

  const executionReady =
    workflow.execution?.is_ready ||
    workflow.steps.find((step) => step.id === "execution")?.state === "done";

  const executionSummary = workflow.execution || {};
  const spatial = useSpatialIntelligence({ workflow });
  const spatialSummary = spatial.data;
  const spatialEnabled = hasSpatialCapabilities(spatialSummary, workflow);
  const currentSimulation = state.lastSimulationProject === (state.activeProject || PROJECT_CONTEXT.code) ? state.lastSimulation : null;

  const context = React.useMemo(
    () =>
      getExecutionContext(
        state.activeProject || PROJECT_CONTEXT.code,
        state.activeScenario,
        currentSimulation,
        workflow.scenario
      ),
    [state.activeProject, state.activeScenario, currentSimulation, workflow.scenario]
  );

  React.useEffect(() => {
    setTab(new URLSearchParams(window.location.search).get("tab") || "planning");
  }, [window.location.search]);

  React.useEffect(() => {
    let cancelled = false;

    listProjectExecutionActions(state.activeProject, workflow.scenario?.scenario_id).then(
      (payload) => {
        if (!cancelled && Array.isArray(payload?.actions)) {
          setRemoteActionsRaw(payload.actions);
          setRemoteActions(payload.actions.map(mapExecutionAction));
        }
      }
    );

    return () => {
      cancelled = true;
    };
  }, [state.activeProject, workflow.scenario?.scenario_id]);

  const handleGenerateExecutionActions = async () => {
    await generateProjectExecutionActions(
      state.activeProject,
      workflow.scenario?.scenario_id
    );

    const payload = await listProjectExecutionActions(
      state.activeProject,
      workflow.scenario?.scenario_id
    );

    if (Array.isArray(payload?.actions)) {
      setRemoteActions(payload.actions.map(mapExecutionAction));
    }
  };

  const storageUsed = 72;
  const storageRemaining = 100 - storageUsed;

  const displayedActions = remoteActions.length ? remoteActions : siteActions;

  const blockedLots =
    Number(executionSummary.critical_lots_count || 0) ||
    displayedActions.filter(
      (action) => action.priority === "Haute" || action.priority === "Critique"
    ).length;

  const criticalDeliveries = deliveries.filter(
    (item) => item.risk === "Élevé" || item.risk === "Moyen"
  ).length;

  const watchedEta = deliveries.filter((item) => String(item.gap).startsWith("+")).length;

  const syncState = workflowState || {};
  const factMetreRows = Number(syncState.counts?.fact_metre_rows ?? syncState.normalized_lines_count ?? 0);
  const syncDeltaRows = Math.abs(Number(syncState.sync_delta_rows || 0));
  const syncDeltaCapex = Math.abs(Number(syncState.sync_delta_capex || 0));
  const syncStatus = String(syncState.sync_status || "OUT_OF_SYNC").toUpperCase();
  const syncBadge = syncStatus === "SYNCED" && !syncDeltaRows && !syncDeltaCapex ? "Synchronisé" : "Désynchronisé";
  const syncTone = syncStatus === "SYNCED" && !syncDeltaRows && !syncDeltaCapex ? "success" : "warning";
  const lastFactMetreSync = formatLineageSync(syncState.last_fact_metre_sync || syncState.last_dqe_certification);
  const scenarioLineCount = Number(workflow.scenario?.line_count || currentSimulation?.kpi?.lignes_simulees || 0);
  const readyLots = displayedActions.filter((action) => action.status === "Terminé").length;
  const pendingActions = displayedActions.filter((action) => action.status === "À traiter" || action.status === "En cours").length;
  const lineageMetrics = [
    buildLineageMetric("DQE actif", context.lines ?? 0, context.dqeLabel),
    buildLineageMetric("FACT_METRE", factMetreRows, lastFactMetreSync),
    buildLineageMetric("Scénario actif", scenarioLineCount, context.scenarioLabel),
    buildLineageMetric("Lots prêts", readyLots, "Coordination prête"),
    buildLineageMetric("Livraisons critiques", criticalDeliveries, "ETA à suivre"),
    buildLineageMetric("Actions à traiter", pendingActions, "Opérations chantier"),
  ];

  const tabContent = {
    planning: {
      title: "Planning opérationnel",
      help: "Relier les livraisons attendues aux besoins chantier sans inventer de dates non certifiées.",
      columns: [
        { key: "lot", label: "Lot" },
        { key: "start", label: "Début prévu" },
        { key: "required", label: "Livraison requise" },
        { key: "eta", label: "ETA estimé" },
        { key: "gap", label: "Écart" },
        { key: "status", label: "Statut" },
      ],
      rows: planningRows,
      empty: "Aucune ligne planning disponible.",
    },

    dependencies: {
      title: "Dépendances chantier",
      help: "Identifier les liens entre lots pour éviter qu’un arbitrage achat ne bloque une intervention terrain.",
      columns: [
        { key: "upstream", label: "Lot amont" },
        { key: "downstream", label: "Lot dépendant" },
        { key: "type", label: "Type de dépendance" },
        { key: "need", label: "Date besoin" },
        { key: "risk", label: "Risque" },
        { key: "action", label: "Action" },
      ],
      rows: dependencies,
      empty: "Aucune dépendance critique identifiée.",
    },

    deliveries: {
      title: "Livraisons critiques",
      help: "Suivre les ETA qui peuvent créer un écart avec le besoin chantier.",
      columns: [
        { key: "delivery", label: "Livraison" },
        { key: "lot", label: "Lot" },
        { key: "supplier", label: "Fournisseur" },
        { key: "eta", label: "ETA" },
        { key: "need", label: "Besoin chantier" },
        { key: "gap", label: "Écart" },
        { key: "risk", label: "Risque" },
        { key: "action", label: "Action" },
      ],
      rows: deliveries,
      empty: "Aucune livraison critique identifiée.",
    },

    criticality: {
      title: "Alertes opérationnelles",
      help: "Les lots critiques combinent budget exposé, dérive possible et impact planning.",
      columns: [
        { key: "lot", label: "Lot" },
        { key: "exposedBudget", label: "Budget exposé" },
        { key: "drift", label: "Probabilité de dérive" },
        { key: "action", label: "Action chantier" },
      ],
      rows: criticalAlerts,
      empty: "Aucune alerte chantier critique identifiée.",
    },
  };

  const activeTab = tabContent[tab] || tabContent.planning;
  const generatedActionsCount =
    Number(executionSummary.actions_count || 0) || remoteActionsRaw.length || remoteActions.length;
  const hasGeneratedActions = generatedActionsCount > 0;
  const preparationStage =
    !setupDone
      ? "configuration"
      : !context.scenarioIsExecutable
      ? "simulation"
      : !procurementReady
      ? "procurement"
      : !executionReady && executionStatus === "REQUIRED" && !hasGeneratedActions
      ? "prepare"
      : "active";
  const activeScope =
    preparationStage === "configuration"
      ? "Configuration projet"
      : preparationStage === "simulation"
      ? "Simulation CAPEX"
      : preparationStage === "procurement"
      ? "Arbitrages achat"
      : preparationStage === "prepare"
      ? "Actions chantier"
      : "Coordination des lots";
  const stageCopy = {
    configuration: {
      title: "Configurer le projet avant de préparer le chantier",
      message: "La préparation chantier dépend du DQE, du scénario CAPEX et des arbitrages achat. A ce stade, aucun KPI chantier n'est utile.",
      metrics: [
        { label: "Maintenant", value: "Configurer", help: "Créer le socle projet" },
        { label: "Donnée chantier", value: "Non prête", help: "Masquée tant que le projet n'est pas prêt" },
      ],
    },
    simulation: {
      title: "Lancer la simulation avant toute préparation chantier",
      message: "Les ETA, dépendances et alertes restent masqués tant que l'impact planning du scénario n'a pas été calculé.",
      metrics: [
        { label: "Maintenant", value: "Simuler", help: "Calculer l'impact CAPEX et planning" },
        { label: "Scenario", value: context.scenarioStatusLabel, help: context.planningImpactLabel },
      ],
    },
    procurement: {
      title: "Valider les arbitrages achat avant de préparer les lots",
      message: "La page chantier attend les décisions procurement. Les tableaux logistiques ne s'affichent pas tant que les achats ne sont pas prêts.",
      metrics: [
        { label: "Maintenant", value: "Arbitrer", help: "Local, import, hybride ou escalade" },
        { label: "Approvisionnement", value: "En attente", help: "Préparation chantier bloquée" },
      ],
    },
    prepare: {
      title: "Générer les actions chantier par lot",
      message: "L'approvisionnement est prêt. La prochaine étape utile est de créer les actions opérationnelles et d'affecter les responsables.",
      metrics: [
        { label: "Maintenant", value: "Générer", help: "Actions chantier par lot" },
        { label: "ETA", value: "A confirmer", help: "Après génération des actions" },
      ],
    },
    active: {
      title: "Piloter uniquement les lots à préparer maintenant",
      message: "Les actions, ETA et dépendances sont disponibles. La page affiche les éléments utiles à la coordination opérationnelle actuelle.",
      metrics: [
        { label: "Lots prêts", value: readyLots, help: "Lots coordonnables" },
        { label: "Lots bloqués", value: blockedLots, help: "Points de blocage" },
        { label: "Livraisons critiques", value: criticalDeliveries, help: "ETA à surveiller" },
        { label: "Dépendances ouvertes", value: dependencies.length, help: "Liens actifs" },
        { label: "Retards ETA", value: watchedEta, help: "Déviation planning" },
        { label: "Actions à traiter", value: pendingActions, help: "Affectations à planifier" },
      ],
    },
  };
  const currentStage = stageCopy[preparationStage];

  if (preparationStage !== "active") {
    return (
      <main className="cockpit-page cockpit-page-fit site-prep-page">
        <PreparationAssistantHeader
          stage={preparationStage}
          title={currentStage.title}
          message={currentStage.message}
          metrics={currentStage.metrics}
        />

        <PreparationContextStrip context={context} activeScope={activeScope} />
        <DataLineageCard
          eyebrow="Qualité de synchronisation"
          title="TRAÇABILITÉ CHANTIER"
          badge={syncBadge}
          badgeTone={syncTone}
          metrics={lineageMetrics}
          testId="site-data-lineage-card"
        />

        {preparationStage === "configuration" ? (
          <WorkflowGuardEmptyState
            title="Configuration projet requise"
            message="Ce projet doit être configuré avant de poursuivre le workflow CAPEX."
            actionLabel="Configurer le projet"
            actionRoute="/app/projects"
            severity="blocking"
            currentStep={workflow.label}
            requiredStep="Configuration projet"
            testId="execution-empty-state"
          />
        ) : preparationStage === "simulation" ? (
          <WorkflowGuardEmptyState
            title="Simulation à lancer"
            message="Lancez une simulation pour calculer l'impact planning avant de préparer le chantier."
            actionLabel="Simuler la stratégie CAPEX"
            actionRoute="/app/simulation"
            currentStep={context.scenarioStatusLabel}
            requiredStep="Scénario exploitable"
            testId="execution-empty-state"
          />
        ) : preparationStage === "procurement" ? (
          <WorkflowGuardEmptyState
            title="Approvisionnement à préparer"
            message="Préparez les arbitrages achat avant de lancer la préparation chantier."
            actionLabel="Analyser les arbitrages achat"
            actionRoute="/app/procurement"
            currentStep={workflow.steps.find((step) => step.id === "procurement")?.status}
            requiredStep="Approvisionnement"
            testId="execution-empty-state"
          />
        ) : (
          <section className="site-prep-generate-step">
            <WorkflowGuardEmptyState
              title="Préparation chantier par lot"
              message="L'approvisionnement est prêt. Générez les actions par lot, affectez les responsables et confirmez les ETA avant le suivi opérationnel."
              actionLabel="Préparer les actions chantier par lot"
              actionRoute="/app/site?tab=planning"
              currentStep={workflow.steps.find((step) => step.id === "execution")?.status}
              requiredStep="Actions chantier"
              testId="execution-empty-state"
            />

            <button
              type="button"
              className="primary-action secondary-action"
              onClick={handleGenerateExecutionActions}
            >
              Générer actions chantier par lot
            </button>
          </section>
        )}
      </main>
    );
  }

  return (
    <main className="cockpit-page cockpit-page-fit">
      <section className="page-hero compact">
        <p className="eyebrow">Préparation Chantier</p>
        <h1>Readiness lots, ETA fournisseurs et dépendances chantier</h1>
        <p>
          Préparer les priorités chantier liées aux décisions CAPEX, aux livraisons,
          aux dépendances et aux risques de readiness.
        </p>
      </section>

      <DataLineageCard
        eyebrow="Qualité de synchronisation"
        title="TRAÇABILITÉ CHANTIER"
        badge={syncBadge}
        badgeTone={syncTone}
        metrics={lineageMetrics}
        testId="site-data-lineage-card"
      />

      <section className={`execution-context-strip ${context.hasActiveDqe ? "ready" : "blocked"}`}>
        <div>
          <strong>{context.dqeLabel}</strong>
          <span>
            {context.hasActiveDqe
              ? `${context.dqeStatus} · Trust score ${context.trustScore ?? "-"}/100 · ${
                  context.lines ?? "-"
                } lignes`
              : "Importez et validez un DQE avant de préparer le chantier."}
          </span>
        </div>

        <div>
          <strong>
            {context.scenarioTitleLabel} : {context.scenarioLabel}
          </strong>
          <span>
            {context.scenarioStatusLabel} · {context.planningImpactLabel}
          </span>
        </div>

        <div>
          <strong>Gouvernance</strong>
          <span>
            {context.hasActiveDqe
              ? `${context.dataLoss ?? 0} perte stricte · ${
                  context.reviewRequired ?? 0
                } validation bloquante`
              : "Validation requise"}
          </span>
        </div>

        <div>
          <strong>Risque global</strong>
          <span>{context.globalRisk}</span>
        </div>
      </section>

      <SmartWorkflowActions
        workflow={workflow}
        module="execution"
        simulation={currentSimulation}
        execution={{ ...executionSummary, blockedLots, critical_lots_count: blockedLots, eta_to_watch_count: watchedEta }}
        onNavigate={navigate}
      />

      {spatialEnabled ? (
        <>
          <SpatialDrilldownPanel
            summary={spatialSummary}
            filters={spatial.filters}
            onFilterChange={spatial.setSpatialFilter}
            onReset={spatial.resetSpatialFilters}
          />
          <SpatialKpiBand summary={spatialSummary} />
        </>
      ) : null}

      {!setupDone ? (
        <WorkflowGuardEmptyState
          title="Configuration projet requise"
          message="Ce projet doit être configuré avant de poursuivre le workflow CAPEX."
          actionLabel="Configurer le projet"
          actionRoute="/app/projects"
          severity="blocking"
          currentStep={workflow.label}
          requiredStep="Configuration projet"
          testId="execution-empty-state"
        />
      ) : !context.scenarioIsExecutable ? (
        <WorkflowGuardEmptyState
          title="Simulation à lancer"
          message="Lancez une simulation pour calculer l’impact planning avant de préparer le chantier."
          actionLabel="Simuler la stratégie CAPEX"
          actionRoute="/app/simulation"
          currentStep={context.scenarioStatusLabel}
          requiredStep="Scénario exploitable"
          testId="execution-empty-state"
        />
      ) : !procurementReady ? (
        <WorkflowGuardEmptyState
          title="Approvisionnement à préparer"
          message="Préparez les arbitrages achat avant de lancer la préparation chantier."
          actionLabel="Analyser les arbitrages achat"
          actionRoute="/app/procurement"
          currentStep={workflow.steps.find((step) => step.id === "procurement")?.status}
          requiredStep="Approvisionnement"
          testId="execution-empty-state"
        />
      ) : !executionReady && executionStatus === "REQUIRED" ? (
        <div>
          <WorkflowGuardEmptyState
            title="Préparation chantier par lot"
            message="L’approvisionnement est prêt. Générez les actions par lot, affectez les responsables et confirmez les ETA avant le suivi opérationnel."
            actionLabel="Préparer les actions chantier par lot"
            actionRoute="/app/site?tab=planning"
            currentStep={workflow.steps.find((step) => step.id === "execution")?.status}
            requiredStep="Actions chantier"
            testId="execution-empty-state"
          />

          <button
            type="button"
            className="primary-action secondary-action"
            onClick={handleGenerateExecutionActions}
          >
            Générer actions chantier par lot
          </button>
        </div>
      ) : null}

      {setupDone && !context.hasActiveDqe ? (
        <div className="app-warning">
          Aucun DQE actif. Importez et validez un DQE avant de préparer le chantier.
          <button
            type="button"
            className="link-button"
            onClick={() => navigate("/app/dqe?tab=import")}
          >
            Importer un DQE
          </button>
        </div>
      ) : null}

      {setupDone && !context.scenarioIsExecutable ? (
        <div className="app-warning">
          La stratégie est sélectionnée, mais la simulation doit être lancée avant
          de préparer le chantier.
          <button
            type="button"
            className="link-button"
            onClick={() => navigate("/app/simulation")}
          >
            Simuler la stratégie CAPEX
          </button>
        </div>
      ) : null}

      <div className="tab-row">
        <button
          data-testid="execution-tab-workflow"
          className={tab === "workflow" ? "active" : ""}
          onClick={() => setTab("workflow")}
          type="button"
        >
          Workflow actions
        </button>

        {spatialEnabled ? (
          <button
            className={tab === "spatial" ? "active" : ""}
            onClick={() => setTab("spatial")}
            type="button"
            data-testid="execution-tab-spatial"
          >
            Spatial
          </button>
        ) : null}

        <button
          className={tab === "planning" ? "active" : ""}
          onClick={() => setTab("planning")}
          type="button"
        >
          Planning
        </button>

        <button
          className={tab === "dependencies" ? "active" : ""}
          onClick={() => setTab("dependencies")}
          type="button"
        >
          Dépendances
        </button>

        <button
          className={tab === "deliveries" ? "active" : ""}
          onClick={() => setTab("deliveries")}
          type="button"
        >
          Livraisons
        </button>

        <button
          className={tab === "criticality" ? "active" : ""}
          onClick={() => setTab("criticality")}
          type="button"
        >
          Alertes critiques
        </button>
      </div>

      {tab === "workflow" && (
        <section className="execution-workflow-section">
          <AnalyticsCard title="Workflow des actions chantier" eyebrow="Kanban opérationnel">
            <React.Suspense fallback={<div className="live-refresh">Chargement du workflow...</div>}>
              <ActionsWorkflowBoard
              projectId={state.activeProject}
              actions={remoteActionsRaw}
              onRefresh={() => {
                listProjectExecutionActions(state.activeProject, workflow.scenario?.scenario_id).then(
                  (payload) => {
                    if (Array.isArray(payload?.actions)) {
                      setRemoteActionsRaw(payload.actions);
                      setRemoteActions(payload.actions.map(mapExecutionAction));
                    }
                  }
                );
              }}
                loading={false}
              />
            </React.Suspense>
          </AnalyticsCard>
        </section>
      )}

      {tab === "spatial" && spatialEnabled ? (
        <SpatialWorkflowPanel summary={spatialSummary} filters={spatial.filters} />
      ) : null}

      <section className="metric-grid">
        <KpiCard label="Lots critiques" value={blockedLots} tone="warning" />
        <KpiCard
          label="Livraisons à risque"
          value={Number(executionSummary.deliveries_to_watch_count || 0) || criticalDeliveries}
          tone="warning"
        />
        <KpiCard label="Stockage utilisé" value={`${storageUsed}%`} />
        <KpiCard
          label="ETA à surveiller"
          value={Number(executionSummary.eta_to_watch_count || 0) || watchedEta}
        />
        <KpiCard label="Budget exposé" value="À consolider" />
        <KpiCard
          label="Actions requises"
          value={Number(executionSummary.actions_count || 0) || displayedActions.length}
          tone="warning"
        />
      </section>

      {tab !== "workflow" && tab !== "spatial" && (
        <>
      <section className="procurement-scope-note" data-testid="execution-actions-summary">
        <span>
          Actions chantier :{" "}
          {Number(executionSummary.actions_count || displayedActions.length || 0).toLocaleString(
            "fr-FR"
          )}
        </span>
        <span>
          Ouvertes : {Number(executionSummary.open_count || 0).toLocaleString("fr-FR")}
        </span>
        <span>
          Terminées : {Number(executionSummary.done_count || 0).toLocaleString("fr-FR")}
        </span>
        <span>
          À risque : {Number(executionSummary.at_risk_count || 0).toLocaleString("fr-FR")}
        </span>
        <span>
          Bloquées : {Number(executionSummary.blocked_count || 0).toLocaleString("fr-FR")}
        </span>
        <span>Source : {executionSummary.source || "données prévisionnelles"}</span>
      </section>

      <section className="execution-operational-grid">
        <AnalyticsCard title="Actions chantier prioritaires" eyebrow="Priorités opérationnelles">
          <DataTable
            columns={[
              { key: "priority", label: "Priorité" },
              { key: "lot", label: "Lot" },
              { key: "issue", label: "Problème" },
              { key: "impact", label: "Impact chantier" },
              { key: "owner", label: "Responsable" },
              { key: "due", label: "Échéance" },
              { key: "status", label: "Statut" },
            ]}
            rows={displayedActions}
            empty="Aucune action chantier critique identifiée pour le moment."
          />
        </AnalyticsCard>

        <AnalyticsCard title="Stockage site" eyebrow="Capacité chantier">
          <div className="execution-storage-card">
            <strong>{storageUsed}% utilisé</strong>
            <div className="procurement-progress">
              <i style={{ width: `${storageUsed}%` }} />
            </div>

            <ul className="signal-list">
              <li>Seuil de surveillance : 70%.</li>
              <li>Seuil critique : 80%.</li>
              <li>Capacité restante : {storageRemaining}%.</li>
              <li>Risque : moyen.</li>
              <li>
                Action : prioriser les livraisons par lot et éviter les arrivées simultanées.
              </li>
            </ul>
          </div>
        </AnalyticsCard>
      </section>

      <section className="cockpit-split">
        <AnalyticsCard title={activeTab.title} eyebrow="Suivi opérationnel">
          <p className="execution-help">{activeTab.help}</p>
          <DataTable columns={activeTab.columns} rows={activeTab.rows} empty={activeTab.empty} />
        </AnalyticsCard>

        <aside className="context-panel">
          <AnalyticsCard title="Impact approvisionnement" eyebrow="Lien achat / chantier">
            <ul className="signal-list">
              <li>Source approvisionnement : scénario {context.scenarioLabel}.</li>
              <li>Lignes import : à consolider depuis le workbench achat.</li>
              <li>Lignes hybrides : à arbitrer avec le responsable chantier.</li>
              <li>ETA moyen import : à confirmer par fournisseur.</li>
              <li>
                Risque logistique : moyen tant que les containers ne sont pas consolidés.
              </li>
            </ul>

            <button
              type="button"
              className="primary-action secondary-action"
              onClick={() => navigate("/app/procurement")}
            >
              Analyser les arbitrages achat
            </button>
          </AnalyticsCard>

          <AnalyticsCard title="Alertes chantier à remonter" eyebrow="Risque readiness">
            <ul className="signal-list">
              <li>
                Lot bloqué : L01 - Gros œuvre et démolition, cause arbitrage achat à
                sécuriser.
              </li>
              <li>Livraison critique : Menuiserie aluminium, écart ETA +10 jours.</li>
              <li>Stockage sous surveillance : 72% utilisé, seuil critique 80%.</li>
              <li>
                Action suivante : arbitrer les lots critiques en réunion chantier + achat.
              </li>
            </ul>
          </AnalyticsCard>
        </aside>
      </section>
      </>
      )}
    </main>
  );
}
