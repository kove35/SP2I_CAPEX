import React from "react";
import CapexTimeline from "../../../components/charts/CapexTimeline";

export default function LivraisonTimeline({ timeline = [] }) {
  return (
    <article className="appro-panel">
      <header className="appro-panel-header">
        <div>
          <span>Timeline livraison</span>
          <strong>Commande → livraison → pose chantier</strong>
        </div>
      </header>
      <CapexTimeline data={timeline} />
    </article>
  );
}
