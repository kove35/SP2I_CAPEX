import React from "react";
import { filterSpatialRows } from "../adapters/spatialAdapter";

export default function SpatialStoragePanel({ summary, filters }) {
  const rows = React.useMemo(
    () => filterSpatialRows(summary?.storage || [], filters),
    [summary, filters]
  );

  if (!rows.length) return null;

  return (
    <section className="spatial-panel spatial-storage-panel" data-testid="spatial-storage-panel">
      <div className="spatial-panel-header">
        <div>
          <p className="eyebrow">Stockage chantier</p>
          <h3>Saturation par zone</h3>
        </div>
      </div>

      <div className="spatial-storage-list">
        {rows.slice(0, 6).map((row) => (
          <article key={row.zone} className={`spatial-storage-row ${row.saturation_level === "HIGH" ? "warning" : ""}`}>
            <div>
              <strong>{row.zone}</strong>
              <span>{row.message}</span>
            </div>
            <b>{row.saturation_level === "HIGH" ? "À surveiller" : "Stable"}</b>
          </article>
        ))}
      </div>
    </section>
  );
}
