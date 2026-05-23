import React from "react";
import { CheckCircle2, Circle, Clock3, LockKeyhole } from "lucide-react";

const stateIcon = {
  done: CheckCircle2,
  progress: Clock3,
  todo: Circle,
  blocking: Clock3,
  blocked: LockKeyhole,
};

export default function ProjectWorkflowStepper({ workflow, compact = false, onNavigate, onSetup }) {
  const steps = workflow?.steps || [];
  const doneCount = steps.filter((step) => step.state === "done").length;
  const nextStep = steps.find((step) => ["blocking", "todo", "progress"].includes(step.state)) || steps[steps.length - 1];
  const visibleSteps = steps.filter((step) => step.state !== "blocked").slice(-3);

  if (compact) {
    return (
      <section className="project-workflow-stepper compact" aria-label="Parcours projet" data-testid="project-workflow-stepper">
        <header className="project-workflow-compact-header">
          <div>
            <span>Parcours projet</span>
            <strong>{workflow?.completion || 0}%</strong>
          </div>
          <div>
            <span>Etapes terminees</span>
            <strong>{doneCount}/{steps.length || 0}</strong>
          </div>
        </header>
        <button
          type="button"
          className={`project-workflow-compact-action ${nextStep?.state || "todo"}`}
          onClick={() => {
            if (nextStep?.id === "configuration") onSetup?.();
            else onNavigate?.(nextStep?.route);
          }}
          disabled={!nextStep || nextStep.state === "blocked"}
        >
          <span>Prochaine action</span>
          <strong>{nextStep?.action || workflow?.primary_action?.label || "Ouvrir"}</strong>
          <small>{nextStep ? `${nextStep.label} · ${nextStep.status}` : workflow?.label}</small>
        </button>
        <div className="project-workflow-compact-statuses">
          {visibleSteps.map((step) => (
            <span key={step.id} className={step.state}>{step.label}: {step.status}</span>
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="project-workflow-stepper" aria-label="Parcours projet" data-testid="project-workflow-stepper">
      <header>
        <div>
          <span>Parcours projet</span>
          <strong>{workflow?.label || "Configuration requise"}</strong>
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
