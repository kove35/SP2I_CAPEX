import React from "react";
import BIChart from "./BIChart";

export default function RiskMatrix({ rows = [] }) {
  const data = rows.slice(0, 30).map((row, index) => [
    Number(row.taux_economie || row.economie || 0),
    Number(row.score_confiance || row.global_risk_score || 0),
    Math.max(Number(row.capex_optimise || row.capex_local || 1) / 1_000_000, 1),
    row.designation || `Ligne ${index + 1}`,
  ]);

  return (
    <BIChart
      height={280}
      option={{
        backgroundColor: "transparent",
        tooltip: {
          formatter: (params) => `${params.data[3]}<br/>Gain: ${params.data[0]}<br/>Risque: ${params.data[1]}`,
        },
        grid: { left: 40, right: 20, top: 25, bottom: 38 },
        xAxis: {
          name: "Gain",
          axisLabel: { color: "#9fb4d1" },
          splitLine: { lineStyle: { color: "rgba(148,163,184,.12)" } },
        },
        yAxis: {
          name: "Risque",
          axisLabel: { color: "#9fb4d1" },
          splitLine: { lineStyle: { color: "rgba(148,163,184,.12)" } },
        },
        series: [
          {
            type: "scatter",
            symbolSize: (value) => Math.min(Math.max(value[2] / 6, 8), 36),
            data,
            itemStyle: { color: "#5eead4", opacity: 0.82 },
          },
        ],
      }}
    />
  );
}
