import React from "react";
import { AgGridReact } from "ag-grid-react";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-quartz.css";
import { agGridLocaleFr } from "../../utils/agGridLocaleFr";

export default function SmartDataGrid({
  rows = [],
  columns = [],
  height = 420,
  quickFilterText = "",
  onRowSelected,
  getRowClass,
  rowClassRules,
}) {
  const defaultColDef = React.useMemo(
    () => ({
      sortable: true,
      filter: true,
      resizable: true,
      floatingFilter: true,
      minWidth: 130,
      filterParams: {
        buttons: ["reset", "apply"],
        closeOnApply: true,
        debounceMs: 250,
      },
    }),
    []
  );

  return (
    <div className="ag-theme-quartz-dark sp2i-grid" style={{ height }}>
      <AgGridReact
        rowData={rows}
        columnDefs={columns}
        defaultColDef={defaultColDef}
        pagination
        paginationPageSize={25}
        paginationPageSizeSelector={[25, 50, 100]}
        localeText={agGridLocaleFr}
        overlayNoRowsTemplate='<span class="sp2i-grid-empty">Aucune ligne budgetaire a afficher</span>'
        overlayLoadingTemplate='<span class="sp2i-grid-empty">Chargement des donnees projet...</span>'
        animateRows
        suppressCellFocus
        rowSelection={{ mode: "singleRow" }}
        quickFilterText={quickFilterText}
        getRowClass={getRowClass}
        rowClassRules={rowClassRules}
        onRowClicked={(event) => onRowSelected?.(event.data)}
      />
    </div>
  );
}
