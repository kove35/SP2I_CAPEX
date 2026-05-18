import React from "react";
import BIChart from "./BIChart";
import { formatMoney } from "../../shared/formatters";
import { useCrossFiltering } from "../../hooks/useCrossFiltering";

function normalizeHeatmap(payload) {
  if (payload?.xLabels && payload?.yLabels && Array.isArray(payload?.data)) {
    return {
      xLabels: payload.xLabels,
      yLabels: payload.yLabels,
      data: payload.data.map((item) => [Number(item[0]), Number(item[1]), Number(item[2] || 0)]),
      max: Number(payload.max || Math.max(...payload.data.map((item) => Number(item[2] || 0)), 1)),
    };
  }

  const rows = Array.isArray(payload) ? payload : [];
  const xLabels = [...new Set(rows.map((row) => row.lot || "NON_RENSEIGNE"))].slice(0, 16);
  const yLabels = [...new Set(rows.map((row) => row.famille || "default"))].slice(0, 14);
  const data = rows
    .slice(0, 224)
    .map((row) => [
      xLabels.indexOf(row.lot || "NON_RENSEIGNE"),
      yLabels.indexOf(row.famille || "default"),
      Number(row.value || 0),
    ])
    .filter((item) => item[0] >= 0 && item[1] >= 0);
  return {
    xLabels,
    yLabels,
    data,
    max: Math.max(...data.map((item) => item[2]), 1),
  };
}

export default function CapexHeatmap({ data = [] }) {
  const { applyFilters } = useCrossFiltering();
  const heatmap = React.useMemo(() => normalizeHeatmap(data), [data]);
  const chartKey = `heatmap-${heatmap.xLabels.join("|")}-${heatmap.yLabels.join("|")}-${heatmap.data.length}`;

  return (
    <BIChart
      height={340}
      chartKey={chartKey}
      option={{
        backgroundColor: "transparent",
        tooltip: {
          backgroundColor: "rgba(7, 17, 31, .96)",
          borderColor: "rgba(148, 163, 184, .24)",
          textStyle: { color: "#f8fafc" },
          formatter: (params) => {
            const [x, y, value] = params.data || [];
            return `${heatmap.xLabels[x] || "Lot"}<br/>${heatmap.yLabels[y] || "Famille"}<br/><b>${formatMoney(value)}</b>`;
          },
        },
        grid: { left: 124, right: 24, top: 28, bottom: 92 },
        xAxis: {
          type: "category",
          data: heatmap.xLabels,
          axisLabel: { color: "#9fb4d1", rotate: 35, fontSize: 10, interval: 0 },
          axisLine: { lineStyle: { color: "rgba(148,163,184,.18)" } },
        },
        yAxis: {
          type: "category",
          data: heatmap.yLabels,
          axisLabel: { color: "#9fb4d1", fontSize: 10 },
          axisLine: { lineStyle: { color: "rgba(148,163,184,.18)" } },
        },
        visualMap: {
          min: 0,
          max: Math.max(heatmap.max, 1),
          calculable: true,
          orient: "horizontal",
          left: "center",
          bottom: 12,
          textStyle: { color: "#9fb4d1" },
          inRange: { color: ["#1e3a8a", "#0891b2", "#facc15", "#f97316", "#dc2626"] },
          handleStyle: { color: "#67e8c9" },
        },
        series: [
          {
            type: "heatmap",
            data: heatmap.data,
            label: { show: false },
            progressive: 200,
            emphasis: {
              itemStyle: {
                borderColor: "#f8fafc",
                borderWidth: 1,
                shadowBlur: 10,
                shadowColor: "rgba(103,232,201,.35)",
              },
            },
          },
        ],
      }}
      onEvents={{
        click: (params) => {
          const [x, y] = params?.data || [];
          applyFilters({ lot: heatmap.xLabels[x] || "", famille: heatmap.yLabels[y] || "" });
        },
      }}
    />
  );
}
