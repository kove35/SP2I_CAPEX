import React from "react";
import { CheckCircle2, Database, MapPin, RadioTower, ShieldCheck } from "lucide-react";
import { useSidebarStore } from "./sidebarStore";
import { getProjectContext, getScenarioContext } from "../../../utils/businessContext";

export default function SidebarProjectStatus() {
  const { isCollapsed, activeProject, activeScenario, apiStatus, syncStatus } = useSidebarStore();
  const project = getProjectContext(activeProject);
  const scenario = getScenarioContext(activeScenario);

  if (isCollapsed) {
    return (
      <div className="sidebar-status-compact" title={`${project.label} - ${scenario.label}`}>
        <span className="status-dot online" />
        <span className="status-dot sync" />
      </div>
    );
  }

  return (
    <div className="sidebar-project-status">
      <span>Projet actif</span>
      <strong>{project.label}</strong>
      <small><MapPin size={12} /> {project.location}</small>
      <div className={`sidebar-scenario-card ${scenario.tone}`}>
        <ShieldCheck size={14} />
        <div>
          <b>{scenario.label}</b>
          <small>{scenario.gain} · {scenario.risk}</small>
        </div>
      </div>
      <div className="sidebar-status-grid">
        <span><RadioTower size={14} /> API {apiStatus}</span>
        <span><Database size={14} /> Sync {syncStatus}</span>
        <span><CheckCircle2 size={14} /> PostgreSQL</span>
      </div>
    </div>
  );
}
