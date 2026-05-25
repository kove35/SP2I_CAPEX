import React from "react";
import RiskMatrix from "../../../components/charts/RiskMatrix";
import { formatMoney } from "../../../shared/formatters";

function toMatrixRows(risks = []) {
  return risks.map((risk) => ({
    lot: risk.lot,
    label: risk.label,
    impact: risk.impact,
    probabilite: risk.probability,
    criticite: risk.criticality,
    risque_type: risk.label,
  }));
}

export default function RisquesApprovisionnement({ risks = [] }) {
  const matrixRows = React.useMemo(() => toMatrixRows(risks), [risks]);
  return (
    <article className="appro-panel appro-risk-panel">
      <header className="appro-panel-header">
        <div>
          <span>Risques</span>
          <strong>Impact chantier x probabilité</strong>
        </div>
      </header>
      <RiskMatrix rows={matrixRows} />
      <div className="appro-risk-list">
        {risks.slice(0, 4).map((risk) => (
          <div key={risk.id}>
            <strong>{risk.label}</strong>
            <span>{risk.lot} · impact {formatMoney(risk.impact)} · criticité {Math.round(risk.criticality)}/100</span>
            <p>{risk.action}</p>
          </div>
        ))}
      </div>
    </article>
  );
}
