import React from "react";
import BIChart from "./BIChart";
import { useDashboardStore } from "../../store/dashboardStore";

export default function RiskMatrix({ rows = [] }) {
  const setFilters = useDashboardStore((state) => state.setFilters);
  const data = rows.slice(0, 40).map((row, index) => {
    const capex = Number(row.capex_optimise || row.capex_brut || row.capex_local || row.value || 1);
    const gain = Number(row.taux_economie || row.economie_nette || row.economie || 0);
    const risk = Math.min(100, Math.max(5, Number(row.global_risk_score || 100 - gain * 100 || 35 + index)));
    return [gain, risk, Math.max(capex / 1_000_000, 1), row.designation || row.lot || `Ligne ${index + 1}`, row.lot || row.label || ""];
  });

  return (
    <BIChart
      height={280}
      option={{
        backgroundColor: "transparent",
        tooltip: {
          formatter: (params) => `${params.data[3]}<br/>Gain: ${params.data[0]}<br/>Risque: ${Math.round(params.data[1])}/100`,
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
      onEvents={{
        click: (params) => {
          if (params?.data?.[4]) setFilters({ lot: params.data[4] });
        },
      }}
    />
  );
}
