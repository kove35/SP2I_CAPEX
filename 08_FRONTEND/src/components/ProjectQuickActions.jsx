import React from "react";
import { sidebarQuickActions } from "../navigation/sidebarConfig";
import { useAppStore } from "../store/appStore.jsx";

export default function ProjectQuickActions({ onNavigate, disabled = false }) {
  const { state } = useAppStore();
  const hasProject = Boolean(state.activeProject);
  const isDisabled = disabled || !hasProject;

  const handleClick = (path) => {
    if (!hasProject) {
      onNavigate?.("/app/projects");
      return;
    }
    onNavigate?.(path);
  };

  return (
    <div className="project-quick-actions" aria-label="Actions du projet actif">
      {sidebarQuickActions.map((action) => {
        const Icon = action.icon;
        return (
          <button
            key={action.label}
            type="button"
            className="project-action-button"
            onClick={() => handleClick(action.path)}
            disabled={isDisabled}
            title={hasProject ? action.label : "Selectionner un projet"}
          >
            <Icon size={16} />
            <span>{action.label}</span>
          </button>
        );
      })}
    </div>
  );
}
