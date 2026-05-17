import React from "react";
import { CheckCircle2, Database, RadioTower } from "lucide-react";
import { useSidebarStore } from "./sidebarStore";

export default function SidebarProjectStatus() {
  const { isCollapsed, activeProject, activeScenario, apiStatus, syncStatus } = useSidebarStore();

  if (isCollapsed) {
    return (
      <div className="sidebar-status-compact" title={`${activeProject} - ${activeScenario}`}>
        <span className="status-dot online" />
        <span className="status-dot sync" />
      </div>
    );
  }

  return (
    <div className="sidebar-project-status">
      <span>Projet actif</span>
      <strong>{activeProject}</strong>
      <small>Scenario : {activeScenario}</small>
      <div className="sidebar-status-grid">
        <span><RadioTower size={14} /> API {apiStatus}</span>
        <span><Database size={14} /> Sync {syncStatus}</span>
        <span><CheckCircle2 size={14} /> PostgreSQL</span>
      </div>
    </div>
  );
}
