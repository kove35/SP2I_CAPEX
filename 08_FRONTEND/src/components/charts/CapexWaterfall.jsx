import React from "react";
import BIChart from "./BIChart";

export default function CapexWaterfall({ summary = {} }) {
  const capexLocal = Number(summary.capex_local || 0);
  const economie = Number(summary.economie || summary.economie_nette || 0);
  const capexOptimise = Number(summary.capex_optimise || 0);

  return (
    <BIChart
      height={300}
      option={{
        backgroundColor: "transparent",
        tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
        grid: { left: 42, right: 20, top: 30, bottom: 36 },
        xAxis: {
          type: "category",
          data: ["CAPEX brut", "Economie", "CAPEX optimise"],
          axisLabel: { color: "#9fb4d1" },
        },
        yAxis: {
          type: "value",
          axisLabel: { color: "#9fb4d1" },
          splitLine: { lineStyle: { color: "rgba(148,163,184,.12)" } },
        },
        series: [
          {
            type: "bar",
            data: [
              { value: capexLocal, itemStyle: { color: "#60a5fa" } },
              { value: economie, itemStyle: { color: "#34d399" } },
              { value: capexOptimise, itemStyle: { color: "#f59e0b" } },
            ],
            barWidth: 34,
          },
        ],
      }}
    />
  );
}
