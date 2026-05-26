import React from "react";
import { filterSpatialRows } from "../adapters/spatialAdapter";

export default function SpatialExecutionBoard({ summary, filters }) {
  const rows = React.useMemo(
    () => filterSpatialRows(summary?.execution_by_space || [], filters),
    [summary, filters]
  );

  if (!rows.length) return null;

  return (
    <section className="spatial-panel" data-testid="spatial-execution-board">
      <div className="spatial-panel-header">
        <div>
          <p className="eyebrow">Exécution spatiale</p>
          <h3>Actions par zone</h3>
        </div>
      </div>

      <div className="spatial-zone-list">
        {rows.slice(0, 8).map((row) => (
          <article key={`${row.batiment}-${row.niveau}-${row.piece}`} className="spatial-zone-row">
            <div>
              <strong>{[row.batiment, row.niveau, row.piece].filter(Boolean).join(" › ") || "Zone non renseignée"}</strong>
              <span>{row.actions_count} action(s), {row.open_count} ouverte(s)</span>
            </div>
            <div className="spatial-zone-status">
              <span>{row.done_count} terminée(s)</span>
              {row.at_risk_count || row.blocked_count ? <b>{row.at_risk_count + row.blocked_count} alerte(s)</b> : null}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
