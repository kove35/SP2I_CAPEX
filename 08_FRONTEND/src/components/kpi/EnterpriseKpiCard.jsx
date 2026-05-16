import React from "react";

export default function EnterpriseKpiCard({ label, value, helper, tone = "blue" }) {
  return (
    <article className={`enterprise-kpi enterprise-kpi-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {helper ? <small>{helper}</small> : null}
    </article>
  );
}
