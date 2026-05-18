import React from "react";

export default function SimulationToolbar({ running, onRun, scenarioName, onScenarioNameChange }) {
  return (
    <section className="analytics-toolbar">
      <label>
        Scenario
        <input
          value={scenarioName}
          onChange={(event) => onScenarioNameChange(event.target.value)}
          placeholder="Nom du scenario"
        />
      </label>
      <label>
        Transport
        <input value="12%" readOnly />
      </label>
      <label>
        Douane
        <input value="15%" readOnly />
      </label>
      <label>
        Tresorerie
        <input value="30/70" readOnly />
      </label>
      <button type="button" onClick={onRun} disabled={running}>
        {running ? "Simulation..." : "Lancer simulation"}
      </button>
    </section>
  );
}
