import React from "react";
import { useAppStore } from "../store/appStore.jsx";

export default function ProjectSelector() {
  const { state } = useAppStore();

  return (
    <div className="project-selector">
      <span>Projet actif</span>
      <strong>{state.activeProject}</strong>
    </div>
  );
}
