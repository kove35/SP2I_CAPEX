import React from "react";

const stepOrder = ["configuration", "dqe", "budget", "scenarios", "procurement", "execution"];

const stepLabels = {
  configuration: "Configuration",
  dqe: "DQE",
  budget: "Budget",
  scenarios: "Scenario",
  procurement: "Approvisionnement",
  execution: "Execution",
};

const currentModuleByPath = {
  dqe: "dqe",
  simulation: "scenarios",
  procurement: "procurement",
  site: "execution",
  analytics: "pilotage",
};

function normalizeStatus(workflow, step) {
  if (!step) return "";
  if (step.id === "configuration" && step.state === "done") return "terminee";
  if (step.id === "execution") {
    const status = workflow?.execution?.status;
    if (status === "REQUIRED") return "a preparer";
    if (status === "READY") return "prete";
    if (status === "ACTIVE") return "active";
    if (status === "AT_RISK") return "a risque";
  }
  return String(step.status || "").toLowerCase();
}

function nextWorkflowStep(workflow) {
  const steps = workflow?.steps || [];
  return steps.find((step) => ["blocking", "todo", "progress"].includes(step.state)) || steps[steps.length - 1];
}

function actionLabel(workflow, nextStep) {
  if (workflow?.primary_action?.label) return workflow.primary_action.label;
  if (nextStep?.id === "execution") {
    const status = workflow?.execution?.status;
    if (status === "REQUIRED") return "Preparer l'execution";
    if (status === "READY") return "Ouvrir Execution";
    if (status === "ACTIVE") return "Suivre l'execution";
    if (status === "AT_RISK") return "Suivre l'execution a risque";
  }
  if (nextStep?.id === "configuration") return "Configurer le projet";
  if (nextStep?.id === "dqe") return "Importer le DQE";
  if (nextStep?.id === "budget") return "Synchroniser le budget";
  if (nextStep?.id === "scenarios") return "Tester un scenario";
  if (nextStep?.id === "procurement") return workflow?.procurement?.status === "REVIEW_REQUIRED" ? "Valider les arbitrages achat" : "Preparer l'approvisionnement";
  return nextStep?.action || "Ouvrir";
}

function moduleFromPath(path = "") {
  const segment = String(path).replace(/^\/app\/?/, "").split(/[/?#]/)[0] || "";
  return currentModuleByPath[segment] || "";
}

export default function ProjectWorkflowBreadcrumb({ workflow, currentModule, showAction = true, onNavigate, onSetup }) {
  const steps = workflow?.steps || [];
  const current = currentModule || "";
  const nextStep = nextWorkflowStep(workflow);
  const items = stepOrder
    .map((id) => steps.find((step) => step.id === id))
    .filter(Boolean);
  const visibleMobile = items.filter((step) => step.state !== "done").slice(0, 2);
  const action = actionLabel(workflow, nextStep);

  const navigate = () => {
    if (nextStep?.id === "configuration") {
      onSetup?.();
      return;
    }
    onNavigate?.(nextStep?.route || workflow?.primary_action?.route || "/app");
  };

  return (
    <nav className="project-workflow-breadcrumb" aria-label="Workflow projet" data-testid="project-workflow-breadcrumb">
      <div className="workflow-breadcrumb-desktop">
        <span>Workflow projet</span>
        <ol>
          {items.map((step) => (
            <li key={step.id} className={`${step.state} ${current === step.id ? "current" : ""}`}>
              {stepLabels[step.id] || step.label} {normalizeStatus(workflow, step)}
            </li>
          ))}
        </ol>
      </div>
      <div className="workflow-breadcrumb-mobile">
        <span>Workflow</span>
        <strong>
          {visibleMobile.length
            ? visibleMobile.map((step) => `${stepLabels[step.id] || step.label} ${normalizeStatus(workflow, step)}`).join(" -> ")
            : `Prochaine etape : ${action}`}
        </strong>
      </div>
      {showAction ? (
        <button type="button" onClick={navigate} disabled={!nextStep || nextStep.state === "blocked"} data-testid="workflow-breadcrumb-action">
          <span>Prochaine action</span>
          {action}
        </button>
      ) : null}
    </nav>
  );
}

export { moduleFromPath };
