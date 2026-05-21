import React from "react";
import { AlertTriangle, CheckCircle2, FileWarning, ShieldAlert, TrendingDown, UsersRound } from "lucide-react";

function scoreTone(value) {
  const score = Number(value || 0);
  if (score >= 75) return "watch";
  if (score >= 50) return "risk";
  return "critical";
}

function scoreValue(value) {
  return `${Math.round(Number(value || 0))}/100`;
}

export default function GovernanceKpiStrip({ kpis = {} }) {
  const items = [
    { label: "Governance score", value: scoreValue(kpis.globalGovernanceScore), tone: scoreTone(kpis.globalGovernanceScore), icon: ShieldAlert, note: "Confiance supervisee" },
    { label: "Procurement score", value: scoreValue(kpis.globalProcurementScore), tone: "critical", icon: TrendingDown, note: "Decision non automatisee" },
    { label: "Confidence score", value: scoreValue(kpis.globalConfidenceScore), tone: scoreTone(kpis.globalConfidenceScore), icon: CheckCircle2, note: "Aucun HIGH automatique" },
    { label: "Drift score", value: scoreValue(kpis.globalDriftScore), tone: scoreTone(kpis.globalDriftScore), icon: AlertTriangle, note: "Marches a surveiller" },
    { label: "Review backlog", value: Number(kpis.globalReviewBacklog || 0).toLocaleString("fr-FR"), tone: "critical", icon: UsersRound, note: "Validation humaine" },
    { label: "High risk", value: Number(kpis.globalHighRiskCount || 0).toLocaleString("fr-FR"), tone: "critical", icon: FileWarning, note: "Escalade requise" },
  ];

  return (
    <section className="governance-kpi-strip" aria-label="Indicateurs governance">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <article className={`governance-kpi-card ${item.tone}`} key={item.label}>
            <span><Icon size={16} /> {item.label}</span>
            <strong>{item.value}</strong>
            <small>{item.note}</small>
          </article>
        );
      })}
    </section>
  );
}
