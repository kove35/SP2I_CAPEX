import React from "react";
import BIChart from "./BIChart";

export default function ImportDecisionSankey({ rows = [] }) {
  const importCount = rows.filter((row) => String(row.decision_import || "").toUpperCase() === "IMPORT").length;
  const localCount = Math.max(rows.length - importCount, 0);

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
            data: [
              { name: "DQE" },
              { name: "Import recommande" },
              { name: "Local securise" },
              { name: "CAPEX optimise" },
            ],
            links: [
              { source: "DQE", target: "Import recommande", value: importCount || 1 },
              { source: "DQE", target: "Local securise", value: localCount || 1 },
              { source: "Import recommande", target: "CAPEX optimise", value: importCount || 1 },
              { source: "Local securise", target: "CAPEX optimise", value: localCount || 1 },
            ],
          },
        ],
      }}
    />
  );
}
