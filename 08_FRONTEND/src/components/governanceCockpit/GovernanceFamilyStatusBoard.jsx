import React from "react";

function statusTone(status) {
  if (status === "BLOCKED") return "critical";
  if (status === "HIGH_RISK") return "risk";
  if (status === "CONDITIONALLY_READY") return "watch";
  return "stable";
}

export default function GovernanceFamilyStatusBoard({ families = [], onSelect }) {
  return (
    <section className="family-status-board" aria-label="Statut governance par famille">
      {families.map((family) => (
        <button className={`family-status-card ${statusTone(family.familyStatus)}`} type="button" key={family.family} onClick={() => onSelect?.(family.family)}>
          <span>{family.family}</span>
          <strong>{family.familyStatus}</strong>
          <div className="family-status-metrics">
            <small>Readiness {Math.round(Number(family.readinessScore || 0))}/100</small>
            <small>{family.reviewRequiredCount} reviews</small>
            <small>{family.blockImportCount} block import</small>
            <small>{family.highRiskCount} high risk</small>
          </div>
        </button>
      ))}
    </section>
  );
}
