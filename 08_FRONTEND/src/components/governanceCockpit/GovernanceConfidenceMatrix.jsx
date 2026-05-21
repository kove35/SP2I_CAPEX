import React from "react";

const LEVELS = ["HIGH", "MEDIUM", "LOW"];

export default function GovernanceConfidenceMatrix({ rows = [] }) {
  const families = React.useMemo(() => [...new Set(rows.map((row) => row.family))], [rows]);

  return (
    <article className="governance-panel confidence-matrix">
      <header>
        <span>Confidence matrix</span>
        <strong>Confiance par famille et benchmark</strong>
      </header>
      <div className="confidence-table" role="table" aria-label="Matrice de confiance governance">
        <div className="confidence-row header" role="row">
          <span>Famille</span>
          {LEVELS.map((level) => <span key={level}>{level}</span>)}
          <span>Benchmark</span>
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
