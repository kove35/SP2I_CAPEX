import React from "react";
import { AlertOctagon, ShieldCheck } from "lucide-react";

export default function GovernanceEscalationPanel({ escalations = [], onSelect }) {
  return (
    <article className="governance-panel escalation-panel">
      <header>
        <span>Escalation layer</span>
        <strong>Validations renforcees</strong>
      </header>
      <div className="escalation-list">
        {escalations.map((item) => (
          <button className={`escalation-row ${item.severity?.toLowerCase()}`} type="button" key={item.level} onClick={() => onSelect?.(item.level)}>
            <span>{item.severity === "CRITICAL" ? <AlertOctagon size={16} /> : <ShieldCheck size={16} />} {item.level.replaceAll("_", " ")}</span>
            <strong>{item.volume}</strong>
            <small>{item.critical} critiques | {item.high} high</small>
          </button>
        ))}
      </div>
    </article>
  );
}
