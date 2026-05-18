import React from "react";
import { Download, FileText, Maximize2, Printer, Sparkles } from "lucide-react";
import SmartDataGrid from "./SmartDataGrid";
import { formatMoney, formatPercent } from "../../shared/formatters";
import { useCrossFiltering } from "../../hooks/useCrossFiltering";
import { useAnalyticsFilterStore } from "../../stores/analyticsFilterStore";
import { normalizeDecision, normalizeFamily, toBusinessLabel } from "../../utils/analyticsLabels";

const exportKeys = ["lot", "famille", "batiment", "niveau", "designation", "decision_import", "capex_local", "capex_optimise", "economie", "taux_economie"];

function normalizeRow(row = {}) {
  const decision = normalizeDecision(row.decision_import || row.decision);
  const capexLocal = Number(row.capex_local || row.capex_brut || 0);
  const capexOptimise = Number(row.capex_optimise || capexLocal || 0);
  const economie = Number(row.economie || Math.max(capexLocal - capexOptimise, 0));
  const roi = capexOptimise ? economie / capexOptimise : 0;
  return {
    ...row,
    lot: toBusinessLabel(row.lot, "Lot non renseigne"),
    famille: normalizeFamily(row.famille),
    batiment: toBusinessLabel(row.batiment, "Batiment non renseigne"),
    niveau: toBusinessLabel(row.niveau, "Niveau non renseigne"),
    designation: toBusinessLabel(row.designation, "Designation non renseignee"),
    decision_import: decision,
    capex_local: capexLocal,
    capex_optimise: capexOptimise,
    economie,
    taux_economie: Number(row.taux_economie || (capexLocal ? economie / capexLocal : 0)),
    roi,
    fournisseur: row.fournisseur || row.famille || "SP2I Supply",
    delai: Number(row.delai || (decision === "IMPORT" ? 75 : 14)),
    risque: Number(row.risque || row.criticite || (decision === "IMPORT" ? 58 : 32)),
    statut_achat: row.statut_achat || (decision === "IMPORT" ? "A arbitrer" : "Local securise"),
  };
}

function toCsv(rows) {
  if (!rows.length) return "";
  const escape = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
  return [exportKeys.join(";"), ...rows.map((row) => exportKeys.map((key) => escape(row[key])).join(";"))].join("\n");
}

function downloadBlob(content, filename, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function buildExcelHtml(rows) {
  const headers = exportKeys.map((key) => `<th>${key}</th>`).join("");
  const body = rows
    .map((row) => `<tr>${exportKeys.map((key) => `<td>${String(row[key] ?? "")}</td>`).join("")}</tr>`)
    .join("");
  return `<html><meta charset="utf-8"><body><table border="1"><thead><tr>${headers}</tr></thead><tbody>${body}</tbody></table></body></html>`;
}

function buildDecisionReport(rows, metrics, selectedRow) {
  return JSON.stringify(
    {
      generated_at: new Date().toISOString(),
      scope: "SP2I analyse operationnelle des lignes budgetaires",
      metrics,
      selected_line: selectedRow,
      opportunities: rows
        .filter((row) => row.decision_import === "IMPORT")
        .sort((a, b) => b.economie - a.economie)
        .slice(0, 10)
        .map((row) => ({ lot: row.lot, designation: row.designation, economie: row.economie, roi: row.roi })),
      risks: rows
        .filter((row) => row.risque >= 55)
        .slice(0, 10)
        .map((row) => ({ lot: row.lot, designation: row.designation, risque: row.risque, delai: row.delai })),
    },
    null,
    2
  );
}

export default function FactMetreGrid({ rows = [], total = 0 }) {
  const { applyFilters, applyDrilldown } = useCrossFiltering();
  const drilldownTarget = useAnalyticsFilterStore((state) => state.drilldownTarget);
  const clearDrilldown = useAnalyticsFilterStore((state) => state.clearDrilldown);
  const [quickSearch, setQuickSearch] = React.useState("");
  const [fullscreen, setFullscreen] = React.useState(false);
  const [selectedRow, setSelectedRow] = React.useState(null);
  const normalizedRows = React.useMemo(() => rows.map(normalizeRow), [rows]);
  const metrics = React.useMemo(() => {
    const source = selectedRow ? [selectedRow] : normalizedRows;
    const importRows = source.filter((row) => row.decision_import === "IMPORT").length;
    const localRows = source.filter((row) => row.decision_import === "LOCAL").length;
    const capex = source.reduce((sum, row) => sum + Number(row.capex_local || 0), 0);
    const savings = source.reduce((sum, row) => sum + Number(row.economie || 0), 0);
    const roi = source.length ? source.reduce((sum, row) => sum + Number(row.roi || 0), 0) / source.length : 0;
    return { lignes: source.length, importRows, localRows, capex, savings, roi };
  }, [normalizedRows, selectedRow]);

  const columns = React.useMemo(
    () => [
      { field: "lot", headerName: "Lot", minWidth: 210, pinned: "left", tooltipField: "lot" },
      { field: "designation", headerName: "Designation", flex: 1, minWidth: 310, pinned: "left", tooltipField: "designation" },
      {
        field: "decision_import",
        headerName: "Decision",
        minWidth: 124,
        pinned: "left",
        cellRenderer: ({ value }) => <span className={`decision-badge ${String(value || "").toLowerCase()}`}>{value || "LOCAL"}</span>,
        tooltipValueGetter: ({ data }) => `${data?.statut_achat || "Statut achat"} - delai ${data?.delai || 0} j`,
      },
      { field: "famille", headerName: "Famille", minWidth: 160, tooltipField: "famille" },
      { field: "batiment", headerName: "Batiment", minWidth: 170 },
      { field: "niveau", headerName: "Niveau", minWidth: 140 },
      { field: "fournisseur", headerName: "Fournisseur", minWidth: 160 },
      { field: "delai", headerName: "Delai", minWidth: 95, valueFormatter: ({ value }) => `${Math.round(Number(value || 0))} j`, type: "numericColumn" },
      { field: "risque", headerName: "Risque", minWidth: 105, valueFormatter: ({ value }) => `${Math.round(Number(value || 0))}/100`, type: "numericColumn" },
      { field: "capex_local", headerName: "Budget initial", valueFormatter: ({ value }) => formatMoney(value), type: "numericColumn", tooltipValueGetter: ({ value }) => formatMoney(value) },
      { field: "capex_optimise", headerName: "Budget optimise", valueFormatter: ({ value }) => formatMoney(value), type: "numericColumn" },
      { field: "economie", headerName: "Economie", valueFormatter: ({ value }) => formatMoney(value), type: "numericColumn" },
      { field: "roi", headerName: "ROI", valueFormatter: ({ value }) => formatPercent(value), type: "numericColumn" },
      { field: "taux_economie", headerName: "Taux", valueFormatter: ({ value }) => formatPercent(value), type: "numericColumn" },
    ],
    []
  );

  const exportCsv = () => downloadBlob(toCsv(normalizedRows), "sp2i_lignes_budgetaires.csv", "text/csv;charset=utf-8");
  const exportExcel = () => downloadBlob(buildExcelHtml(normalizedRows), "sp2i_lignes_budgetaires.xls", "application/vnd.ms-excel;charset=utf-8");
  const exportReport = () => downloadBlob(buildDecisionReport(normalizedRows, metrics, selectedRow), "sp2i_rapport_decisionnel.json", "application/json;charset=utf-8");
  const printSnapshot = () => window.print();

  const handleRowSelected = (row) => {
    setSelectedRow(row);
    const filters = { lot: row.lot, famille: row.famille, batiment: row.batiment, niveau: row.niveau, importLocal: row.decision_import, decisionImport: row.decision_import };
    applyFilters(filters);
    applyDrilldown(filters, {
      source: "ag-grid",
      title: `Ligne ${row.lot} - ${row.designation}`,
      metric: formatMoney(row.capex_local),
    });
  };

  return (
    <section className={fullscreen ? "fact-grid-shell fullscreen" : "fact-grid-shell"} data-fact-metre-grid>
      <header className="fact-grid-toolbar sticky">
        <div>
          <strong>{Number(total || normalizedRows.length).toLocaleString("fr-FR")} lignes budgetaires</strong>
          <span>Centre operationnel connecte au moteur de pilotage SP2I</span>
        </div>
        <div className="fact-grid-metrics">
          <span>Selection {metrics.lignes}</span>
          <span>Budget {formatMoney(metrics.capex)}</span>
          <span>ROI {formatPercent(metrics.roi)}</span>
          <span>Gain {formatMoney(metrics.savings)}</span>
          <span>IMPORT {metrics.importRows}</span>
          <span>LOCAL {metrics.localRows}</span>
        </div>
        <input value={quickSearch} onChange={(event) => setQuickSearch(event.target.value)} placeholder="Recherche rapide" />
        <button type="button" onClick={() => setFullscreen((value) => !value)}><Maximize2 size={15} />Plein ecran</button>
        <button type="button" onClick={exportCsv}><Download size={15} />CSV</button>
        <button type="button" onClick={exportExcel}><Download size={15} />Excel</button>
        <button type="button" onClick={exportReport}><FileText size={15} />Rapport</button>
        <button type="button" onClick={printSnapshot}><Printer size={15} />Snapshot</button>
      </header>
      {drilldownTarget ? (
        <div className="fact-grid-drilldown">
          <div>
          <span>Analyse detaillee active</span>
            <strong>{drilldownTarget.title}</strong>
            {drilldownTarget.metric ? <small>{drilldownTarget.metric}</small> : null}
          </div>
          <button type="button" onClick={clearDrilldown}>Fermer</button>
        </div>
      ) : null}
      <div className="fact-grid-body">
        <SmartDataGrid
          rows={normalizedRows}
          columns={columns}
          height={fullscreen ? 690 : 460}
          quickFilterText={quickSearch}
          onRowSelected={handleRowSelected}
          getRowClass={({ data }) => (selectedRow?.id_ligne && data?.id_ligne === selectedRow.id_ligne ? "sp2i-row-selected" : "")}
          rowClassRules={{
            "sp2i-row-import": ({ data }) => data?.decision_import === "IMPORT",
            "sp2i-row-risk": ({ data }) => Number(data?.risque || 0) >= 60,
          }}
        />
        <aside className="fact-line-detail">
          <div className="line-detail-header">
            <Sparkles size={16} />
            <span>Copilote operationnel</span>
          </div>
          {selectedRow ? (
            <>
              <strong>{selectedRow.designation}</strong>
              <dl>
                <div><dt>Budget</dt><dd>{formatMoney(selectedRow.capex_local)}</dd></div>
                <div><dt>Gain</dt><dd>{formatMoney(selectedRow.economie)}</dd></div>
                <div><dt>ROI</dt><dd>{formatPercent(selectedRow.roi)}</dd></div>
                <div><dt>Fournisseur</dt><dd>{selectedRow.fournisseur}</dd></div>
                <div><dt>Delai</dt><dd>{selectedRow.delai} j</dd></div>
                <div><dt>Risque</dt><dd>{Math.round(selectedRow.risque)}/100</dd></div>
              </dl>
              <p>
                {selectedRow.decision_import === "IMPORT"
                  ? "Opportunite import a challenger: verifier incoterm, delai maritime et risque fournisseur avant validation."
                  : "Option locale stable: utile pour securiser le planning ou reduire le risque logistique."}
              </p>
            </>
          ) : (
            <p>Selectionner une ligne pour afficher ROI, risque, alternatives import/local et recommandation SP2I.</p>
          )}
        </aside>
      </div>
    </section>
  );
}
