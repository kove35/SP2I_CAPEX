import React from "react";

export default function KpiSparkline({ tone = "blue", points = [] }) {
  const values = points.length ? points : [34, 42, 39, 51, 48, 62, 68];
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = Math.max(max - min, 1);
  const path = values
    .map((value, index) => {
      const x = (index / Math.max(values.length - 1, 1)) * 100;
      const y = 34 - ((value - min) / range) * 28;
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");

  return (
    <svg className={`kpi-sparkline sparkline-${tone}`} viewBox="0 0 100 40" preserveAspectRatio="none" aria-hidden="true">
      <path className="sparkline-fill" d={`${path} L 100 40 L 0 40 Z`} />
      <path className="sparkline-line" d={path} />
    </svg>
  );
}
