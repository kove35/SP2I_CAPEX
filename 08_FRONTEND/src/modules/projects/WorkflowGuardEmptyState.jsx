import React from "react";

export default function WorkflowGuardEmptyState({
  title,
  message,
  actionLabel,
  actionRoute,
  severity = "warning",
  currentStep,
  requiredStep,
  testId = "workflow-empty-state",
}) {
  const navigate = () => {
    if (!actionRoute) return;
    window.history.pushState({}, "", actionRoute);
    window.dispatchEvent(new PopStateEvent("popstate"));
  };

  return (
    <section className={`workflow-empty-state ${severity}`} data-testid={testId}>
      <div>
        <span>{requiredStep || "Parcours projet"}</span>
        <strong>{title}</strong>
        <p>{message}</p>
        {currentStep ? <small>Étape actuelle : {currentStep}</small> : null}
      </div>
      {actionLabel && actionRoute ? (
        <button type="button" data-testid="workflow-empty-action" onClick={navigate}>
          {actionLabel}
        </button>
      ) : null}
    </section>
  );
}
