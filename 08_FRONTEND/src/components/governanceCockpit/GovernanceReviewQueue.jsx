import React from "react";
import SmartDataGrid from "../grids/SmartDataGrid";

const badgeClass = (value) => `governance-grid-badge ${String(value || "medium").toLowerCase().replaceAll("_", "-")}`;
const labelMap = {
  LOW: "Donnees peu fiables",
  MEDIUM: "A verifier",
  HIGH: "Fiable",
  CRITICAL: "Critique",
  BLOCK_IMPORT: "Importation non autorisee",
  HIGH_RISK: "Risque critique",
  REVIEW_REQUIRED: "Verification achat necessaire",
  TECHNICAL_VALIDATION_REQUIRED: "Controle technique requis",
  SENIOR_PROCUREMENT_APPROVAL: "Responsable achat requis",
  DOUBLE_VALIDATION: "Double verification obligatoire",
  SENIOR_REVIEW: "Validation superieure requise",
  PROCUREMENT_REVIEW: "Verification achat necessaire",
  STANDARD_REVIEW: "Verification standard",
  PENDING: "A verifier",
};

function humanLabel(value) {
  return labelMap[String(value || "").toUpperCase()] || String(value || "A verifier").replaceAll("_", " ");
}

export default function GovernanceReviewQueue({ rows = [], onSelect }) {
  const [quickFilterText, setQuickFilterText] = React.useState("");
  const pinnedTopRowData = React.useMemo(() => {
    if (!rows.length) return [];
    return [{
      family: "TOTAL A VERIFIER",
      referenceId: `${rows.length.toLocaleString("fr-FR")} references`,
      designation: "Validation humaine obligatoire",
      confidenceLevel: `${rows.filter((row) => row.confidenceLevel === "LOW").length} peu fiables`,
      driftLevel: `${rows.filter((row) => row.driftLevel === "CRITICAL").length} critiques`,
      escalationLevel: `${rows.filter((row) => row.escalationLevel !== "STANDARD_REVIEW").length} validations superieures`,
      reviewStatus: "PENDING",
      decisionBlocker: `${rows.filter((row) => row.decisionBlocker === "BLOCK_IMPORT").length} imports non autorises`,
    }];
  }, [rows]);

  const columns = React.useMemo(() => [
    { field: "family", headerName: "Famille", minWidth: 150, filter: "agSetColumnFilter", pinned: "left" },
    { field: "referenceId", headerName: "Reference", minWidth: 150, pinned: "left" },
    { field: "designation", headerName: "Designation", minWidth: 260, tooltipField: "designation" },
    { field: "confidenceLevel", headerName: "Confiance donnees", headerTooltip: "Les prix et fournisseurs sont-ils suffisamment verifies ?", minWidth: 170, filter: "agSetColumnFilter", valueFormatter: ({ value }) => humanLabel(value), cellClass: ({ value }) => badgeClass(value) },
    { field: "driftLevel", headerName: "Ecart marche", headerTooltip: "Le prix semble-t-il eloigne du marche local ?", minWidth: 135, filter: "agSetColumnFilter", valueFormatter: ({ value }) => humanLabel(value), cellClass: ({ value }) => badgeClass(value) },
    { field: "escalationLevel", headerName: "Validation requise", headerTooltip: "Qui doit intervenir avant decision ?", minWidth: 230, filter: "agSetColumnFilter", valueFormatter: ({ value }) => humanLabel(value), cellClass: ({ value }) => badgeClass(value) },
    { field: "reviewStatus", headerName: "Etat", minWidth: 125, filter: "agSetColumnFilter", valueFormatter: ({ value }) => humanLabel(value), cellClass: ({ value }) => badgeClass(value) },
    { field: "decisionBlocker", headerName: "Point bloquant", headerTooltip: "Ce qui empeche une decision immediate.", minWidth: 220, filter: "agSetColumnFilter", valueFormatter: ({ value }) => humanLabel(value), cellClass: ({ value }) => badgeClass(value) },
    { field: "procurementScore", headerName: "Fiabilite achats", minWidth: 150, type: "numericColumn", valueFormatter: ({ value }) => `${Math.round(Number(value || 0))}/100` },
    { field: "manualValidationRequired", headerName: "Controle humain", minWidth: 155, valueFormatter: ({ value }) => value ? "Obligatoire" : "Non", cellClass: "governance-grid-badge red" },
  ], []);

  return (
    <article className="governance-panel governance-review-queue">
      <header className="governance-panel-header">
        <div>
          <span>References a verifier</span>
          <strong>Liste de controle avant decision</strong>
        </div>
        <input
          value={quickFilterText}
          onChange={(event) => setQuickFilterText(event.target.value)}
          placeholder="Filtrer famille, reference, validation..."
          aria-label="Filtrer les references a verifier"
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
          "row-active-context": ({ data }) => data?.family === "TOTAL A VERIFIER",
        }}
        gridOptions={{ maintainColumnOrder: true, suppressAggFuncInHeader: true }}
      />
    </article>
  );
}
