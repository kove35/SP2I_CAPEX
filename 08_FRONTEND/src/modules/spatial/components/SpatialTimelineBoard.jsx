import React from "react";
import { filterSpatialRows } from "../adapters/spatialAdapter";

const STEPS = [
  { key: "eta_date", label: "ETA" },
  { key: "delivery_date", label: "Livraison" },
  { key: "installation_date", label: "Pose" },
  { key: "validation_date", label: "Validation" },
];

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("fr-FR", { day: "2-digit", month: "short" });
}

export default function SpatialTimelineBoard({ summary, filters }) {
  const rows = React.useMemo(
    () => filterSpatialRows(summary?.timeline || [], filters),
    [summary, filters]
  );

  if (!rows.length) return null;

  return (
    <section className="spatial-panel spatial-timeline-board" data-testid="spatial-timeline-board">
      <div className="spatial-panel-header">
        <div>
          <p className="eyebrow">Timeline spatiale</p>
          <h3>ETA, livraison et pose par zone</h3>
        </div>
        <span className="spatial-mode-badge">{rows.length} jalon(s)</span>
      </div>

      <div className="spatial-timeline-list">
        {rows.slice(0, 8).map((row) => (
          <article key={`${row.action_id || row.zone}-${row.action_type}-${row.delivery_date}`} className={`spatial-timeline-row ${row.is_critical ? "critical" : ""}`}>
            <div className="spatial-timeline-meta">
              <strong>{row.zone || "Zone non renseignée"}</strong>
              <span>{row.lot || row.action_type || "Coordination chantier"}</span>
              <em>{row.message || "Jalon chantier à suivre."}</em>
            </div>
            <div className="spatial-timeline-steps">
              {STEPS.map((step) => (
                <span key={step.key}>
                  <small>{step.label}</small>
                  <b>{formatDate(row[step.key])}</b>
                </span>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
