import React from "react";

export default function KpiCard({ label, value, trend, tone = "neutral" }) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {trend ? <small>{trend}</small> : null}
    </article>
  );
}
