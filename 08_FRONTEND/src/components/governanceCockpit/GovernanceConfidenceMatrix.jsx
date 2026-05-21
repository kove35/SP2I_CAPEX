import React from "react";

const LEVELS = ["HIGH", "MEDIUM", "LOW"];
const LEVEL_LABELS = {
  HIGH: "Fiables",
  MEDIUM: "A verifier",
  LOW: "Peu fiables",
};

export default function GovernanceConfidenceMatrix({ rows = [] }) {
  const families = React.useMemo(() => [...new Set(rows.map((row) => row.family))], [rows]);

  return (
    <article className="governance-panel confidence-matrix">
      <header>
        <span>Fiabilite des donnees</span>
        <strong>Ce qui est fiable ou reste a verifier</strong>
      </header>
      <div className="confidence-table" role="table" aria-label="Fiabilite des donnees par famille">
        <div className="confidence-row header" role="row">
          <span>Famille</span>
          {LEVELS.map((level) => <span key={level}>{LEVEL_LABELS[level]}</span>)}
          <span>Prix a confirmer</span>
        </div>
        {families.map((family) => {
          const familyRows = rows.filter((row) => row.family === family);
          return (
            <div className="confidence-row" role="row" key={family}>
              <strong>{family}</strong>
              {LEVELS.map((level) => (
                <span className={`confidence-pill ${level.toLowerCase()}`} key={level}>
                  {familyRows.filter((row) => row.confidenceLevel === level).length}
                </span>
              ))}
              <span className="confidence-pill benchmark">
                {familyRows.filter((row) => row.benchmark === "LOW").length} faibles
              </span>
            </div>
          );
        })}
      </div>
    </article>
  );
}
