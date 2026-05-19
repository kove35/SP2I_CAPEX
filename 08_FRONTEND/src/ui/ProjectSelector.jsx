import React from "react";
import { Building2, MapPin, ShieldCheck } from "lucide-react";
import { useAppStore } from "../store/appStore.jsx";
import { getProjectContext, getScenarioContext } from "../utils/businessContext";

export default function ProjectSelector() {
  const { state } = useAppStore();
  const project = getProjectContext(state.activeProject);
  const scenario = getScenarioContext(state.activeScenario);

  return (
    <div className="project-selector decision-context">
      <div className="context-icon"><Building2 size={18} /></div>
      <div>
        <span>Projet immobilier</span>
        <strong>{project.label}</strong>
        <small><MapPin size={12} /> {project.location}</small>
      </div>
      <div className={`scenario-pill ${scenario.tone}`}>
        <ShieldCheck size={13} />
        <span>{scenario.label}</span>
      </div>
    </div>
  );
}
