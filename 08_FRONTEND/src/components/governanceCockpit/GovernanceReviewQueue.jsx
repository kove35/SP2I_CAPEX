import React from "react";
import SmartDataGrid from "../grids/SmartDataGrid";

const badgeClass = (value) => `governance-grid-badge ${String(value || "medium").toLowerCase().replaceAll("_", "-")}`;

export default function GovernanceReviewQueue({ rows = [], onSelect }) {
  const [quickFilterText, setQuickFilterText] = React.useState("");
  const pinnedTopRowData = React.useMemo(() => {
    if (!rows.length) return [];
    return [{
      family: "TOTAL QUEUE",
      referenceId: `${rows.length.toLocaleString("fr-FR")} references`,
      designation: "Validation humaine obligatoire",
      confidenceLevel: `${rows.filter((row) => row.confidenceLevel === "LOW").length} LOW`,
      driftLevel: `${rows.filter((row) => row.driftLevel === "CRITICAL").length} CRITICAL`,
      escalationLevel: `${rows.filter((row) => row.escalationLevel !== "STANDARD_REVIEW").length} escalations`,
      reviewStatus: "PENDING",
      decisionBlocker: `${rows.filter((row) => row.decisionBlocker === "BLOCK_IMPORT").length} BLOCK_IMPORT`,
    }];
  }, [rows]);

  const columns = React.useMemo(() => [
    { field: "family", headerName: "Famille", minWidth: 150, filter: "agSetColumnFilter", pinned: "left" },
    { field: "referenceId", headerName: "Reference", minWidth: 150, pinned: "left" },
    { field: "designation", headerName: "Designation", minWidth: 260, tooltipField: "designation" },
    { field: "confidenceLevel", headerName: "Confidence", minWidth: 130, filter: "agSetColumnFilter", cellClass: ({ value }) => badgeClass(value) },
    { field: "driftLevel", headerName: "Drift", minWidth: 110, filter: "agSetColumnFilter", cellClass: ({ value }) => badgeClass(value) },
    { field: "escalationLevel", headerName: "Escalation", minWidth: 220, filter: "agSetColumnFilter", cellClass: ({ value }) => badgeClass(value) },
    { field: "reviewStatus", headerName: "Review", minWidth: 120, filter: "agSetColumnFilter", cellClass: ({ value }) => badgeClass(value) },
    { field: "decisionBlocker", headerName: "Blocker", minWidth: 190, filter: "agSetColumnFilter", cellClass: ({ value }) => badgeClass(value) },
    { field: "procurementScore", headerName: "Procurement", minWidth: 130, type: "numericColumn", valueFormatter: ({ value }) => `${Math.round(Number(value || 0))}/100` },
    { field: "manualValidationRequired", headerName: "Validation", minWidth: 145, valueFormatter: ({ value }) => value ? "MANUELLE" : "NON", cellClass: "governance-grid-badge red" },
  ], []);

  return (
    <article className="governance-panel governance-review-queue">
      <header className="governance-panel-header">
        <div>
          <span>Review queue</span>
          <strong>References a valider humainement</strong>
        </div>
        <input
          value={quickFilterText}
          onChange={(event) => setQuickFilterText(event.target.value)}
          placeholder="Filtrer famille, reference, escalation..."
          aria-label="Filtrer la review queue governance"
        />
      </header>
      <SmartDataGrid
        rows={rows}
        columns={columns}
        height={520}
        quickFilterText={quickFilterText}
        onRowSelected={onSelect}
        pinnedTopRowData={pinnedTopRowData}
        rowHeight={44}
        headerHeight={44}
        rowClassRules={{
          "row-alert-critical": ({ data }) => data?.reviewPriority === "CRITICAL",
          "row-alert-watch": ({ data }) => data?.reviewPriority === "HIGH",
          "row-active-context": ({ data }) => data?.family === "TOTAL QUEUE",
        }}
        gridOptions={{ maintainColumnOrder: true, suppressAggFuncInHeader: true }}
      />
    </article>
  );
}
