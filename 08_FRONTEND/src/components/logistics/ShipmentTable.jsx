import React from "react";

export default function ShipmentTable({ rows = [] }) {
  return (
    <div className="analytics-table-wrap">
      <table className="analytics-table">
        <thead>
          <tr>
            <th>Produit</th>
            <th>Strategie shipment</th>
            <th>ETA</th>
            <th>Risque livraison</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id_ligne || row.designation}>
              <td>{row.designation}</td>
              <td>{row.shipment_strategy}</td>
              <td>{row.lead_time_total} j</td>
              <td>{row.delivery_risk}</td>
            </tr>
          ))}
          {!rows.length ? (
            <tr>
              <td colSpan="4">Aucune expedition disponible.</td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}
