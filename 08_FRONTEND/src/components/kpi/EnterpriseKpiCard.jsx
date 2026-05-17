import React from "react";

export default function EnterpriseKpiCard({ label, value, helper, tone = "blue", icon: Icon, delta }) {
  return (
    <article className={`enterprise-kpi enterprise-kpi-${tone}`}>
      <div className="enterprise-kpi-head">
        <span>{label}</span>
        {Icon ? <Icon size={16} /> : null}
      </div>
      <strong>{value}</strong>
      <footer>
        {helper ? <small>{helper}</small> : null}
        {delta ? <em>{delta}</em> : null}
      </footer>
    </article>
  );
}
