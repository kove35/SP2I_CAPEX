import React from "react";
import { AlertTriangle, CheckCircle2, FileWarning, Info, ShieldAlert, TrendingDown, UsersRound } from "lucide-react";

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
    {
      label: "Niveau global de controle",
      value: scoreValue(kpis.globalGovernanceScore),
      tone: scoreTone(kpis.globalGovernanceScore),
      icon: ShieldAlert,
      note: "Donnees encore partiellement verifiees",
      help: "Indique si les references sont assez controlees pour aider une decision fiable.",
    },
    {
      label: "Fiabilite des achats",
      value: scoreValue(kpis.globalProcurementScore),
      tone: "risk",
      icon: TrendingDown,
      note: "Achats necessitant une validation humaine",
      help: "Mesure si fournisseurs, prix et conditions d'achat sont suffisamment controles.",
    },
    {
      label: "Niveau de confiance des donnees",
      value: scoreValue(kpis.globalConfidenceScore),
      tone: scoreTone(kpis.globalConfidenceScore),
      icon: CheckCircle2,
      note: "Aucune confiance haute automatique",
      help: "Indique si les prix et fournisseurs ont ete suffisamment verifies.",
    },
    {
      label: "Ecart avec le marche",
      value: scoreValue(kpis.globalDriftScore),
      tone: scoreTone(kpis.globalDriftScore),
      icon: AlertTriangle,
      note: "Prix a comparer au marche local",
      help: "Mesure si les prix proposes semblent coherents avec le marche local.",
    },
    {
      label: "References a verifier",
      value: Number(kpis.globalReviewBacklog || 0).toLocaleString("fr-FR"),
      tone: "critical",
      icon: UsersRound,
      note: "Validation manuelle obligatoire",
      help: "Nombre de references qui doivent encore etre controlees par une personne.",
    },
    {
      label: "Risques critiques",
      value: Number(kpis.globalHighRiskCount || 0).toLocaleString("fr-FR"),
      tone: "critical",
      icon: FileWarning,
      note: "Responsable achat a impliquer",
      help: "References qui peuvent influencer fortement la decision ou le budget.",
    },
  ];

  return (
    <section className="governance-kpi-strip" aria-label="Indicateurs governance">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <article className={`governance-kpi-card ${item.tone}`} key={item.label}>
            <span><Icon size={16} /> {item.label} <Info className="governance-info-icon" size={13} aria-label={item.help} title={item.help} /></span>
            <strong>{item.value}</strong>
            <small>{item.note}</small>
          </article>
        );
      })}
    </section>
  );
}
