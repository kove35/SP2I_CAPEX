import React from "react";
import { getNextSpatialFocus } from "../adapters/spatialAdapter";

export default function SpatialRiskPropagationPanel({ summary }) {
  const focus = React.useMemo(() => getNextSpatialFocus(summary), [summary]);
  if (!focus) return null;

  return (
    <section className="spatial-panel spatial-risk-panel" data-testid="spatial-risk-propagation-panel">
      <div className="spatial-panel-header">
        <div>
          <p className="eyebrow">Propagation risques</p>
          <h3>Impact spatial probable</h3>
        </div>
      </div>
      <div className="spatial-risk-chain">
        <span>{focus.label}</span>
        <i>→</i>
        <span>Lots dépendants</span>
        <i>→</i>
        <span>Planning chantier</span>
      </div>
      <p>{focus.message}</p>
    </section>
  );
}
