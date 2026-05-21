import React from "react";
import BIChart from "../charts/BIChart";

const driftValue = { LOW: 18, MEDIUM: 48, HIGH: 76, CRITICAL: 96 };

function buildOption(rows = []) {
  const families = [...new Set(rows.map((row) => row.family))];
  const metrics = ["Drift marche", "Procurement", "Technique"];
  const points = families.flatMap((family, y) => {
    const familyRows = rows.filter((row) => row.family === family);
    const avg = (key) => Math.round(familyRows.reduce((sum, row) => sum + (driftValue[row[key]] || 50), 0) / Math.max(familyRows.length, 1));
    return [
      [0, y, avg("driftLevel")],
      [1, y, avg("procurementAlert")],
      [2, y, avg("technicalAlert")],
    ];
  });
  return {
    backgroundColor: "transparent",
    tooltip: { formatter: ({ value }) => `${families[value?.[1]]}<br/>${metrics[value?.[0]]}: ${value?.[2]}/100` },
    grid: { top: 24, right: 18, bottom: 54, left: 118 },
    xAxis: { type: "category", data: metrics, axisLabel: { color: "#b8c7dc" } },
    yAxis: { type: "category", data: families, axisLabel: { color: "#b8c7dc" } },
    visualMap: {
      min: 0,
      max: 100,
      orient: "horizontal",
      right: 12,
      bottom: 0,
      text: ["Critique", "Stable"],
      textStyle: { color: "#b8c7dc", fontSize: 10 },
      inRange: { color: ["#16a34a", "#facc15", "#f97316", "#7f1d1d"] },
    },
    series: [{ type: "heatmap", data: points, label: { show: true, color: "#07111f", fontWeight: 900 }, emphasis: { itemStyle: { borderColor: "#fff", borderWidth: 1 } } }],
  };
}

export default function GovernanceDriftHeatmap({ rows = [] }) {
  const option = React.useMemo(() => buildOption(rows), [rows]);
  return (
    <article className="governance-panel">
      <header>
        <span>Drift heatmap</span>
        <strong>Derive marche et risques benchmarks</strong>
      </header>
      <BIChart option={option} height={320} chartKey={`governance-drift-${rows.length}`} />
    </article>
  );
}
