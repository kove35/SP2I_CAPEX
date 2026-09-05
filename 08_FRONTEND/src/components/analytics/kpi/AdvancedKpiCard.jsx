import React from "react";
import KpiSparkline from "./KpiSparkline";
import KpiTrendBadge from "./KpiTrendBadge";

export default function AdvancedKpiCard({
  label,
  value,
  helper,
  tone = "blue",
  icon: Icon,
  delta = null,
  positiveIsGood = true,
  status = "Live",
  points = [],
}) {
  const hasSeries = Array.isArray(points) && points.length > 0;
  const hasTrend = delta !== null && delta !== undefined && !(typeof value === "string" && value.startsWith("Indisponible"));
  return (
    <article className={`advanced-kpi-card advanced-kpi-${tone}`}>
      <header>
        <span>{label}</span>
        <div>
          <small>{status}</small>
          {Icon ? <Icon size={16} /> : null}
        </div>
      </header>
      <strong>{value}</strong>
      {hasSeries ? <KpiSparkline tone={tone} points={points} /> : null}
      <footer>
        <small>{helper}</small>
        {hasTrend ? <KpiTrendBadge delta={delta} positiveIsGood={positiveIsGood} /> : null}
      </footer>
    </article>
  );
}
