import React from "react";

function statusTone(status) {
  if (status === "BLOCKED") return "critical";
  if (status === "HIGH_RISK") return "risk";
  if (status === "CONDITIONALLY_READY") return "watch";
  return "stable";
}

const statusLabels = {
  BLOCKED: "Bloque",
  HIGH_RISK: "Risque eleve",
  CONDITIONALLY_READY: "Pret sous controle",
  VERIFIED: "Verifie",
};

function familySummary(family) {
  if (family.blockImportCount > 40) return "De nombreuses references ne peuvent pas encore etre importees.";
  if (family.highRiskCount > 0) return "Plusieurs references necessitent une validation par un responsable.";
  if (family.driftCriticalCount > 0) return "Certains prix semblent eloignes du marche local.";
  if (family.reviewRequiredCount > 0) return "Des controles humains restent necessaires avant decision.";
  return "Famille suffisamment controlee pour une revue finale.";
}

export default function GovernanceFamilyStatusBoard({ families = [], onSelect }) {
  return (
    <section className="family-status-board" aria-label="Statut par famille technique">
      {families.map((family) => (
        <button className={`family-status-card ${statusTone(family.familyStatus)}`} type="button" key={family.family} onClick={() => onSelect?.(family.family)}>
          <span>{family.family}</span>
          <strong>{statusLabels[family.familyStatus] || family.familyStatus}</strong>
          <p>{familySummary(family)}</p>
          <div className="family-status-metrics">
            <small>Preparation {Math.round(Number(family.readinessScore || 0))}/100</small>
            <small>{family.reviewRequiredCount} a verifier</small>
            <small>{family.blockImportCount} imports bloques</small>
            <small>{family.highRiskCount} risques critiques</small>
          </div>
        </button>
      ))}
    </section>
  );
}
