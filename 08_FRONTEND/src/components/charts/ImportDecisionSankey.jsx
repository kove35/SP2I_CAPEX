import React from "react";
import BIChart from "./BIChart";
import { useDashboardStore } from "../../store/dashboardStore";

export default function ImportDecisionSankey({ rows = [], chartRows = [] }) {
  const setFilters = useDashboardStore((state) => state.setFilters);
  const sourceRows = rows.length ? rows : chartRows;
  const lotMap = sourceRows.reduce((acc, row) => {
    const lot = row.lot || row.label || "Lot non renseigne";
    const decision = String(row.decision_import || row.decision || "IMPORT").toUpperCase() === "LOCAL" ? "LOCAL" : "IMPORT";
    const key = `${decision}|${lot}`;
    const value = Math.max(Number(row.capex_optimise || row.capex_brut || row.value || 0), 1);
    const current = acc.get(key) || { lot, decision, value: 0 };
    current.value += value;
    acc.set(key, current);
    return acc;
  }, new Map());
  const lots = [...lotMap.values()]
    .sort((a, b) => b.value - a.value)
    .slice(0, 12);
  const importTotal = lots.filter((row) => row.decision === "IMPORT").reduce((sum, row) => sum + row.value, 0);
  const localTotal = lots.filter((row) => row.decision !== "IMPORT").reduce((sum, row) => sum + row.value, 0);
  const data = [{ name: "CAPEX" }, { name: "IMPORT" }, { name: "LOCAL" }, ...lots.map((row) => ({ name: row.lot }))];
  const links = [
    { source: "CAPEX", target: "IMPORT", value: importTotal || 1 },
    { source: "CAPEX", target: "LOCAL", value: localTotal || 1 },
    ...lots.map((row) => ({ source: row.decision === "IMPORT" ? "IMPORT" : "LOCAL", target: row.lot, value: row.value })),
  ];

  return (
    <BIChart
      height={280}
      option={{
        backgroundColor: "transparent",
        tooltip: { trigger: "item" },
        series: [
          {
            type: "sankey",
            emphasis: { focus: "adjacency" },
            nodeAlign: "justify",
            lineStyle: { color: "gradient", opacity: 0.35 },
            label: { color: "#dbeafe" },
            data,
            links,
          },
        ],
      }}
      onEvents={{
        click: (params) => {
          if (params?.name?.startsWith("L")) setFilters({ lot: params.name });
          if (params?.name === "IMPORT" || params?.name === "LOCAL") setFilters({ decisionImport: params.name });
        },
      }}
    />
  );
}
