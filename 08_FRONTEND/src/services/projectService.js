import { getStoredSession } from "./authService";
import { request } from "./apiClient";

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
  PROCUREMENT_READY: "Approvisionnement pret",
  EXECUTION_READY: "Execution prete",
  ACTIVE: "Actif",
  ARCHIVED: "Archive",
};

const DQE_READY_STATUSES = ["SYNCED", "CERTIFIED", "CERTIFIED_WITH_WARNINGS"];

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
  const configured = project.setup_status === "CONFIGURED" || hasMinimumSetup(project);
  const versions = readDqeVersions(project);
  const activeDqe = versions.find((version) => version.is_active);
  const dqeReady = activeDqe && DQE_READY_STATUSES.includes(activeDqe.status);
  const budgetSynced = Boolean(project.budget || activeDqe?.synced_at || dqeReady);
  const scenarioReady = Boolean(appState.lastSimulation || project.scenario_ready || project.workflow_status === "SCENARIO_READY" || project.workflow_status === "ACTIVE");
  const procurementReady = Boolean(project.procurement_ready || scenarioReady);
  const executionReady = Boolean(project.execution_ready || procurementReady);

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
      status: procurementReady ? "Pret" : scenarioReady ? "A preparer" : "Bloque",
      state: procurementReady ? "done" : scenarioReady ? "todo" : "blocked",
      action: "Preparer",
      route: "/app/procurement",
    },
    {
      id: "execution",
      label: "Execution",
      status: executionReady ? "Pret" : procurementReady ? "En attente" : "Bloque",
      state: executionReady ? "done" : procurementReady ? "todo" : "blocked",
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
            : !procurementReady
              ? "SCENARIO_READY"
              : "ACTIVE";

  return {
    status,
    label: projectStatusLabels[status],
    steps,
    completion: Math.round((steps.filter((step) => step.state === "done").length / steps.length) * 100),
    activeDqe,
  };
}

export function getProjectPrimaryAction(project = {}, appState = {}) {
  const workflow = getProjectWorkflow(project, appState);
  const nextStep = workflow.steps.find((step) => ["blocking", "todo", "progress"].includes(step.state)) || workflow.steps[workflow.steps.length - 1];
  if (nextStep.id === "configuration") return { label: "Configurer le projet", route: "/app/projects", mode: "setup" };
  if (nextStep.id === "dqe") return { label: workflow.activeDqe ? "Analyser le DQE" : "Importer le DQE", route: "/app/dqe?tab=import" };
  if (nextStep.id === "budget") return { label: "Synchroniser le budget", route: "/app/dqe?tab=sync" };
  if (nextStep.id === "scenarios") return { label: "Tester un scenario", route: "/app/simulation" };
  if (nextStep.id === "procurement") return { label: "Preparer l'approvisionnement", route: "/app/procurement" };
  return { label: "Ouvrir le workspace", route: "/app" };
}

function authHeaders() {
  const session = getStoredSession();
  if (!session?.access_token || session.token_type === "demo") return {};
  return { Authorization: `Bearer ${session.access_token}` };
}

export async function listProjects() {
  const session = getStoredSession();
  if (!session || session.token_type === "demo") return { projects: demoProjects };
  try {
    return await request({ url: "/projects", headers: authHeaders() });
  } catch {
    return { projects: demoProjects };
  }
}

export async function createProject(payload) {
  const session = getStoredSession();
  if (!session || session.token_type === "demo") {
    return {
      ...payload,
      id: `local-${Date.now()}`,
      workspace_key: `local-${Date.now()}`,
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
