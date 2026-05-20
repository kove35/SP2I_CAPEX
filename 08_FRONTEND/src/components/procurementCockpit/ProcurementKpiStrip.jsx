import React from "react";
import { AlertTriangle, BrainCircuit, CircleDollarSign, Gauge, ShieldCheck, Target, TrendingUp } from "lucide-react";
import { formatMoney, formatPercent } from "../../shared/formatters";

const KPI_CONFIG = [
  { key: "capexOptimise", label: "CAPEX optimise", icon: CircleDollarSign, format: formatMoney },
  { key: "gain", label: "Gain capture", icon: TrendingUp, format: formatMoney },
  { key: "roi", label: "ROI achat", icon: Target, format: formatPercent },
  { key: "procurementScore", label: "Procurement score", icon: Gauge, suffix: "/100" },
  { key: "financialConfidence", label: "Financial sanity", icon: ShieldCheck, suffix: "/100" },
  { key: "anomalyCount", label: "Alertes anomalies", icon: AlertTriangle },
  { key: "importRate", label: "Sourcing coverage", icon: ShieldCheck, format: formatPercent },
  { key: "riskScore", label: "Risk intelligence", icon: BrainCircuit, suffix: "/100" },
];

function formatValue(item, value) {
  if (item.format) return item.format(value);
  if (item.suffix) return `${Math.round(Number(value || 0))}${item.suffix}`;
  return Number(value || 0).toLocaleString("fr-FR");
}

export default function ProcurementKpiStrip({ kpis = {}, loading = false, onKpiClick }) {
  return (
    <section className="procurement-kpi-strip">
      {KPI_CONFIG.map((item) => {
        const Icon = item.icon;
        return (
          <button className="procurement-kpi-card" key={item.key} aria-busy={loading} type="button" onClick={() => onKpiClick?.(item.key)}>
            <span><Icon size={16} /> {item.label}</span>
            <strong>{loading ? "..." : formatValue(item, kpis[item.key])}</strong>
          </button>
        );
      })}
    </section>
  );
}
