import React from "react";
import { AlertOctagon, ShieldCheck } from "lucide-react";

const labels = {
  SENIOR_PROCUREMENT_APPROVAL: "Responsable achat requis",
  DOUBLE_VALIDATION: "Double verification obligatoire",
  SENIOR_REVIEW: "Validation superieure requise",
  PROCUREMENT_REVIEW: "Verification achat necessaire",
  STANDARD_REVIEW: "Verification standard",
};

const descriptions = {
  SENIOR_PROCUREMENT_APPROVAL: "Une personne senior doit autoriser la suite avant decision.",
  DOUBLE_VALIDATION: "Deux controles independants sont necessaires.",
  SENIOR_REVIEW: "Le dossier doit etre relu par un responsable.",
  PROCUREMENT_REVIEW: "Les conditions d'achat doivent etre verifiees.",
  STANDARD_REVIEW: "Controle simple avant classement.",
};

export default function GovernanceEscalationPanel({ escalations = [], onSelect }) {
  return (
    <article className="governance-panel escalation-panel">
      <header>
        <span>Validations superieures</span>
        <strong>Qui doit intervenir ?</strong>
      </header>
      <div className="escalation-list">
        {escalations.map((item) => (
          <button className={`escalation-row ${item.severity?.toLowerCase()}`} type="button" key={item.level} onClick={() => onSelect?.(item.level)}>
            <span>{item.severity === "CRITICAL" ? <AlertOctagon size={16} /> : <ShieldCheck size={16} />} {labels[item.level] || item.level.replaceAll("_", " ")}</span>
            <strong>{item.volume}</strong>
            <small>{descriptions[item.level] || "Controle humain requis."}</small>
            <small>{item.critical} critiques | {item.high} a surveiller</small>
          </button>
        ))}
      </div>
    </article>
  );
}
