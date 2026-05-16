import React from "react";

export default function SimpleBarChart({ title, data = [] }) {
  const max = Math.max(...data.map((item) => Number(item.value || 0)), 1);

  return (
    <article className="analytics-card simple-chart">
      <h3>{title}</h3>
      <div className="chart-bars">
        {data.map((item) => (
          <div className="chart-row" key={item.label}>
            <span>{item.label}</span>
            <div>
              <i style={{ width: `${Math.max((Number(item.value || 0) / max) * 100, 4)}%` }} />
            </div>
            <strong>{item.display ?? item.value}</strong>
          </div>
        ))}
      </div>
    </article>
  );
}
