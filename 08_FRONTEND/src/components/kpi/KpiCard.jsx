import React from "react";

export default function KpiCard({ label, value, help, tone = "default" }) {
  return (
    <article className={`analytics-card kpi-card kpi-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {help ? <small>{help}</small> : null}
    </article>
  );
}
