import React from "react";
import { AlertTriangle, BrainCircuit, CircleDollarSign, Gauge, ShieldCheck, Target, TrendingDown, TrendingUp } from "lucide-react";
import { formatMoney, formatPercent } from "../../shared/formatters";

const KPI_CONFIG = [
  { key: "capexOptimise", label: "CAPEX optimise", context: "Budget sous controle", icon: CircleDollarSign, format: formatMoney, tier: "primary", tone: "blue" },
  { key: "roi", label: "ROI global", context: "Rendement achat", icon: Target, format: formatPercent, tier: "primary", tone: "green", invertLow: true },
  { key: "gain", label: "Potentiel capturable", context: "Economies identifiees", icon: TrendingUp, format: formatMoney, tier: "primary", tone: "green" },
  { key: "riskScore", label: "Risque global", context: "Maitrise operationnelle", icon: BrainCircuit, suffix: "/100", tier: "primary", tone: "amber", invertHigh: true },
  { key: "importRate", label: "Sourcing coverage", context: "Couverture import/local", icon: ShieldCheck, format: formatPercent, tier: "secondary", tone: "cyan" },
  { key: "procurementScore", label: "Procurement score", context: "Qualite arbitrage", icon: Gauge, suffix: "/100", tier: "secondary", tone: "cyan" },
  { key: "anomalyCount", label: "Anomaly score", context: "Alertes a traiter", icon: AlertTriangle, tier: "secondary", tone: "red", invertHigh: true },
  { key: "financialConfidence", label: "Confidence score", context: "Sanity financiere", icon: ShieldCheck, suffix: "/100", tier: "secondary", tone: "violet" },
];

function formatValue(item, value) {
  if (item.format) return item.format(value);
  if (item.suffix) return `${Math.round(Number(value || 0))}${item.suffix}`;
  return Number(value || 0).toLocaleString("fr-FR");
}

function getSignal(item, value) {
  const numeric = Number(value || 0);
  if (item.key === "anomalyCount") {
    if (numeric >= 8) return { label: "Critical", className: "critical", Icon: TrendingDown };
    if (numeric >= 3) return { label: "Warning", className: "warning", Icon: TrendingDown };
    return { label: "Stable", className: "stable", Icon: TrendingUp };
  }
  if (item.invertHigh) {
    if (numeric >= 65) return { label: "Sous tension", className: "warning", Icon: TrendingDown };
    if (numeric <= 35) return { label: "Maitrise", className: "stable", Icon: TrendingUp };
  }
  if (item.invertLow) {
    if (numeric < 0) return { label: "ROI faible", className: "warning", Icon: TrendingDown };
    if (numeric > 0.12) return { label: "Fort levier", className: "stable", Icon: TrendingUp };
  }
  return { label: "Confiance", className: "stable", Icon: TrendingUp };
}

export default function ProcurementKpiStrip({ kpis = {}, loading = false, onKpiClick }) {
  const primary = KPI_CONFIG.filter((item) => item.tier === "primary");
  const secondary = KPI_CONFIG.filter((item) => item.tier === "secondary");
  const renderCard = (item) => {
    const Icon = item.icon;
    const signal = getSignal(item, kpis[item.key]);
    const SignalIcon = signal.Icon;
    return (
      <button
        className={`procurement-kpi-card tier-${item.tier} tone-${item.tone}`}
        key={item.key}
        aria-busy={loading}
        title={`${item.label} - ${item.context}`}
        type="button"
        onClick={() => onKpiClick?.(item.key)}
      >
        <span className="kpi-label"><Icon size={16} /> {item.label}</span>
        <strong>{loading ? "..." : formatValue(item, kpis[item.key])}</strong>
        <small>{item.context}</small>
        <em className={`kpi-signal ${signal.className}`}><SignalIcon size={12} /> {signal.label}</em>
      </button>
    );
  };

  return (
    <section className="procurement-kpi-strip">
      <div className="kpi-tier kpi-tier-primary">{primary.map(renderCard)}</div>
      <div className="kpi-tier kpi-tier-secondary">{secondary.map(renderCard)}</div>
    </section>
  );
}
