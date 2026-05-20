import React from "react";
import SmartDataGrid from "../grids/SmartDataGrid";
import { formatMoney, formatPercent } from "../../shared/formatters";

const scoreFormatter = ({ value }) => `${Math.round(Number(value || 0))}/100`;
const severityLabel = (value) => {
  const score = Number(value || 0);
  if (score >= 60) return "CRITICAL";
  if (score >= 30) return "WARNING";
  if (score > 0) return "INFO";
  return "STABLE";
};

export default function ProcurementCockpitGrid({ rows = [], onSelect }) {
  const [quickFilterText, setQuickFilterText] = React.useState("");
  const pinnedTopRowData = React.useMemo(() => {
    if (!rows.length) return [];
    const sum = (key) => rows.reduce((total, row) => total + Number(row[key] || 0), 0);
    const avg = (key) => sum(key) / rows.length;
    return [{
      lot: "TOTAL CONTEXTE",
      famille: `${rows.length.toLocaleString("fr-FR")} lignes`,
      designation: "Synthese cross-filtered",
      supplier: "Tous fournisseurs",
      decision: "MIX",
      amount: sum("amount"),
      gain: sum("gain"),
      roi: sum("amount") ? sum("gain") / sum("amount") : 0,
      procurement_score: avg("procurement_score"),
      financial_confidence_score: avg("financial_confidence_score"),
      semantic_confidence_score: avg("semantic_confidence_score"),
      risk_score: avg("risk_score"),
      anomaly_score: avg("anomaly_score"),
      alert: severityLabel(avg("anomaly_score")),
    }];
  }, [rows]);
  const columns = React.useMemo(() => [
    { field: "lot", headerName: "LOT", minWidth: 160, rowGroup: false, filter: "agSetColumnFilter" },
    { field: "famille", headerName: "Famille CAPEX", minWidth: 180, filter: "agSetColumnFilter" },
    { field: "designation", headerName: "Article", minWidth: 300, pinned: "left", tooltipField: "designation" },
    { field: "supplier", headerName: "Fournisseur", minWidth: 180, filter: "agSetColumnFilter" },
    { field: "decision", headerName: "Sourcing", minWidth: 120, filter: "agSetColumnFilter", cellClass: ({ value }) => value === "IMPORT" ? "grid-badge grid-badge-import" : "grid-badge grid-badge-local" },
    { field: "amount", headerName: "CAPEX", minWidth: 130, type: "numericColumn", valueFormatter: ({ value }) => formatMoney(value) },
    { field: "gain", headerName: "Gain", minWidth: 130, type: "numericColumn", valueFormatter: ({ value }) => formatMoney(value) },
    { field: "roi", headerName: "ROI", minWidth: 100, type: "numericColumn", valueFormatter: ({ value }) => formatPercent(value), cellClass: ({ value }) => Number(value || 0) >= 0.12 ? "grid-score-good" : "grid-score-watch" },
    { field: "procurement_score", headerName: "Procurement", minWidth: 130, type: "numericColumn", valueFormatter: scoreFormatter, cellClass: ({ value }) => Number(value || 0) >= 70 ? "grid-score-good" : "grid-score-watch" },
    { field: "financial_confidence_score", headerName: "Sanity", minWidth: 115, type: "numericColumn", valueFormatter: scoreFormatter },
    { field: "semantic_confidence_score", headerName: "Semantic", minWidth: 120, type: "numericColumn", valueFormatter: scoreFormatter },
    { field: "risk_score", headerName: "Risque", minWidth: 105, type: "numericColumn", valueFormatter: scoreFormatter, cellClass: ({ value }) => Number(value || 0) >= 60 ? "grid-risk-high" : "grid-score-good" },
    { field: "anomaly_score", headerName: "Anomalie", minWidth: 115, type: "numericColumn", valueFormatter: scoreFormatter, cellClass: ({ value }) => Number(value || 0) >= 60 ? "grid-risk-high" : Number(value || 0) >= 30 ? "grid-risk-watch" : "grid-score-good" },
    { field: "alert", headerName: "Severity", minWidth: 120, pinned: "right", filter: "agSetColumnFilter", valueGetter: ({ data }) => data?.alert || severityLabel(data?.anomaly_score), cellClass: ({ value }) => `grid-severity grid-severity-${String(value || "stable").toLowerCase()}` },
  ], []);

  return (
    <article className="procurement-panel grid-panel" data-fact-metre-grid>
      <header className="grid-panel-header">
        <div>
          <span>Drill-down LOT vers ARTICLE</span>
          <strong>Controle detaille des lignes procurement</strong>
        </div>
        <div className="grid-action-cluster">
          <span>{rows.length.toLocaleString("fr-FR")} lignes</span>
          <span>{rows.filter((row) => Number(row.anomaly_score || 0) >= 60).length} critical</span>
        </div>
        <input
          value={quickFilterText}
          onChange={(event) => setQuickFilterText(event.target.value)}
          placeholder="Filtrer article, lot, fournisseur..."
          aria-label="Filtrer les lignes procurement"
        />
      </header>
      <SmartDataGrid
        rows={rows}
        columns={columns}
        height={520}
        quickFilterText={quickFilterText}
        onRowSelected={onSelect}
        pinnedTopRowData={pinnedTopRowData}
        rowHeight={46}
        headerHeight={44}
        rowClassRules={{
          "row-active-context": ({ data }) => data?.lot === "TOTAL CONTEXTE",
          "row-alert-critical": ({ data }) => Number(data?.anomaly_score || 0) >= 60,
          "row-alert-watch": ({ data }) => Number(data?.anomaly_score || 0) >= 30 && Number(data?.anomaly_score || 0) < 60,
        }}
        gridOptions={{
          suppressAggFuncInHeader: true,
          maintainColumnOrder: true,
        }}
      />
    </article>
  );
}
