import React from "react";
import { HardHat, Settings } from "lucide-react";
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
  const procurementReady = workflow.procurement?.is_ready || workflow.steps?.find((step) => step.id === "procurement")?.state === "done";
  const isDisabled = disabled || !hasProject;

  const actions = needsSetup
    ? [{ label: "Configurer le projet", path: "/app/projects", icon: Settings }]
    : sidebarQuickActions.map((action) => {
        const isSimulation = /tester|simuler/i.test(action.label);
        const isScenarioCreate = /nouveau|comparer/i.test(action.label);
        if (isSimulation && !budgetSynced) return { ...action, label: "Simuler stratégie CAPEX", disabled: true, title: "Synchroniser le budget avant de simuler la stratégie CAPEX" };
        if (isScenarioCreate && !budgetSynced) return { ...action, label: "Comparer stratégies CAPEX", disabled: true, title: "Synchroniser le budget avant de comparer les scénarios" };
        if (procurementReady && isSimulation) return { ...action, label: "Suivre les lots chantier", path: "/app/site?tab=planning", icon: HardHat };
        if (scenarioReady && isSimulation) return { ...action, label: "Analyser arbitrages achat", path: "/app/procurement" };
        if (isSimulation) return { ...action, label: "Simuler stratégie CAPEX" };
        if (isScenarioCreate) return { ...action, label: "Comparer stratégies CAPEX" };
        return action;
      });

  const handleClick = (action) => {
    if (!hasProject) {
      onNavigate?.("/app/projects");
      return;
    }

    if (/simuler|tester/i.test(action.label) && !hasActiveDqeVersion(state.activeProject)) {
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
            title={hasProject ? action.title || action.label : "Sélectionner un projet"}
          >
            <Icon size={16} />
            <span>{action.label}</span>
          </button>
        );
      })}
    </div>
  );
}
