import React from "react";
import { CheckCircle2, Circle, Clock3, LockKeyhole } from "lucide-react";

const stateIcon = {
  done: CheckCircle2,
  progress: Clock3,
  todo: Circle,
  blocking: Clock3,
  blocked: LockKeyhole,
};

function compactActionLabel(workflow, nextStep) {
  if (workflow?.next_action?.label) return workflow.next_action.label;
  if (nextStep?.id === "scenarios") return "Simuler la stratégie CAPEX";
  if (nextStep?.id === "procurement") {
    return workflow?.procurement?.status === "REVIEW_REQUIRED" ? "Valider les décisions import critiques" : "Analyser les arbitrages achat";
  }
  if (nextStep?.id !== "execution") return nextStep?.action || workflow?.primary_action?.label || "Piloter";
  const status = workflow?.execution?.status;
  if (status === "REQUIRED") return "Préparer les actions chantier";
  if (status === "ACTIVE") return "Piloter la préparation chantier";
  if (status === "AT_RISK") return "Traiter les lots chantier à risque";
  if (status === "READY") return "Suivre la préparation des lots";
  return workflow?.primary_action?.label || nextStep?.action || "Piloter";
}

function compactStepStatus(workflow, step) {
  if (step?.id !== "execution") return step?.status || "";
  const status = workflow?.execution?.status;
  if (status === "REQUIRED") return "à préparer";
  if (status === "READY") return "prête";
  if (status === "ACTIVE") return "active";
  if (status === "AT_RISK") return "à risque";
  return step?.status || "";
}

export default function ProjectWorkflowStepper({ workflow, compact = false, variant = "card", onNavigate, onSetup }) {
  const steps = workflow?.steps || [];
  const doneCount = steps.filter((step) => step.state === "done").length;
  const nextStep = workflow?.active_step || steps.find((step) => ["blocking", "todo", "progress"].includes(step.state)) || steps[steps.length - 1];
  const visibleSteps = steps.filter((step) => step.state !== "blocked").slice(-3);

  if (compact && variant === "inline") {
    return (
      <section className="project-workflow-inline" aria-label="Workflow projet" data-testid="project-workflow-stepper">
        <div>
          <span>Workflow projet</span>
          <strong>{visibleSteps.map((step) => `${step.label} ${compactStepStatus(workflow, step)}`).join(" · ") || workflow?.label}</strong>
        </div>
        <button
          type="button"
          onClick={() => {
            if (nextStep?.id === "configuration") onSetup?.();
            else onNavigate?.(nextStep?.route);
          }}
          disabled={!nextStep || nextStep.state === "blocked"}
        >
          <span>Prochaine action</span>
          {compactActionLabel(workflow, nextStep)}
        </button>
      </section>
    );
  }

  if (compact) {
    return (
      <section className="project-workflow-stepper compact" aria-label="Parcours projet" data-testid="project-workflow-stepper">
        <header className="project-workflow-compact-header">
          <div>
            <span>Parcours projet</span>
            <strong>{workflow?.global_state_label || workflow?.label || "Workflow"}</strong>
          </div>
          <div>
            <span>Étapes terminées</span>
            <strong>{doneCount}/{steps.length || 0}</strong>
          </div>
        </header>
        <button
          type="button"
          className={`project-workflow-compact-action ${nextStep?.state || "todo"}`}
          aria-label="Ouvrir l'etape active du workflow"
          onClick={() => {
            if (nextStep?.id === "configuration") onSetup?.();
            else onNavigate?.(nextStep?.route);
          }}
          disabled={!nextStep || nextStep.state === "blocked"}
        >
          <span>Prochaine action</span>
          <strong>{compactActionLabel(workflow, nextStep)}</strong>
          <small>{nextStep ? `${nextStep.label}: ${compactStepStatus(workflow, nextStep)}` : workflow?.label}</small>
        </button>
        <div className="project-workflow-compact-statuses">
          {visibleSteps.map((step) => (
            <span key={step.id} className={step.state}>{step.label}: {compactStepStatus(workflow, step)}</span>
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="project-workflow-stepper" aria-label="Parcours projet" data-testid="project-workflow-stepper">
      <header>
        <div>
          <span>Etat global workflow</span>
          <strong>{workflow?.global_state_label || workflow?.label || "Configuration requise"}</strong>
        </div>
        <b>{workflow?.completion || 0}%</b>
      </header>
      <div className="project-workflow-steps">
        {steps.map((step) => {
          const Icon = stateIcon[step.state] || Circle;
          const disabled = step.state === "blocked";
          return (
            <button
              key={step.id}
              type="button"
              className={`project-workflow-step ${step.state}`}
              disabled={disabled}
              onClick={() => {
                if (step.id === "configuration") onSetup?.();
                else onNavigate?.(step.route);
              }}
              title={disabled ? `${step.label} bloque` : `${step.action} - ${step.status}`}
            >
              <Icon size={15} />
              <span>{step.label}</span>
              <small>{step.status}</small>
            </button>
          );
        })}
      </div>
    </section>
  );
}
