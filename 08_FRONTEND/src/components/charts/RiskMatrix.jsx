import React from "react";
import BIChart from "./BIChart";
import { formatMoney } from "../../shared/formatters";
import { useDashboardStore } from "../../store/dashboardStore";
import { analyticsColors } from "../../theme/colors";
import { chartTheme } from "../../theme/chartTheme";

function riskColor(value) {
  if (value >= 72) return analyticsColors.red;
  if (value >= 48) return analyticsColors.amber;
  return analyticsColors.green;
}

export default function RiskMatrix({ rows = [] }) {
  const setFilters = useDashboardStore((state) => state.setFilters);
  const data = rows.slice(0, 48).map((row, index) => {
    const capex = Number(row.capex_optimise || row.capex_brut || row.capex_local || row.value || 1);
    const gain = Number(row.taux_economie || row.economie_nette || row.economie || 0);
    const gainScore = gain > 1 ? Math.min(gain / 1_000_000, 100) : gain * 100;
    const risk = Math.min(100, Math.max(5, Number(row.global_risk_score || 100 - gainScore || 35 + index)));
    return {
      value: [gainScore, risk, Math.max(capex / 1_000_000, 1), row.designation || row.lot || `Ligne ${index + 1}`, row.lot || row.label || "", capex],
      itemStyle: { color: riskColor(risk), opacity: 0.82 },
    };
  });

  return (
    <BIChart
      height={310}
      option={{
        backgroundColor: "transparent",
        tooltip: {
          ...chartTheme.tooltip,
          formatter: (params) =>
            `${params.data.value[3]}<br/>Gain: <b>${Math.round(params.data.value[0])}/100</b><br/>Risque: <b>${Math.round(params.data.value[1])}/100</b><br/>CAPEX: <b>${formatMoney(params.data.value[5])}</b>`,
        },
        grid: { left: 44, right: 24, top: 28, bottom: 42 },
        xAxis: {
          name: "Gain",
          min: 0,
          max: 100,
          axisLabel: chartTheme.axisLabel,
          splitLine: chartTheme.splitLine,
        },
        yAxis: {
          name: "Risque",
          min: 0,
          max: 100,
          axisLabel: chartTheme.axisLabel,
          splitLine: chartTheme.splitLine,
        },
        series: [
          {
            type: "scatter",
            symbolSize: (value) => Math.min(Math.max(value[2] / 5, 8), 42),
            data,
            markLine: {
              silent: true,
              symbol: "none",
              lineStyle: { color: "rgba(203,213,225,.25)", type: "dashed" },
              data: [{ xAxis: 50 }, { yAxis: 50 }],
            },
            markArea: {
              silent: true,
              itemStyle: { color: "rgba(15, 23, 42, .18)" },
              data: [
                [{ name: "Quick wins", xAxis: 50, yAxis: 0 }, { xAxis: 100, yAxis: 50 }],
                [{ name: "Surveillance", xAxis: 50, yAxis: 50 }, { xAxis: 100, yAxis: 100 }],
              ],
            },
          },
        ],
      }}
      onEvents={{
        click: (params) => {
          if (params?.data?.value?.[4]) setFilters({ lot: params.data.value[4] });
        },
      }}
    />
  );
}
