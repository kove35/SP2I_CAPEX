import React from "react";
import { AgGridReact } from "ag-grid-react";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-quartz.css";

export default function SmartDataGrid({ rows = [], columns = [], height = 420, quickFilterText = "", onRowSelected }) {
  const defaultColDef = React.useMemo(
    () => ({
      sortable: true,
      filter: true,
      resizable: true,
      floatingFilter: true,
      minWidth: 130,
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
        animateRows
        suppressCellFocus
        rowSelection="single"
        quickFilterText={quickFilterText}
        onRowClicked={(event) => onRowSelected?.(event.data)}
      />
    </div>
  );
}
