import React from "react";
import { MapPin } from "lucide-react";
import { useSidebarStore } from "./sidebarStore";
import { useAppStore } from "../../../store/appStore.jsx";
import { getProjectContext } from "../../../utils/businessContext";

export default function SidebarProjectStatus({ onNavigate }) {
  const { isCollapsed, activeProject, projectMeta } = useSidebarStore();
  const { state } = useAppStore();
  const project = getProjectContext(state.activeProjectDetails || projectMeta || activeProject);

  if (isCollapsed) {
    return (
      <div className="sidebar-status-compact" title={`${project.label}`}>
        <span className="status-dot online" />
      </div>
    );
  }

  return (
    <div className="sidebar-project-status">
      <span className="sidebar-project-label">PROJET ACTIF</span>
      <strong>{project.label}</strong>
      <small><MapPin size={12} /> {project.location}</small>
      <div className="sidebar-project-meta">
        <span>Statut: Actif</span>
        <span>Confiance: 87/100</span>
      </div>
      <button type="button" className="sidebar-change-project" onClick={() => onNavigate?.("/app/projects")}>
        Changer de projet
      </button>
    </div>
  );
}
