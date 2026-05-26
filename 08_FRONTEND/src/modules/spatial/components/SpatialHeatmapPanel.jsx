import React from "react";
import { filterSpatialRows } from "../adapters/spatialAdapter";

function riskTone(score) {
  if (score >= 70) return "critical";
  if (score >= 35) return "warning";
  return "calm";
}

export default function SpatialHeatmapPanel({ summary, filters }) {
  const rows = React.useMemo(
    () => filterSpatialRows(summary?.risk_heatmap || [], filters),
    [summary, filters]
  );

  if (!rows.length) return null;

  return (
    <section className="spatial-panel" data-testid="spatial-heatmap-panel">
      <div className="spatial-panel-header">
        <div>
          <p className="eyebrow">Heatmap spatiale</p>
          <h3>Risques chantier</h3>
        </div>
      </div>
      <div className="spatial-heatmap-grid">
        {rows.slice(0, 12).map((row) => {
          const score = Number(row.risk_score || 0);
          return (
            <article key={`${row.batiment}-${row.niveau}-${row.piece}`} className={`spatial-heatmap-cell ${riskTone(score)}`}>
              <strong>{row.piece || row.niveau || row.batiment || "Zone"}</strong>
              <span>{[row.batiment, row.niveau].filter(Boolean).join(" · ")}</span>
              <b>{score}/100</b>
            </article>
          );
        })}
      </div>
    </section>
  );
}
