import React from "react";
import { getScenarioContext, SCENARIO_OPTIONS } from "../../utils/businessContext";

export default function SimulationToolbar({ running, onRun, scenarioName, onScenarioNameChange, disabled = false, disabledReason = "" }) {
  const scenario = getScenarioContext(scenarioName);

  return (
    <section className="analytics-toolbar simulation-config-panel">
      <button className="simulation-run-button" type="button" onClick={onRun} disabled={running || disabled}>
        {running ? "Simulation en cours..." : "Lancer simulation"}
      </button>
      <label className={`scenario-select-field ${scenario.tone}`}>
        Stratégie active
        <select value={scenario.code} onChange={(event) => onScenarioNameChange(event.target.value)}>
          {SCENARIO_OPTIONS.map((option) => (
            <option key={option.code} value={option.code}>{option.label}</option>
          ))}
        </select>
        <small>{scenario.description}</small>
      </label>
      <div className="scenario-assumption-grid">
      <label>
        Transport
        <input value="12%" readOnly />
      </label>
      <label>
        Douane
        <input value="15%" readOnly />
      </label>
      <label>
        Trésorerie
        <input value="30/70" readOnly />
      </label>
      </div>
      <p className="scenario-config-help">Hypothèses CAPEX standard du projet. Ajustements avancés prévus pour les simulations logistique, chantier et procurement intelligence.</p>
      {disabledReason ? <p className="scenario-disabled-reason">{disabledReason}</p> : null}
    </section>
  );
}
