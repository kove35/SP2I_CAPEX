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

  return (
    <section className={`project-workflow-stepper ${compact ? "compact" : ""}`} aria-label="Parcours projet">
      {!compact ? (
        <header>
          <div>
            <span>Parcours projet</span>
            <strong>{workflow?.label || "Configuration requise"}</strong>
          </div>
          <b>{workflow?.completion || 0}%</b>
        </header>
      ) : null}
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
              {!compact ? <small>{step.status}</small> : null}
            </button>
          );
        })}
      </div>
    </section>
  );
}
