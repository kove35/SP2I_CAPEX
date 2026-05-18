import React from "react";
import { Download, Maximize2 } from "lucide-react";
import SmartDataGrid from "./SmartDataGrid";
import { formatMoney, formatPercent } from "../../shared/formatters";
import { useCrossFiltering } from "../../hooks/useCrossFiltering";

function toCsv(rows) {
  if (!rows.length) return "";
  const keys = ["lot", "famille", "batiment", "niveau", "designation", "decision_import", "capex_local", "capex_optimise", "economie", "taux_economie"];
  const escape = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
  return [keys.join(";"), ...rows.map((row) => keys.map((key) => escape(row[key])).join(";"))].join("\n");
}

export default function FactMetreGrid({ rows = [], total = 0 }) {
  const { applyFilters } = useCrossFiltering();
  const [quickSearch, setQuickSearch] = React.useState("");
  const [fullscreen, setFullscreen] = React.useState(false);
  const metrics = React.useMemo(() => {
    const importRows = rows.filter((row) => String(row.decision_import || "").toUpperCase() === "IMPORT").length;
    const localRows = rows.filter((row) => String(row.decision_import || "").toUpperCase() === "LOCAL").length;
    const savings = rows.reduce((sum, row) => sum + Number(row.economie || 0), 0);
    return { importRows, localRows, savings };
  }, [rows]);

  const columns = React.useMemo(
    () => [
      { field: "lot", headerName: "Lot", minWidth: 220, rowGroup: false },
      { field: "famille", headerName: "Famille", minWidth: 150 },
      { field: "batiment", headerName: "Batiment", minWidth: 170 },
      { field: "niveau", headerName: "Niveau", minWidth: 140 },
      { field: "designation", headerName: "Designation", flex: 1, minWidth: 300 },
      {
        field: "decision_import",
        headerName: "Decision",
        minWidth: 125,
        cellRenderer: ({ value }) => <span className={`decision-badge ${String(value || "").toLowerCase()}`}>{value || "LOCAL"}</span>,
      },
      { field: "capex_local", headerName: "CAPEX brut", valueFormatter: ({ value }) => formatMoney(value), type: "numericColumn" },
      { field: "capex_optimise", headerName: "Optimise", valueFormatter: ({ value }) => formatMoney(value), type: "numericColumn" },
      { field: "economie", headerName: "Economie", valueFormatter: ({ value }) => formatMoney(value), type: "numericColumn" },
      { field: "taux_economie", headerName: "Taux", valueFormatter: ({ value }) => formatPercent(value), type: "numericColumn" },
    ],
    []
  );

  const exportCsv = () => {
    const blob = new Blob([toCsv(rows)], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "sp2i_fact_metre.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className={fullscreen ? "fact-grid-shell fullscreen" : "fact-grid-shell"}>
      <header className="fact-grid-toolbar">
        <div>
          <strong>{Number(total || rows.length).toLocaleString("fr-FR")} lignes FACT_METRE</strong>
          <span>AG Grid connecte a Analytics Engine V1</span>
        </div>
        <div className="fact-grid-metrics">
          <span>IMPORT {metrics.importRows}</span>
          <span>LOCAL {metrics.localRows}</span>
          <span>Gain {formatMoney(metrics.savings)}</span>
        </div>
        <input value={quickSearch} onChange={(event) => setQuickSearch(event.target.value)} placeholder="Recherche rapide" />
        <button type="button" onClick={() => setFullscreen((value) => !value)}>
          <Maximize2 size={15} />
          Plein ecran
        </button>
        <button type="button" onClick={exportCsv}>
          <Download size={15} />
          Export CSV
        </button>
      </header>
      <SmartDataGrid
        rows={rows}
        columns={columns}
        height={fullscreen ? 720 : 470}
        quickFilterText={quickSearch}
        onRowSelected={(row) => applyFilters({ lot: row.lot, famille: row.famille, batiment: row.batiment, niveau: row.niveau })}
      />
    </section>
  );
}
