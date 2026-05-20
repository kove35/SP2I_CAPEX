import React from "react";
import SmartDataGrid from "../grids/SmartDataGrid";
import { formatMoney, formatPercent } from "../../shared/formatters";

const scoreFormatter = ({ value }) => `${Math.round(Number(value || 0))}/100`;

export default function ProcurementCockpitGrid({ rows = [], onSelect }) {
  const [quickFilterText, setQuickFilterText] = React.useState("");
  const columns = React.useMemo(() => [
    { field: "lot", headerName: "LOT", minWidth: 160, rowGroup: false, filter: "agSetColumnFilter" },
    { field: "famille", headerName: "Famille CAPEX", minWidth: 180, filter: "agSetColumnFilter" },
    { field: "designation", headerName: "Article", minWidth: 300, pinned: "left", tooltipField: "designation" },
    { field: "supplier", headerName: "Fournisseur", minWidth: 180, filter: "agSetColumnFilter" },
    { field: "decision", headerName: "Decision", minWidth: 120, filter: "agSetColumnFilter" },
    { field: "amount", headerName: "CAPEX", minWidth: 130, type: "numericColumn", valueFormatter: ({ value }) => formatMoney(value) },
    { field: "gain", headerName: "Gain", minWidth: 130, type: "numericColumn", valueFormatter: ({ value }) => formatMoney(value) },
    { field: "roi", headerName: "ROI", minWidth: 100, type: "numericColumn", valueFormatter: ({ value }) => formatPercent(value) },
    { field: "procurement_score", headerName: "Procurement", minWidth: 130, type: "numericColumn", valueFormatter: scoreFormatter },
    { field: "financial_confidence_score", headerName: "Sanity", minWidth: 115, type: "numericColumn", valueFormatter: scoreFormatter },
    { field: "semantic_confidence_score", headerName: "Semantic", minWidth: 120, type: "numericColumn", valueFormatter: scoreFormatter },
    { field: "risk_score", headerName: "Risque", minWidth: 105, type: "numericColumn", valueFormatter: scoreFormatter },
    { field: "anomaly_score", headerName: "Anomalie", minWidth: 115, type: "numericColumn", valueFormatter: scoreFormatter },
    { field: "alert", headerName: "Alerte", minWidth: 120, pinned: "right", filter: "agSetColumnFilter" },
  ], []);

  return (
    <article className="procurement-panel grid-panel" data-fact-metre-grid>
      <header className="grid-panel-header">
        <div>
          <span>Drill-down LOT vers ARTICLE</span>
          <strong>Controle detaille des lignes procurement</strong>
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
        rowClassRules={{
          "row-alert-critical": ({ data }) => Number(data?.anomaly_score || 0) >= 60,
          "row-alert-watch": ({ data }) => Number(data?.anomaly_score || 0) >= 30 && Number(data?.anomaly_score || 0) < 60,
        }}
      />
    </article>
  );
}
