import React from "react";
import BIChart from "./BIChart";
import { formatMoney } from "../../shared/formatters";
import { useDashboardStore } from "../../store/dashboardStore";
import { analyticsColors } from "../../theme/colors";
import { chartTheme } from "../../theme/chartTheme";

export default function ImportDecisionSankey({ rows = [], chartRows = [] }) {
  const setFilters = useDashboardStore((state) => state.setFilters);
  const sourceRows = rows.length ? rows : chartRows;
  const lotMap = sourceRows.reduce((acc, row) => {
    const lot = row.lot || row.label || "Lot non renseigne";
    const decision = String(row.decision_import || row.decision || "IMPORT").toUpperCase() === "LOCAL" ? "LOCAL" : "IMPORT";
    const key = `${decision}|${lot}`;
    const value = Math.max(Number(row.capex_optimise || row.capex_brut || row.value || 0), 1);
    const current = acc.get(key) || { lot, decision, nodeName: `${lot} - ${decision}`, value: 0 };
    current.value += value;
    acc.set(key, current);
    return acc;
  }, new Map());
  const lots = [...lotMap.values()].sort((a, b) => b.value - a.value).slice(0, 10);
  const importTotal = lots.filter((row) => row.decision === "IMPORT").reduce((sum, row) => sum + row.value, 0);
  const localTotal = lots.filter((row) => row.decision !== "IMPORT").reduce((sum, row) => sum + row.value, 0);
  const data = [
    { name: "CAPEX", itemStyle: { color: analyticsColors.blue } },
    { name: "IMPORT", itemStyle: { color: analyticsColors.green } },
    { name: "LOCAL", itemStyle: { color: analyticsColors.amber } },
    ...lots.map((row) => ({
      name: row.nodeName,
      label: { formatter: row.lot },
      itemStyle: { color: row.decision === "IMPORT" ? analyticsColors.green : analyticsColors.amber },
    })),
  ];
  const links = [
    { source: "CAPEX", target: "IMPORT", value: importTotal || 1 },
    { source: "CAPEX", target: "LOCAL", value: localTotal || 1 },
    ...lots.map((row) => ({ source: row.decision, target: row.nodeName, value: row.value })),
  ];
  const chartKey = `sankey-${lots.map((row) => row.nodeName).join("|") || "empty"}`;

  return (
    <BIChart
      height={310}
      chartKey={chartKey}
      option={{
        backgroundColor: "transparent",
        tooltip: {
          ...chartTheme.tooltip,
          trigger: "item",
          formatter: (params) => {
            const value = params?.data?.value;
            return `${params.name}<br/><b>${Number(value || 0) ? formatMoney(value) : "Flux decisionnel"}</b>`;
          },
        },
        series: [
          {
            type: "sankey",
            emphasis: { focus: "adjacency" },
            nodeAlign: "justify",
            draggable: false,
            lineStyle: { color: "gradient", opacity: 0.42, curveness: 0.52 },
            label: { color: "#dbeafe", fontSize: 11, overflow: "truncate", width: 150 },
            levels: [
              { depth: 0, itemStyle: { borderColor: analyticsColors.blue } },
              { depth: 1, itemStyle: { borderColor: analyticsColors.green } },
              { depth: 2, itemStyle: { borderColor: analyticsColors.cyan } },
            ],
            data,
            links,
          },
        ],
      }}
      onEvents={{
        click: (params) => {
          const lot = lots.find((row) => row.nodeName === params?.name)?.lot;
          if (lot) setFilters({ lot });
          if (params?.name === "IMPORT" || params?.name === "LOCAL") setFilters({ decisionImport: params.name });
        },
      }}
    />
  );
}
