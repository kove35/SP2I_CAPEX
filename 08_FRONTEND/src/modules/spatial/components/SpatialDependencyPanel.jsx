import React from "react";

export default function SpatialDependencyPanel({ summary }) {
  const nodes = summary?.dependencies?.nodes || [];
  const edges = summary?.dependencies?.edges || [];

  if (!nodes.length && !edges.length) return null;

  return (
    <section className="spatial-panel spatial-dependency-panel" data-testid="spatial-dependency-panel">
      <div className="spatial-panel-header">
        <div>
          <p className="eyebrow">Dépendances spatiales</p>
          <h3>Lots liés par zone</h3>
        </div>
        <span className="spatial-mode-badge">{edges.length} lien(s)</span>
      </div>

      <div className="spatial-dependency-list">
        {edges.slice(0, 8).map((edge) => {
          const source = nodes.find((node) => node.id === edge.source);
          const target = nodes.find((node) => node.id === edge.target);
          return (
            <article key={`${edge.source}-${edge.target}`} className="spatial-dependency-row">
              <span>{source?.zone || "Zone"}</span>
              <strong>{source?.label || "Lot amont"}</strong>
              <i>→</i>
              <strong>{target?.label || "Lot aval"}</strong>
            </article>
          );
        })}
      </div>
    </section>
  );
}
