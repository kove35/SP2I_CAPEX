import React from "react";
import BIChart from "./BIChart";
import { formatMoney } from "../../shared/formatters";

export default function CapexTimeline({ data = [] }) {
  const periods = data.map((row) => row.periode || row.date || "periode");
  const capex = data.map((row) => Number(row.capex_optimise || 0));
  const savings = data.map((row) => Number(row.economie_nette || 0));

  return (
    <BIChart
      height={280}
      option={{
        backgroundColor: "transparent",
        tooltip: {
          trigger: "axis",
          formatter: (params) => params.map((item) => `${item.marker}${item.seriesName}: <b>${formatMoney(item.value)}</b>`).join("<br/>"),
        },
        legend: { top: 0, textStyle: { color: "#cbd5e1" } },
        grid: { left: 50, right: 24, top: 42, bottom: 34 },
        xAxis: { type: "category", data: periods, axisLabel: { color: "#9fb4d1" } },
        yAxis: { type: "value", axisLabel: { color: "#9fb4d1" }, splitLine: { lineStyle: { color: "rgba(148,163,184,.12)" } } },
        series: [
          { name: "CAPEX optimisé", type: "line", smooth: true, areaStyle: { opacity: 0.12 }, data: capex, color: "#60a5fa" },
          { name: "Economies", type: "line", smooth: true, areaStyle: { opacity: 0.1 }, data: savings, color: "#34d399" },
        ],
      }}
    />
  );
}
