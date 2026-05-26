import React from "react";

export default function SpatialCriticalPathPanel({ summary }) {
  const chains = summary?.risk_propagation || [];

  if (!chains.length) return null;

  return (
    <section className="spatial-panel spatial-critical-path-panel" data-testid="spatial-critical-path-panel">
      <div className="spatial-panel-header">
        <div>
          <p className="eyebrow">Propagation spatiale</p>
          <h3>Chemins d’impact chantier</h3>
        </div>
      </div>

      <div className="spatial-critical-path-list">
        {chains.slice(0, 4).map((chain, index) => (
          <article key={`${chain.source_event || "chain"}-${chain.zone}-${index}`}>
            <strong>{chain.zone}</strong>
            <div className="spatial-risk-chain">
              {(chain.chain || []).map((step, stepIndex) => (
                <React.Fragment key={`${step}-${stepIndex}`}>
                  {stepIndex > 0 ? <i>→</i> : null}
                  <span>{step}</span>
                </React.Fragment>
              ))}
            </div>
            <p>{chain.message}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
