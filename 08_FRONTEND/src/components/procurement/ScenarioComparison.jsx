import React from "react";
import { getScenarioContext } from "../../utils/businessContext";

export default function ScenarioComparison({ rows = [] }) {
  return (
    <div className="analytics-table-wrap">
      <table className="analytics-table">
        <thead>
          <tr>
            <th>Strategie</th>
            <th>Budget optimise</th>
            <th>Economie</th>
            <th>Taux economie</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.scenario_id || row.scenario_nom}>
              <td>{getScenarioContext(row.scenario_nom).label}</td>
              <td>{Number(row.capex_optimise_total || 0).toLocaleString("fr-FR")}</td>
              <td>{Number(row.economie_totale || 0).toLocaleString("fr-FR")}</td>
              <td>{Number(row.taux_economie_global || 0).toLocaleString("fr-FR")} %</td>
            </tr>
          ))}
          {!rows.length ? (
            <tr>
              <td colSpan="4">Selectionne deux strategies historisees.</td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}
