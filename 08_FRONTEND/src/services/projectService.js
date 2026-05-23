import { getStoredSession } from "./authService";
import { request } from "./apiClient";

const LOCAL_PROJECTS_KEY = "sp2i:projects";

export const demoProjects = [
  {
    id: "demo-pnr-medical",
    workspace_key: "Pointe-Noire CAPEX",
    name: "Centre medical Pointe-Noire",
    client_name: "SP2I",
    city: "Pointe-Noire",
    country: "Congo-Brazzaville",
    currency: "FCFA",
    status: "ACTIVE",
    trust_score: 87,
    last_dqe: "DQE_PROJECT_SP2I.xlsx",
    budget: 1129667152,
    updated_at: "Derniere synchronisation governance",
    setup_status: "CONFIGURED",
    workflow_status: "ACTIVE",
    project_manager: "Direction SP2I",
    setup_completion_percent: 100,
  },
  {
    id: "demo-brazza-clinic",
    workspace_key: "demo-brazza-clinic",
    name: "Clinique pilote Brazzaville",
    client_name: "Investisseur prive",
    city: "Brazzaville",
    country: "Congo-Brazzaville",
    currency: "FCFA",
    status: "REVIEW",
    trust_score: 72,
    last_dqe: "DQE a importer",
    budget: 0,
    updated_at: "Workspace pret",
    setup_status: "CONFIG_REQUIRED",
    workflow_status: "CONFIG_REQUIRED",
    project_manager: "",
    setup_completion_percent: 55,
  },
];

export const projectStatusLabels = {
  DRAFT: "Brouillon",
  CONFIG_REQUIRED: "Configuration requise",
  CONFIGURED: "Projet configure",
  DQE_REQUIRED: "DQE a importer",
  DQE_UPLOADED: "DQE importe",
  DQE_ANALYZED: "DQE analyse",
  DQE_CERTIFIED: "DQE certifie",
  BUDGET_SYNC_REQUIRED: "Budget a synchroniser",
  BUDGET_SYNCED: "Budget synchronise",
  SCENARIO_REQUIRED: "Scenario a lancer",
  SCENARIO_READY: "Scenario disponible",
  PROCUREMENT_REVIEW_REQUIRED: "Arbitrages achat a valider",
  PROCUREMENT_READY: "Approvisionnement pret",
  EXECUTION_READY: "Execution prete",
  ACTIVE: "Actif",
  ARCHIVED: "Archive",
};

const DQE_READY_STATUSES = ["SYNCED", "CERTIFIED", "CERTIFIED_WITH_WARNINGS"];

function normalizeBackendWorkflow(backendWorkflow) {
  if (!backendWorkflow || !Array.isArray(backendWorkflow.steps)) return null;
  return {
    ...backendWorkflow,
    activeDqe: backendWorkflow.dqe ? { ...backendWorkflow.dqe } : null,
  };
}

export function getProjectWorkspaceKey(project) {
  return project?.workspace_key || project?.code || project?.id || project?.name || "Pointe-Noire CAPEX";
}

function readDqeVersions(project) {
  const key = getProjectWorkspaceKey(project);
  try {
    const stored = window.localStorage.getItem(`sp2i:dqeVersions:${key}`);
    if (stored) {
      const parsed = JSON.parse(stored);
      return Array.isArray(parsed) ? parsed : [];
    }
  } catch {
    return [];
  }
  if (key === "Pointe-Noire CAPEX") {
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
      synced_at: new Date().toISOString(),
    }];
  }
  return [];
}

function hasMinimumSetup(project = {}) {
  if (getProjectWorkspaceKey(project) === "Pointe-Noire CAPEX") return true;
  return Boolean(project.name && project.city && project.country && project.currency && project.client_name && project.project_manager);
}

export function getProjectWorkflow(project = {}, appState = {}) {
  const backendWorkflow = normalizeBackendWorkflow(project.backendWorkflow || project.backend_workflow);
  if (backendWorkflow) return backendWorkflow;

  const configured = project.setup_status === "CONFIGURED" || hasMinimumSetup(project);
  const versions = readDqeVersions(project);
  const activeDqe = versions.find((version) => version.is_active);
  const dqeReady = activeDqe && DQE_READY_STATUSES.includes(activeDqe.status);
  const budgetSynced = Boolean(project.budget || activeDqe?.synced_at || activeDqe?.status === "SYNCED");
  const scenarioReady = Boolean(appState.lastSimulation || project.scenario_ready || project.workflow_status === "SCENARIO_READY" || project.workflow_status === "ACTIVE");
  const procurementReady = Boolean(project.procurement_ready || project.workflow_status === "PROCUREMENT_READY" || project.workflow_status === "EXECUTION_READY" || project.workflow_status === "ACTIVE");
  const procurementReviewRequired = Boolean(project.procurement_review_required || project.workflow_status === "PROCUREMENT_REVIEW_REQUIRED");
  const procurementRequired = Boolean(scenarioReady && !procurementReady && !procurementReviewRequired);
  const executionStatusOverride = project.execution_status;
  const executionReady = Boolean(project.execution_ready || project.workflow_status === "EXECUTION_READY" || ["READY", "ACTIVE", "AT_RISK"].includes(executionStatusOverride));
  const executionRequired = Boolean(procurementReady && !executionReady);

  const steps = [
    {
      id: "configuration",
      label: "Configuration",
      status: configured ? "Termine" : "A completer",
      state: configured ? "done" : "blocking",
      action: configured ? "Modifier" : "Configurer",
      route: "/app/projects",
    },
    {
      id: "dqe",
      label: "DQE",
      status: dqeReady ? "Certifie" : activeDqe ? "En cours" : "A importer",
      state: !configured ? "blocked" : dqeReady ? "done" : activeDqe ? "progress" : "todo",
      action: activeDqe ? "Continuer" : "Importer",
      route: "/app/dqe?tab=import",
    },
    {
      id: "budget",
      label: "Budget",
      status: budgetSynced ? "Synchronise" : dqeReady ? "A synchroniser" : "Bloque",
      state: budgetSynced ? "done" : dqeReady ? "todo" : "blocked",
      action: "Synchroniser",
      route: "/app/dqe?tab=sync",
    },
    {
      id: "scenarios",
      label: "Scenarios",
      status: scenarioReady ? "Simule" : budgetSynced ? "Pret" : "Bloque",
      state: scenarioReady ? "done" : budgetSynced ? "todo" : "blocked",
      action: "Tester",
      route: "/app/simulation",
    },
    {
      id: "procurement",
      label: "Approvisionnement",
      status: procurementReady ? "Pret" : procurementReviewRequired ? "Validation requise" : scenarioReady ? "A preparer" : "Bloque",
      state: procurementReady ? "done" : procurementReviewRequired ? "progress" : procurementRequired ? "todo" : "blocked",
      action: "Preparer",
      route: "/app/procurement",
    },
    {
      id: "execution",
      label: "Execution",
      status: executionReady ? "Pret" : executionRequired ? "A preparer" : "Bloque",
      state: executionReady ? "done" : executionRequired ? "todo" : "blocked",
      action: "Suivre",
      route: "/app/site?tab=planning",
    },
  ];

  const status = !configured
    ? "CONFIG_REQUIRED"
    : !activeDqe
      ? "DQE_REQUIRED"
      : !dqeReady
        ? "DQE_UPLOADED"
        : !budgetSynced
          ? "BUDGET_SYNC_REQUIRED"
          : !scenarioReady
            ? "SCENARIO_REQUIRED"
            : procurementReviewRequired
              ? "PROCUREMENT_REVIEW_REQUIRED"
            : !procurementReady
              ? "SCENARIO_READY"
              : executionReady
                ? "EXECUTION_READY"
                : "PROCUREMENT_READY";

  return {
    status,
    label: projectStatusLabels[status],
    steps,
    completion: Math.round((steps.filter((step) => step.state === "done").length / steps.length) * 100),
    activeDqe,
    scenario: {
      status: scenarioReady ? "SIMULATED" : "NOT_STARTED",
      is_ready: scenarioReady,
      line_count: Number(appState.lastSimulation?.kpi?.nb_lignes || appState.lastSimulation?.lignes?.length || 0),
      source: "local_demo",
    },
    procurement: {
      status: procurementReady ? "READY" : procurementReviewRequired ? "REVIEW_REQUIRED" : procurementRequired ? "REQUIRED" : "BLOCKED",
      is_ready: procurementReady,
      decisions_count: Number(project.procurement_decisions_count || appState.lastSimulation?.lignes?.length || 0),
      import_lines_count: Number(project.procurement_import_lines_count || 0),
      local_lines_count: Number(project.procurement_local_lines_count || 0),
      hybrid_lines_count: Number(project.procurement_hybrid_lines_count || 0),
      validated_decisions_count: procurementReady ? Number(project.procurement_validated_decisions_count || project.procurement_decisions_count || 0) : 0,
      export_available: Boolean(project.procurement_export_available || procurementReady),
      source: "local_demo",
      message: procurementReady
        ? "Approvisionnement pret pour execution."
        : procurementReviewRequired
          ? "Arbitrages achat generes. Validation humaine requise avant execution."
          : procurementRequired
            ? "Le scenario est disponible. Preparez les arbitrages achat."
            : "Lancez un scenario avant de preparer l'approvisionnement.",
    },
    execution: {
      status: executionStatusOverride || (executionReady ? "READY" : executionRequired ? "REQUIRED" : "BLOCKED"),
      is_ready: executionReady,
      actions_count: Number(project.execution_actions_count || 0),
      critical_lots_count: Number(project.execution_critical_lots_count || 0),
      deliveries_to_watch_count: Number(project.execution_deliveries_to_watch_count || 0),
      eta_to_watch_count: Number(project.execution_eta_to_watch_count || 0),
      source: "local_demo",
      message: executionReady
        ? "Execution prete pour suivi chantier."
        : executionRequired
          ? "L'approvisionnement est pret. Preparez les actions chantier."
          : "Preparez l'approvisionnement avant de suivre l'execution chantier.",
    },
  };
}

export function getProjectPrimaryAction(project = {}, appState = {}) {
  const workflow = getProjectWorkflow(project, appState);
  if (workflow.primary_action) {
    if (workflow.execution?.status === "REQUIRED") return { label: "Preparer l'execution", route: "/app/site?tab=planning" };
    if (workflow.execution?.status === "READY") return { label: "Ouvrir Execution", route: "/app/site?tab=planning" };
    if (workflow.execution?.status === "ACTIVE") return { label: "Suivre l'execution", route: "/app/site?tab=planning" };
    if (workflow.execution?.status === "AT_RISK") return { label: "Suivre l'execution a risque", route: "/app/site?tab=planning" };
    return workflow.primary_action;
  }

  const nextStep = workflow.steps.find((step) => ["blocking", "todo", "progress"].includes(step.state)) || workflow.steps[workflow.steps.length - 1];
  if (nextStep.id === "configuration") return { label: "Configurer le projet", route: "/app/projects", mode: "setup" };
  if (nextStep.id === "dqe") return { label: workflow.activeDqe ? "Analyser le DQE" : "Importer le DQE", route: "/app/dqe?tab=import" };
  if (nextStep.id === "budget") return { label: "Synchroniser le budget", route: "/app/dqe?tab=sync" };
  if (nextStep.id === "scenarios") return { label: "Tester un scenario", route: "/app/simulation" };
  if (nextStep.id === "procurement" && workflow.procurement?.status === "REVIEW_REQUIRED") return { label: "Valider les arbitrages achat", route: "/app/procurement" };
  if (nextStep.id === "procurement") return { label: "Preparer l'approvisionnement", route: "/app/procurement" };
  if (nextStep.id === "execution" && workflow.execution?.status === "REQUIRED") return { label: "Preparer l'execution", route: "/app/site?tab=planning" };
  if (nextStep.id === "execution" && workflow.execution?.status === "ACTIVE") return { label: "Suivre l'execution", route: "/app/site?tab=planning" };
  if (nextStep.id === "execution" && workflow.execution?.status === "AT_RISK") return { label: "Suivre l'execution a risque", route: "/app/site?tab=planning" };
  if (nextStep.id === "execution") return { label: "Ouvrir Execution", route: "/app/site?tab=planning" };
  return { label: "Ouvrir le workspace", route: "/app" };
}

export function getBudgetStatus(workflow = {}) {
  const budget = workflow?.budget;
  if (budget && typeof budget === "object" && typeof budget.status === "string") {
    return budget.status;
  }

  const budgetStep = workflow?.steps?.find((step) => step.id === "budget");
  if (!budgetStep) return "SYNC_REQUIRED";
  if (budgetStep.state === "done") return "SYNCED";
  if (budgetStep.state === "todo") return "SYNC_REQUIRED";
  return "SYNC_REQUIRED";
}

export function isBudgetSynced(workflow = {}) {
  const budget = workflow?.budget;
  if (budget && typeof budget === "object") {
    if (budget.is_synced === true) return true;
    if (typeof budget.status === "string") return budget.status === "SYNCED";
  }
  return getBudgetStatus(workflow) === "SYNCED";
}

export function isBudgetSyncFailed(workflow = {}) {
  return getBudgetStatus(workflow) === "SYNC_FAILED";
}

export function isBudgetPartialSync(workflow = {}) {
  return getBudgetStatus(workflow) === "PARTIAL_SYNC";
}

function authHeaders() {
  const session = getStoredSession();
  if (!session?.access_token || session.token_type === "demo") return {};
  return { Authorization: `Bearer ${session.access_token}` };
}

function readLocalProjects() {
  try {
    const stored = window.localStorage.getItem(LOCAL_PROJECTS_KEY);
    if (!stored) return null;
    const parsed = JSON.parse(stored);
    return Array.isArray(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

export function saveLocalProjects(projects = []) {
  try {
    window.localStorage.setItem(LOCAL_PROJECTS_KEY, JSON.stringify(projects));
  } catch {
    // Local persistence is a progressive demo fallback only.
  }
}

export async function listProjects() {
  const session = getStoredSession();
  if (!session || session.token_type === "demo") return { projects: readLocalProjects() || demoProjects };
  try {
    const payload = await request({ url: "/projects", headers: authHeaders() });
    return { projects: payload.projects || readLocalProjects() || demoProjects };
  } catch {
    return { projects: readLocalProjects() || demoProjects };
  }
}

export async function createProject(payload) {
  const session = getStoredSession();
  if (!session || session.token_type === "demo") {
    const id = `local-${Date.now()}`;
    return {
      ...payload,
      id,
      workspace_key: id,
      trust_score: 60,
      last_dqe: "DQE a importer",
      budget: 0,
      setup_status: "CONFIG_REQUIRED",
      workflow_status: "CONFIG_REQUIRED",
      setup_completion_percent: 35,
    };
  }
  return request({ url: "/projects", method: "POST", data: payload, headers: authHeaders() });
}

function normalizeSetupPayload(payload = {}) {
  const numericFields = [
    "target_budget",
    "reference_exchange_rate",
    "default_transport_rate",
    "default_customs_rate",
    "default_insurance_rate",
    "default_import_margin",
    "minimum_saving_threshold",
    "site_storage_capacity",
  ];
  const normalized = { ...payload };
  numericFields.forEach((field) => {
    if (normalized[field] === "" || normalized[field] == null) {
      normalized[field] = null;
    } else {
      const value = Number(normalized[field]);
      normalized[field] = Number.isFinite(value) ? value : null;
    }
  });
  ["planned_start_date", "target_delivery_date"].forEach((field) => {
    if (normalized[field] === "") normalized[field] = null;
  });
  return normalized;
}

export async function updateProjectSetup(projectId, setupPayload, currentProjects = []) {
  const localProject = {
    ...setupPayload,
    setup_status: setupPayload.setup_status || "CONFIG_REQUIRED",
    setup_completion_percent: setupPayload.setup_completion_percent ?? 0,
  };
  const session = getStoredSession();
  const isLocalProject = String(projectId || "").startsWith("local-") || Number.isNaN(Number(projectId));

  if (!session || session.token_type === "demo" || isLocalProject) {
    const next = currentProjects.map((project) => String(project.id) === String(projectId) ? localProject : project);
    saveLocalProjects(next.length ? next : [localProject]);
    return localProject;
  }

  try {
    return await request({
      url: `/projects/${projectId}/setup`,
      method: "PATCH",
      data: normalizeSetupPayload(setupPayload),
      headers: authHeaders(),
    });
  } catch {
    const next = currentProjects.map((project) => String(project.id) === String(projectId) ? localProject : project);
    saveLocalProjects(next.length ? next : [localProject]);
    return localProject;
  }
}

export async function getBackendProjectWorkflow(projectId) {
  const session = getStoredSession();
  if (!session || session.token_type === "demo" || String(projectId || "").startsWith("local-") || Number.isNaN(Number(projectId))) {
    return null;
  }
  try {
    return await request({ url: `/projects/${projectId}/workflow`, headers: authHeaders() });
  } catch {
    return null;
  }
}
