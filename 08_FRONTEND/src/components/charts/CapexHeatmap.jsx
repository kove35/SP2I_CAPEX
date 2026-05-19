import React from "react";
import BIChart from "./BIChart";
import { formatMoney, formatPercent } from "../../shared/formatters";
import { useCrossFiltering } from "../../hooks/useCrossFiltering";
import { compactLabel, normalizeFamily, toBusinessLabel } from "../../utils/analyticsLabels";

const HEATMAP_MODES = [
  { key: "lot-famille", label: "Lot x famille", x: "lot", y: "famille" },
  { key: "batiment-niveau", label: "Batiment x niveau", x: "batiment", y: "niveau" },
  { key: "lot-risque", label: "Lot x risque", x: "lot", y: "risque_label" },
  { key: "lot-roi", label: "Lot x ROI", x: "lot", y: "roi_label" },
  { key: "lot-decision", label: "Lot x local/import", x: "lot", y: "decision_import" },
];

function riskLabel(value) {
  const score = Number(value || 0);
  if (score >= 70) return "Risque eleve";
  if (score >= 45) return "Risque moyen";
  return "Risque maitrise";
}

function roiLabel(value) {
  const roi = Number(value || 0);
  if (roi >= 0.15) return "ROI fort";
  if (roi >= 0.06) return "ROI moyen";
  return "ROI faible";
}

function normalizeDecision(value) {
  return String(value || "").toUpperCase() === "IMPORT" ? "IMPORT" : "LOCAL";
}

function rowValue(row = {}) {
  return Number(row.value || row.capex_optimise || row.capex_local || row.capex_brut || 0);
}

function normalizeRows(payload, rows = []) {
  const rawRows = rows.length ? rows : Array.isArray(payload) ? payload : [];
  return rawRows.map((row) => {
    const capexLocal = Number(row.capex_local || row.capex_brut || row.value || 0);
    const capexOptimise = Number(row.capex_optimise || row.value || capexLocal || 0);
    const economie = Number(row.economie || Math.max(capexLocal - capexOptimise, 0));
    const roi = Number(row.roi || row.taux_economie || (capexLocal ? economie / capexLocal : 0));
    const risque = Number(row.risque || row.criticite || row.global_risk_score || (normalizeDecision(row.decision_import) === "IMPORT" ? 58 : 32));
    return {
      ...row,
      lot: toBusinessLabel(row.lot || row.label, "Lot non renseigne"),
      famille: normalizeFamily(row.famille),
      batiment: toBusinessLabel(row.batiment, "Batiment non renseigne"),
      niveau: toBusinessLabel(row.niveau, "Niveau non renseigne"),
      decision_import: normalizeDecision(row.decision_import || row.decision),
      value: capexOptimise || capexLocal,
      capexLocal,
      economie,
      roi,
      risque,
      risque_label: riskLabel(risque),
      roi_label: roiLabel(roi),
    };
  });
}

function normalizeBackendPayload(payload) {
  if (!payload?.xLabels || !payload?.yLabels || !Array.isArray(payload?.data)) return null;
  const xLabels = payload.xLabels.map((label) => toBusinessLabel(label, "Lot non renseigne"));
  const yLabels = payload.yLabels.map((label) => normalizeFamily(label));
  const total = payload.data.reduce((sum, item) => sum + Number(item[2] || 0), 0) || 1;
  const data = payload.data.map((item) => {
    const value = Number(item[2] || 0);
    return {
      value: [Number(item[0]), Number(item[1]), value],
      capex: value,
      share: value / total,
      decision: "A arbitrer",
      risque: "A evaluer",
      roi: 0,
      filters: { lot: xLabels[Number(item[0])] || "", famille: yLabels[Number(item[1])] || "" },
    };
  });
  return {
    xLabels,
    yLabels,
    data,
    total,
    max: Number(payload.max || Math.max(...data.map((item) => item.value[2]), 1)),
  };
}

function buildHeatmap(payload, rows, modeKey) {
  if (modeKey === "lot-famille") {
    const backend = normalizeBackendPayload(payload);
    if (backend && !rows.length) return backend;
  }

  const mode = HEATMAP_MODES.find((item) => item.key === modeKey) || HEATMAP_MODES[0];
  const normalizedRows = normalizeRows(payload, rows);
  const groups = new Map();
  normalizedRows.forEach((row) => {
    const x = toBusinessLabel(row[mode.x], "Non renseigne");
    const y = mode.y === "famille" ? normalizeFamily(row[mode.y]) : toBusinessLabel(row[mode.y], "Non renseigne");
    const key = `${x}|${y}`;
    const current = groups.get(key) || {
      x,
      y,
      capex: 0,
      economie: 0,
      roiTotal: 0,
      riskTotal: 0,
      count: 0,
      importCount: 0,
    };
    current.capex += rowValue(row);
    current.economie += Number(row.economie || 0);
    current.roiTotal += Number(row.roi || 0);
    current.riskTotal += Number(row.risque || 0);
    current.importCount += row.decision_import === "IMPORT" ? 1 : 0;
    current.count += 1;
    groups.set(key, current);
  });

  const cells = [...groups.values()].sort((a, b) => b.capex - a.capex).slice(0, 180);
  const xLabels = [...new Set(cells.map((cell) => cell.x))].slice(0, 18);
  const yLabels = [...new Set(cells.map((cell) => cell.y))].slice(0, 14);
  const total = cells.reduce((sum, cell) => sum + cell.capex, 0) || 1;
  const data = cells
    .map((cell) => {
      const xIndex = xLabels.indexOf(cell.x);
      const yIndex = yLabels.indexOf(cell.y);
      const risk = cell.count ? cell.riskTotal / cell.count : 0;
      const roi = cell.count ? cell.roiTotal / cell.count : 0;
      return {
        value: [xIndex, yIndex, cell.capex],
        capex: cell.capex,
        share: cell.capex / total,
        decision: cell.importCount >= cell.count / 2 ? "IMPORT" : "LOCAL",
        risque: riskLabel(risk),
        roi,
        count: cell.count,
        filters: {
          [mode.x === "risque_label" || mode.x === "roi_label" ? "lot" : mode.x]: cell.x,
          [mode.y === "risque_label" || mode.y === "roi_label" ? "lot" : mode.y]: cell.y,
        },
      };
    })
    .filter((cell) => cell.value[0] >= 0 && cell.value[1] >= 0);
  return { xLabels, yLabels, data, total, max: Math.max(...data.map((cell) => cell.value[2]), 1) };
}

function buildInsights(heatmap) {
  const top = [...heatmap.data].sort((a, b) => b.capex - a.capex)[0];
  if (!top) return ["Aucune donnee budgetaire disponible pour cette carte."];
  const lot = heatmap.xLabels[top.value[0]];
  const family = heatmap.yLabels[top.value[1]];
  return [
    `${lot} concentre ${formatPercent(top.share)} du budget filtre.`,
    `${family} represente le metier dominant sur cette zone.`,
    top.decision === "IMPORT" ? "Potentiel d'optimisation import a analyser." : "Arbitrage local a surveiller pour securiser le planning.",
  ];
}

export default function CapexHeatmap({ data = [], rows = [] }) {
  const { applyFilters, applyDrilldown } = useCrossFiltering();
  const [mode, setMode] = React.useState("lot-famille");
  const heatmap = React.useMemo(() => buildHeatmap(data, rows, mode), [data, rows, mode]);
  const insights = React.useMemo(() => buildInsights(heatmap), [heatmap]);
  const chartKey = `heatmap-premium-${mode}-${heatmap.xLabels.join("|")}-${heatmap.yLabels.join("|")}-${heatmap.data.length}`;

  if (!heatmap.data.length) {
    return <div className="heatmap-empty-state">Aucune cartographie des couts disponible sur le perimetre filtre.</div>;
  }

  return (
    <div className="heatmap-decision-shell">
      <div className="heatmap-mode-row">
        {HEATMAP_MODES.map((item) => (
          <button key={item.key} type="button" className={mode === item.key ? "active" : ""} onClick={() => setMode(item.key)}>
            {item.label}
          </button>
        ))}
      </div>
      <div className="heatmap-insight-strip">
        {insights.map((insight) => <span key={insight}>{insight}</span>)}
      </div>
      <BIChart
        height={380}
        chartKey={chartKey}
        option={{
          backgroundColor: "transparent",
          animationDuration: 900,
          animationEasing: "cubicOut",
          tooltip: {
            backgroundColor: "rgba(7, 17, 31, .98)",
            borderColor: "rgba(103, 232, 201, .34)",
            extraCssText: "box-shadow:0 18px 42px rgba(0,0,0,.38);border-radius:12px;padding:12px;",
            textStyle: { color: "#f8fafc" },
            formatter: (params) => {
              const cell = params.data || {};
              const [x, y, value] = cell.value || [];
              return [
                `<b>Lot / axe: ${heatmap.xLabels[x] || "Non renseigne"}</b>`,
                `Famille / axe: <b>${heatmap.yLabels[y] || "Classification en attente"}</b>`,
                `Budget: <b>${formatMoney(value)}</b>`,
                `Part projet: <b>${formatPercent(cell.share || 0)}</b>`,
                `Decision: <b>${cell.decision || "A arbitrer"}</b>`,
                `Risque: <b>${cell.risque || "A evaluer"}</b>`,
                `ROI: <b>${formatPercent(cell.roi || 0)}</b>`,
                `Postes concernes: <b>${cell.count || "-"}</b>`,
                "Cliquer pour filtrer KPI, tableau et graphiques.",
              ].join("<br/>");
            },
          },
          grid: { left: 138, right: 26, top: 34, bottom: 96 },
          xAxis: {
            type: "category",
            data: heatmap.xLabels,
            axisLabel: { color: "#b7c8dd", rotate: heatmap.xLabels.length > 8 ? 32 : 0, fontSize: 10, interval: 0, formatter: (value) => compactLabel(value, 22) },
            axisLine: { lineStyle: { color: "rgba(148,163,184,.18)" } },
          },
          yAxis: {
            type: "category",
            data: heatmap.yLabels,
            axisLabel: { color: "#b7c8dd", fontSize: 10, formatter: (value) => compactLabel(value, 24) },
            axisLine: { lineStyle: { color: "rgba(148,163,184,.18)" } },
          },
          visualMap: {
            min: 0,
            max: Math.max(heatmap.max, 1),
            calculable: true,
            orient: "horizontal",
            left: "center",
            bottom: 12,
            text: ["Critique", "Faible"],
            textStyle: { color: "#9fb4d1", fontWeight: 800 },
            inRange: { color: ["#0f2a5f", "#0891b2", "#22c55e", "#facc15", "#f97316", "#dc2626"] },
            handleStyle: { color: "#67e8c9" },
          },
          series: [
            {
              type: "heatmap",
              data: heatmap.data,
              label: { show: false },
              progressive: 200,
              itemStyle: { borderColor: "rgba(2,6,23,.58)", borderWidth: 2, borderRadius: 3 },
              emphasis: {
                itemStyle: {
                  borderColor: "#f8fafc",
                  borderWidth: 1,
                  shadowBlur: 18,
                  shadowColor: "rgba(103,232,201,.48)",
                },
              },
            },
          ],
        }}
        onEvents={{
          click: (params) => {
            const cell = params?.data || {};
            const [x, y, value] = cell.value || [];
            const baseFilters = {
              ...cell.filters,
              lot: cell.filters?.lot || heatmap.xLabels[x] || "",
            };
            const filters = Object.fromEntries(
              Object.entries(baseFilters).filter(([, filterValue]) => filterValue && filterValue !== "Non renseigne")
            );
            applyFilters(filters);
            applyDrilldown(filters, {
              source: "heatmap",
              title: `Carte des couts - ${heatmap.xLabels[x]} / ${heatmap.yLabels[y]}`,
              metric: formatMoney(value || 0),
            });
          },
        }}
      />
    </div>
  );
}
