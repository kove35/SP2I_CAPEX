import React from "react";

export default function SpatialPlanningBoard({ summary }) {
  const planning = summary?.planning || {};
  const recommendations = planning.recommendations || [];

  if (!recommendations.length) return null;

  return (
    <section className="spatial-panel spatial-planning-board" data-testid="spatial-planning-board">
      <div className="spatial-panel-header">
        <div>
          <p className="eyebrow">Planning intelligence</p>
          <h3>Recalage chantier recommandé</h3>
        </div>
      </div>

      <div className="spatial-planning-metrics">
        <span>
          <b>{planning.critical_path_count || 0}</b>
          chemin(s) critique(s)
        </span>
        <span>
          <b>{planning.dependency_edges_count || 0}</b>
          dépendance(s)
        </span>
      </div>

      <ul className="spatial-recommendation-list">
        {recommendations.slice(0, 4).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
