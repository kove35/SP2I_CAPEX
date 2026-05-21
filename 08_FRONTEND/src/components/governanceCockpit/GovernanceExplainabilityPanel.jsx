import React from "react";
import { AlertTriangle, ClipboardCheck, LockKeyhole, Route } from "lucide-react";

export default function GovernanceExplainabilityPanel({ reference }) {
  if (!reference) {
    return (
      <aside className="governance-panel explainability-panel">
        <header><span>Explainability</span><strong>Aucune reference selectionnee</strong></header>
      </aside>
    );
  }

  const cards = [
    { icon: LockKeyhole, title: "Pourquoi bloque", text: reference.decisionBlocker === "BLOCK_IMPORT" ? "Import bloque tant qu'une validation senior n'a pas confirme fournisseur, FOB et benchmark." : "La reference reste en revue car la gouvernance interdit une validation automatique.", tone: "critical" },
    { icon: Route, title: "Pourquoi escalation", text: reference.escalationLevel.replaceAll("_", " "), tone: reference.escalationLevel === "STANDARD_REVIEW" ? "medium" : "critical" },
    { icon: AlertTriangle, title: "Pourquoi risque", text: `${reference.confidenceLevel} confidence, drift ${reference.driftLevel}, validation technique ${reference.technicalValidation}.`, tone: "warning" },
    { icon: ClipboardCheck, title: "Prochaine action", text: "Valider fournisseur, benchmark, FOB et commentaire governance avant toute decision.", tone: "info" },
  ];

  return (
    <aside className="governance-panel explainability-panel">
      <header>
        <span>Explainability</span>
        <strong>{reference.referenceId}</strong>
      </header>
      <p className="explainability-summary">{reference.explanation}</p>
      <div className="explainability-cards">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <article className={`explainability-card ${card.tone}`} key={card.title}>
              <Icon size={17} />
              <div>
                <b>{card.title}</b>
                <small>{card.text}</small>
              </div>
            </article>
          );
        })}
      </div>
    </aside>
  );
}
