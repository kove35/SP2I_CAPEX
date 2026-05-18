import React from "react";
import BIChart from "./BIChart";
import { formatMoney } from "../../shared/formatters";
import { analyticsColors } from "../../theme/colors";
import { chartTheme } from "../../theme/chartTheme";

export default function CapexTimeline({ data = [] }) {
  const periods = data.length ? data.map((row) => row.periode || row.date || "periode") : ["T0"];
  const capex = data.length ? data.map((row) => Number(row.capex_optimise || 0)) : [0];
  const savings = data.length ? data.map((row) => Number(row.economie_nette || 0)) : [0];

  return (
    <BIChart
      height={310}
      option={{
        backgroundColor: "transparent",
        tooltip: {
          ...chartTheme.tooltip,
          trigger: "axis",
          formatter: (params) => params.map((item) => `${item.marker}${item.seriesName}: <b>${formatMoney(item.value)}</b>`).join("<br/>"),
        },
        legend: { top: 0, textStyle: { color: "#cbd5e1" } },
        grid: { left: 52, right: 24, top: 48, bottom: 34 },
        xAxis: { type: "category", data: periods, axisLabel: chartTheme.axisLabel },
        yAxis: {
          type: "value",
          axisLabel: { color: analyticsColors.muted, formatter: (value) => `${Math.round(value / 1_000_000)}M` },
          splitLine: chartTheme.splitLine,
        },
        series: [
          { name: "CAPEX optimise", type: "line", smooth: true, areaStyle: { opacity: 0.14 }, data: capex, color: analyticsColors.blue, symbolSize: 9 },
          { name: "Economies", type: "line", smooth: true, areaStyle: { opacity: 0.1 }, data: savings, color: analyticsColors.green, symbolSize: 9 },
        ],
      }}
    />
  );
}
