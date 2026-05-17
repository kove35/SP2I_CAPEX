import React from "react";
import { Download, Maximize2 } from "lucide-react";
import SmartDataGrid from "./SmartDataGrid";
import { formatMoney, formatPercent } from "../../shared/formatters";
import { useDashboardStore } from "../../store/dashboardStore";

export default function FactMetreGrid({ rows = [], total = 0 }) {
  const setFilters = useDashboardStore((state) => state.setFilters);
  const [quickSearch, setQuickSearch] = React.useState("");
  const [fullscreen, setFullscreen] = React.useState(false);

  const columns = React.useMemo(
    () => [
      { field: "lot", headerName: "Lot", minWidth: 220, rowGroup: false },
      { field: "famille", headerName: "Famille", minWidth: 150 },
      { field: "batiment", headerName: "Bâtiment", minWidth: 170 },
      { field: "niveau", headerName: "Niveau", minWidth: 140 },
      { field: "designation", headerName: "Désignation", flex: 1, minWidth: 300 },
      { field: "decision_import", headerName: "Décision", minWidth: 125 },
      { field: "capex_local", headerName: "CAPEX brut", valueFormatter: ({ value }) => formatMoney(value), type: "numericColumn" },
      { field: "capex_optimise", headerName: "Optimisé", valueFormatter: ({ value }) => formatMoney(value), type: "numericColumn" },
      { field: "economie", headerName: "Economie", valueFormatter: ({ value }) => formatMoney(value), type: "numericColumn" },
      { field: "taux_economie", headerName: "Taux", valueFormatter: ({ value }) => formatPercent(value), type: "numericColumn" },
    ],
    []
  );

  return (
    <section className={fullscreen ? "fact-grid-shell fullscreen" : "fact-grid-shell"}>
      <header className="fact-grid-toolbar">
        <div>
          <strong>{Number(total || rows.length).toLocaleString("fr-FR")} lignes FACT_METRE</strong>
          <span>AG Grid connecté à Analytics Engine V1</span>
        </div>
        <input value={quickSearch} onChange={(event) => setQuickSearch(event.target.value)} placeholder="Recherche rapide" />
        <button type="button" onClick={() => setFullscreen((value) => !value)}>
          <Maximize2 size={15} />
          Plein écran
        </button>
        <button type="button" onClick={() => window.alert("Export Excel AG Grid prêt pour l'industrialisation.")}>
          <Download size={15} />
          Export
        </button>
      </header>
      <SmartDataGrid
        rows={rows}
        columns={columns}
        height={fullscreen ? 720 : 470}
        quickFilterText={quickSearch}
        onRowSelected={(row) => setFilters({ lot: row.lot, famille: row.famille, batiment: row.batiment, niveau: row.niveau })}
      />
    </section>
  );
}
