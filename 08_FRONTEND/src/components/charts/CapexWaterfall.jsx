import React from "react";
import BIChart from "./BIChart";
import { formatMoney } from "../../shared/formatters";
import { analyticsColors } from "../../theme/colors";
import { chartTheme } from "../../theme/chartTheme";

export default function CapexWaterfall({ summary = {} }) {
  const capexLocal = Number(summary.capex_brut || summary.capex_local || 0);
  const economie = Number(summary.economie || summary.economie_nette || 0);
  const capexOptimise = Number(summary.capex_optimise || 0);
  const optimisations = Math.max(capexLocal - capexOptimise, 0);

  return (
    <BIChart
      height={320}
      option={{
        backgroundColor: "transparent",
        color: chartTheme.color,
        tooltip: {
          ...chartTheme.tooltip,
          trigger: "axis",
          axisPointer: { type: "shadow" },
          formatter: (params) =>
            params
              .filter((item) => item.seriesName !== "Base")
              .map((item) => `${item.marker}${item.name}<br/><b>${formatMoney(item.value)}</b>`)
              .join("<br/>"),
        },
        grid: { left: 54, right: 20, top: 38, bottom: 42 },
        xAxis: {
          type: "category",
          data: ["CAPEX brut", "Optimisations", "Economies", "CAPEX final"],
          axisLabel: { color: analyticsColors.muted },
        },
        yAxis: {
          type: "value",
          axisLabel: { color: analyticsColors.muted, formatter: (value) => `${Math.round(value / 1_000_000)}M` },
          splitLine: chartTheme.splitLine,
        },
        series: [
          {
            name: "Base",
            type: "bar",
            stack: "total",
            itemStyle: { color: "transparent" },
            emphasis: { itemStyle: { color: "transparent" } },
            data: [0, capexOptimise, capexOptimise, 0],
          },
          {
            name: "CAPEX",
            type: "bar",
            stack: "total",
            barWidth: 34,
            label: {
              show: true,
              position: "top",
              color: analyticsColors.text,
              fontWeight: 800,
              formatter: ({ value }) => `${Math.round(Number(value || 0) / 1_000_000)}M`,
            },
            data: [
              { value: capexLocal, itemStyle: { color: analyticsColors.blue } },
              { value: optimisations, itemStyle: { color: analyticsColors.cyan } },
              { value: economie, itemStyle: { color: analyticsColors.green } },
              { value: capexOptimise, itemStyle: { color: analyticsColors.amber } },
            ],
          },
        ],
      }}
    />
  );
}
