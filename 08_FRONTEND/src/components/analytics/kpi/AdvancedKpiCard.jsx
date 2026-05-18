import React from "react";
import KpiSparkline from "./KpiSparkline";
import KpiTrendBadge from "./KpiTrendBadge";

export default function AdvancedKpiCard({
  label,
  value,
  helper,
  tone = "blue",
  icon: Icon,
  delta = 0,
  positiveIsGood = true,
  status = "Live",
  points,
}) {
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
      <KpiSparkline tone={tone} points={points} />
      <footer>
        <small>{helper}</small>
        <KpiTrendBadge delta={delta} positiveIsGood={positiveIsGood} />
      </footer>
    </article>
  );
}
