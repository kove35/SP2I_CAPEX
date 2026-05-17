import React from "react";
import BIChart from "./BIChart";
import { formatMoney } from "../../shared/formatters";
import { useDashboardStore } from "../../store/dashboardStore";

export default function CapexHeatmap({ data = [] }) {
  const setFilters = useDashboardStore((state) => state.setFilters);
  const lots = [...new Set(data.map((row) => row.lot || "NON_RENSEIGNE"))].slice(0, 12);
  const familles = [...new Set(data.map((row) => row.famille || "default"))].slice(0, 12);
  const matrix = data
    .slice(0, 144)
    .map((row) => [
      lots.indexOf(row.lot || "NON_RENSEIGNE"),
      familles.indexOf(row.famille || "default"),
      Number(row.value || 0),
      row.lot,
      row.famille,
    ])
    .filter((row) => row[0] >= 0 && row[1] >= 0);

  return (
    <BIChart
      height={310}
      option={{
        backgroundColor: "transparent",
        tooltip: {
          formatter: (params) => `${params.data[3]}<br/>${params.data[4]}<br/><b>${formatMoney(params.data[2])}</b>`,
        },
        grid: { left: 128, right: 20, top: 28, bottom: 76 },
        xAxis: { type: "category", data: lots, axisLabel: { color: "#9fb4d1", rotate: 30 } },
        yAxis: { type: "category", data: familles, axisLabel: { color: "#9fb4d1" } },
        visualMap: {
          min: 0,
          max: Math.max(...matrix.map((item) => item[2]), 1),
          orient: "horizontal",
          left: "center",
          bottom: 0,
          textStyle: { color: "#9fb4d1" },
          inRange: { color: ["#0f172a", "#155e75", "#22d3ee", "#f59e0b"] },
        },
        series: [{ type: "heatmap", data: matrix, emphasis: { itemStyle: { borderColor: "#e0f2fe", borderWidth: 1 } } }],
      }}
      onEvents={{
        click: (params) => {
          const row = params?.data;
          if (row) setFilters({ lot: row[3], famille: row[4] });
        },
      }}
    />
  );
}
