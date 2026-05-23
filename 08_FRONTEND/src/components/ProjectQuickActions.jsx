import React from "react";
import { Settings } from "lucide-react";
import { sidebarQuickActions } from "../navigation/sidebarConfig";
import { useAppStore } from "../store/appStore.jsx";
import { PROJECT_CONTEXT } from "../utils/businessContext";
import { getProjectWorkflow, isBudgetSynced } from "../services/projectService";

const DQE_READY_STATUSES = ["SYNCED", "CERTIFIED", "CERTIFIED_WITH_WARNINGS"];

function hasActiveDqeVersion(projectId) {
  try {
    const stored = window.localStorage.getItem(`sp2i:dqeVersions:${projectId || PROJECT_CONTEXT.code}`);
    if (stored) {
      const versions = JSON.parse(stored);
      return Array.isArray(versions) && versions.some((version) => version.is_active && DQE_READY_STATUSES.includes(version.status));
    }
  } catch {
    return false;
  }
  return (projectId || PROJECT_CONTEXT.code) === PROJECT_CONTEXT.code;
}

export default function ProjectQuickActions({ onNavigate, disabled = false }) {
  const { state } = useAppStore();
  const hasProject = Boolean(state.activeProject);
  const workflow = getProjectWorkflow(state.activeProjectDetails || { id: state.activeProject, workspace_key: state.activeProject }, state);
  const needsSetup = workflow.steps?.[0]?.state !== "done";
  const budgetSynced = isBudgetSynced(workflow);
  const scenarioReady = workflow.steps?.find((step) => step.id === "scenarios")?.state === "done";
  const isDisabled = disabled || !hasProject;

  const actions = needsSetup
    ? [{ label: "Configurer le projet", path: "/app/projects", icon: Settings }]
    : sidebarQuickActions.map((action) => {
        if (action.label === "Tester un scenario" && !budgetSynced) return { ...action, disabled: true, title: "Synchroniser le budget avant de tester un scenario" };
        if (action.label === "Nouveau scenario" && !budgetSynced) return { ...action, disabled: true, title: "Synchroniser le budget avant de creer un scenario" };
        if (scenarioReady && action.label === "Tester un scenario") return { ...action, label: "Approvisionnement", path: "/app/procurement" };
        return action;
      });

  const handleClick = (action) => {
    if (!hasProject) {
      onNavigate?.("/app/projects");
      return;
    }

    if (action.label === "Tester un scenario" && !hasActiveDqeVersion(state.activeProject)) {
      onNavigate?.("/app/dqe?tab=import&notice=dqe-required");
      return;
    }

    onNavigate?.(action.path);
  };

  return (
    <div className="project-quick-actions" aria-label="Actions du projet actif" data-testid="project-quick-actions">
      {actions.map((action) => {
        const Icon = action.icon;
        return (
          <button
            key={action.label}
            type="button"
            className="project-action-button"
            onClick={() => handleClick(action)}
            disabled={isDisabled || action.disabled}
            title={hasProject ? action.title || action.label : "Selectionner un projet"}
          >
            <Icon size={16} />
            <span>{action.label}</span>
          </button>
        );
      })}
    </div>
  );
}
