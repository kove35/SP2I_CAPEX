import React from "react";

function money(value) {
  return Number(value || 0).toLocaleString("fr-FR", { maximumFractionDigits: 0 });
}

export default function SimulationTable({ rows = [] }) {
  return (
    <div className="analytics-table-wrap">
      <table className="analytics-table">
        <thead>
          <tr>
            <th>Produit</th>
            <th>Decision</th>
            <th>Economie</th>
            <th>Risque</th>
            <th>Container</th>
            <th>ETA</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id_ligne || row.designation}>
              <td>{row.designation}</td>
              <td>{row.decision_finale || row.decision_import}</td>
              <td>{money(row.economie_nette)} FCFA</td>
              <td>{row.risk_level || "A analyser"}</td>
              <td>{row.container_strategy || "-"}</td>
              <td>{row.lead_time_total || row.lead_time_days || 0} j</td>
            </tr>
          ))}
          {!rows.length ? (
            <tr>
              <td colSpan="6">Aucune simulation chargee.</td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}
