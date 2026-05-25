import React from "react";
import SmartDataGrid from "../../../components/grids/SmartDataGrid";
import { formatMoney } from "../../../shared/formatters";

function riskClass(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("critique")) return "grid-risk-high";
  if (normalized.includes("élevé") || normalized.includes("eleve")) return "grid-risk-watch";
  return "grid-score-good";
}

export default function CommandesPanel({ orders = [], onSelect }) {
  const [quickFilterText, setQuickFilterText] = React.useState("");
  const columns = React.useMemo(() => [
    { field: "reference", headerName: "Commande", minWidth: 130, pinned: "left" },
    { field: "lot", headerName: "Lot", minWidth: 170, filter: "agSetColumnFilter" },
    { field: "supplier", headerName: "Fournisseur", minWidth: 170, filter: "agSetColumnFilter" },
    { field: "amount", headerName: "Montant", minWidth: 135, type: "numericColumn", valueFormatter: ({ value }) => formatMoney(value) },
    { field: "status", headerName: "Statut", minWidth: 125, filter: "agSetColumnFilter", cellClass: "grid-badge" },
    { field: "transportMode", headerName: "Transport", minWidth: 120, filter: "agSetColumnFilter" },
    { field: "etaDays", headerName: "ETA", minWidth: 95, type: "numericColumn", valueFormatter: ({ value }) => `${Math.round(Number(value || 0))} j` },
    { field: "risk", headerName: "Risque", minWidth: 120, filter: "agSetColumnFilter", cellClass: ({ value }) => riskClass(value) },
    { field: "priority", headerName: "Priorité", minWidth: 120, filter: "agSetColumnFilter" },
  ], []);

  return (
    <article className="appro-panel appro-orders-panel">
      <header className="appro-panel-header">
        <div>
          <span>Commandes</span>
          <strong>Portefeuille achat consolidé</strong>
        </div>
        <input
          value={quickFilterText}
          onChange={(event) => setQuickFilterText(event.target.value)}
          placeholder="Rechercher commande, lot, fournisseur..."
          aria-label="Filtrer les commandes approvisionnement"
        />
      </header>
      <SmartDataGrid
        rows={orders}
        columns={columns}
        height={500}
        quickFilterText={quickFilterText}
        onRowSelected={onSelect}
        rowHeight={44}
        headerHeight={42}
        rowClassRules={{
          "row-alert-critical": ({ data }) => data?.risk === "Critique",
          "row-alert-watch": ({ data }) => data?.risk === "Élevé",
        }}
      />
    </article>
  );
}
