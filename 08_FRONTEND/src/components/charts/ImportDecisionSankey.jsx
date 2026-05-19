import React from "react";
import BIChart from "./BIChart";
import { formatMoney, formatPercent } from "../../shared/formatters";
import { useCrossFiltering } from "../../hooks/useCrossFiltering";
import { analyticsColors } from "../../theme/colors";
import { chartTheme } from "../../theme/chartTheme";
import { compactLabel, normalizeDecision, normalizeFamily, toBusinessLabel } from "../../utils/analyticsLabels";

const nodeColors = {
  CAPEX: analyticsColors.blue,
  Budget: analyticsColors.blue,
  IMPORT: analyticsColors.green,
  LOCAL: analyticsColors.amber,
};

function truncateLabel(label = "", size = 22) {
  return compactLabel(label, size);
}

function aggregateLinks(links = []) {
  const map = new Map();
  links.forEach((link) => {
    const source = link.source === "CAPEX" ? "Budget" : link.source;
    const target = link.target === "CAPEX" ? "Budget" : link.target;
    const key = `${source}|${target}`;
    const current = map.get(key) || { ...link, source, target, value: 0, economie: 0, gain: 0, roiTotal: 0, roiCount: 0, nb_lignes: 0 };
    current.value += Number(link.value || 0);
    current.economie += Number(link.economie || 0);
    current.gain += Number(link.gain || link.economie || 0);
    current.roiTotal += Number(link.roi || 0);
    current.roiCount += link.roi !== undefined ? 1 : 0;
    current.nb_lignes += Number(link.nb_lignes || 0);
    map.set(key, current);
  });
  return [...map.values()].map((link) => ({
    ...link,
    roi: link.roiCount ? link.roiTotal / link.roiCount : 0,
  }));
}

function buildFallbackLinks(rows = [], chartRows = []) {
  const sourceRows = rows.length ? rows : chartRows;
  const lotMap = sourceRows.reduce((acc, row) => {
    const lot = toBusinessLabel(row.lot || row.label, "Lot non renseigne");
    const decision = normalizeDecision(row.decision_import || row.decision || "IMPORT");
    const fournisseur = normalizeFamily(row.famille || "SP2I Supply");
    const key = `${decision}|${fournisseur}|${lot}`;
    const value = Math.max(Number(row.capex_optimise || row.capex_brut || row.value || 0), 1);
    const economie = Number(row.economie || row.economie_nette || 0);
    const current = acc.get(key) || { decision, fournisseur, lot, value: 0, economie: 0, roi: 0, delai: decision === "IMPORT" ? 75 : 14 };
    current.value += value;
    current.economie += economie;
    current.roi = current.value ? current.economie / current.value : 0;
    acc.set(key, current);
    return acc;
  }, new Map());

  return [...lotMap.values()].sort((a, b) => b.value - a.value).slice(0, 18).flatMap((row) => [
    { source: "Budget", target: row.decision, value: row.value, ...row },
    { source: row.decision, target: row.fournisseur, value: row.value, ...row },
    { source: row.fournisseur, target: row.lot, value: row.value, ...row },
  ]);
}

export default function ImportDecisionSankey({ rows = [], chartRows = [], sankeyRows = [] }) {
  const { applyDrilldown } = useCrossFiltering();
  const rawLinks = sankeyRows.length ? sankeyRows : buildFallbackLinks(rows, chartRows);
  const links = React.useMemo(() => aggregateLinks(rawLinks).filter((link) => Number(link.value || 0) > 0), [rawLinks]);
  const nodes = React.useMemo(() => {
    const names = [...new Set(links.flatMap((link) => [link.source, link.target]))];
    return names.map((name) => ({
      name,
      label: { formatter: truncateLabel(name) },
      itemStyle: { color: nodeColors[name] || (String(name).startsWith("L") ? analyticsColors.cyan : "#64748b") },
    }));
  }, [links]);
  const kpis = React.useMemo(() => {
    const terminal = links.filter((link) => !["CAPEX", "Budget"].includes(link.source) && link.target !== "IMPORT" && link.target !== "LOCAL");
    const total = terminal.reduce((sum, link) => sum + Number(link.value || 0), 0) || 1;
    const importTotal = terminal.filter((link) => link.decision === "IMPORT").reduce((sum, link) => sum + Number(link.value || 0), 0);
    const localTotal = terminal.filter((link) => link.decision === "LOCAL").reduce((sum, link) => sum + Number(link.value || 0), 0);
    const gain = terminal.reduce((sum, link) => sum + Number(link.gain || link.economie || 0), 0);
    const roi = terminal.length ? terminal.reduce((sum, link) => sum + Number(link.roi || 0), 0) / terminal.length : 0;
    return { importRate: importTotal / total, localRate: localTotal / total, gain, roi };
  }, [links]);
  const chartKey = `sankey-premium-${links.map((link) => `${link.source}-${link.target}-${Math.round(link.value)}`).join("|") || "empty"}`;

  return (
    <div className="premium-sankey-shell">
      <div className="sankey-kpi-strip">
        <span><strong>{formatPercent(kpis.importRate)}</strong> Import</span>
        <span><strong>{formatPercent(kpis.localRate)}</strong> Local</span>
        <span><strong>{formatMoney(kpis.gain)}</strong> Gain</span>
        <span><strong>{formatPercent(kpis.roi)}</strong> ROI moy.</span>
      </div>
      <BIChart
        height={330}
        chartKey={chartKey}
        option={{
          backgroundColor: "transparent",
          tooltip: {
            ...chartTheme.tooltip,
            trigger: "item",
            formatter: (params) => {
              const item = params.data || {};
              if (!item.source) return `<b>${params.name}</b><br/>Cliquer pour filtrer le cockpit.`;
              return [
                `<b>${item.source} -> ${item.target}</b>`,
                `Montant: <b>${formatMoney(item.value)}</b>`,
                `ROI: <b>${formatPercent(item.roi)}</b>`,
                `Gain net: <b>${formatMoney(item.gain || item.economie)}</b>`,
                `Famille/fournisseur: <b>${normalizeFamily(item.fournisseur || "SP2I Supply")}</b>`,
                `Decision: <b>${item.decision || item.target}</b>`,
                `Delai logistique: <b>${Math.round(Number(item.delai || 0))} j</b>`,
                "Cliquer pour synchroniser les indicateurs, les zones couteuses et les lignes budgetaires",
              ].join("<br/>");
            },
          },
          series: [
            {
              type: "sankey",
              top: 18,
              bottom: 12,
              left: 10,
              right: 18,
              nodeGap: 14,
              nodeWidth: 15,
              emphasis: { focus: "adjacency", blurScope: "coordinateSystem" },
              nodeAlign: "justify",
              draggable: false,
              lineStyle: { color: "gradient", opacity: 0.5, curveness: 0.58 },
              label: {
                color: "#dbeafe",
                fontSize: 11,
                overflow: "truncate",
                width: 118,
                formatter: ({ name }) => truncateLabel(name),
              },
              levels: [
                { depth: 0, itemStyle: { borderColor: analyticsColors.blue, borderWidth: 1 } },
                { depth: 1, itemStyle: { borderColor: analyticsColors.green, borderWidth: 1 } },
                { depth: 2, itemStyle: { borderColor: "#94a3b8", borderWidth: 1 } },
                { depth: 3, itemStyle: { borderColor: analyticsColors.cyan, borderWidth: 1 } },
              ],
              data: nodes,
              links,
            },
          ],
        }}
        onEvents={{
          click: (params) => {
            const name = params?.name;
            const link = params?.data || {};
            let filters = {};
            const selectedName = String(name || "");
            if (selectedName === "IMPORT" || selectedName === "LOCAL") filters = { importLocal: selectedName, decisionImport: selectedName };
            else if (link?.lot || selectedName.startsWith("L")) filters = { lot: link.lot || selectedName };
            else if (link?.fournisseur) filters = { famille: normalizeFamily(link.fournisseur) };
            else if (selectedName && !["Budget", "CAPEX"].includes(selectedName)) filters = { famille: normalizeFamily(selectedName) };
            if (Object.keys(filters).length) {
              applyDrilldown(filters, {
                source: "sankey",
                title: `Arbitrage ${link.source || "Budget"} -> ${link.target || name}`,
                metric: formatMoney(link.value || 0),
                path: ["Budget", link.decision || link.source, link.fournisseur, link.lot || selectedName].filter(Boolean),
                decision: link.decision || selectedName,
                selectedLabel: link.lot || link.fournisseur || selectedName,
                value: Number(link.value || 0),
                gain: Number(link.gain || link.economie || 0),
                roi: Number(link.roi || 0),
                delai: Number(link.delai || 0),
              });
            }
          },
        }}
      />
    </div>
  );
}
