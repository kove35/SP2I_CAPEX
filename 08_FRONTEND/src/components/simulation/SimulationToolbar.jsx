import React from "react";
import { getScenarioContext, SCENARIO_OPTIONS } from "../../utils/businessContext";

export default function SimulationToolbar({ running, onRun, scenarioName, onScenarioNameChange }) {
  const scenario = getScenarioContext(scenarioName);

  return (
    <section className="analytics-toolbar">
      <label className={`scenario-select-field ${scenario.tone}`}>
        Strategie
        <select value={scenario.code} onChange={(event) => onScenarioNameChange(event.target.value)}>
          {SCENARIO_OPTIONS.map((option) => (
            <option key={option.code} value={option.code}>{option.label}</option>
          ))}
        </select>
        <small>{scenario.description}</small>
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
