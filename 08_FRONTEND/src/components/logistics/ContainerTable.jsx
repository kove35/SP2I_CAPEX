import React from "react";

export default function ContainerTable({ rows = [] }) {
  return (
    <div className="analytics-table-wrap">
      <table className="analytics-table">
        <thead>
          <tr>
            <th>Produit</th>
            <th>Strategie</th>
            <th>Fill rate</th>
            <th>Cout shipment</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id_ligne || row.designation}>
              <td>{row.designation}</td>
              <td>{row.container_strategy}</td>
              <td>{Math.round(Number(row.fill_rate || 0) * 100)}%</td>
              <td>{Number(row.shipment_cost || 0).toLocaleString("fr-FR")} FCFA</td>
            </tr>
          ))}
          {!rows.length ? (
            <tr>
              <td colSpan="4">Aucun plan container disponible.</td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}
