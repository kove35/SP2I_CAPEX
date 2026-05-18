import React from "react";
import BIChart from "./BIChart";
import { formatMoney, formatPercent } from "../../shared/formatters";
import { useCrossFiltering } from "../../hooks/useCrossFiltering";
import { analyticsColors } from "../../theme/colors";
import { chartTheme } from "../../theme/chartTheme";

function normalizeTimeline(data = []) {
  const rows = Array.isArray(data) ? data : [];
  if (!rows.length) {
    return [{ date: new Date().toISOString().slice(0, 10), capex: 0, economie: 0, roi: 0, risque: 0, scenario: "T0", jalon: "Initial" }];
  }
  return rows.map((row, index) => ({
    date: row.date || row.periode || `T${index}`,
    capex: Number(row.capex || row.capex_optimise || 0),
    economie: Number(row.economie || row.economie_nette || 0),
    roi: Number(row.roi || row.roi_import || 0),
    risque: Number(row.risque || row.risk || row.global_risk_score || 35),
    scenario: row.scenario || row.scenario_nom || (index === rows.length - 1 ? "Scenario actif" : "Historique"),
    jalon: row.jalon || row.event || "Point budget",
    nbLignes: Number(row.nb_lignes || 0),
  }));
}

function buildInsights(rows) {
  const last = rows[rows.length - 1] || {};
  const first = rows[0] || {};
  const capexDelta = Number(first.capex || 0) - Number(last.capex || 0);
  const riskDelta = Number(first.risque || 0) - Number(last.risque || 0);
  return [
    { label: "Budget reduit", value: formatMoney(capexDelta) },
    { label: "Economies cumulees", value: formatMoney(last.economie || 0) },
    { label: "ROI courant", value: formatPercent(last.roi || 0) },
    { label: "Risque reduit", value: `${Math.round(riskDelta)} pts` },
  ];
}

export default function CapexTimeline({ data = [] }) {
  const { applyDrilldown } = useCrossFiltering();
  const rows = React.useMemo(() => normalizeTimeline(data), [data]);
  const insights = React.useMemo(() => buildInsights(rows), [rows]);
  const dates = rows.map((row) => row.date);
  const capex = rows.map((row) => row.capex);
  const savings = rows.map((row) => row.economie);
  const roi = rows.map((row) => Number((row.roi * 100).toFixed(2)));
  const risk = rows.map((row) => row.risque);
  const milestones = rows.map((row, index) => ({
    coord: [row.date, row.capex],
    value: row.jalon,
    itemStyle: { color: index >= rows.length - 2 ? analyticsColors.amber : analyticsColors.cyan },
    label: { formatter: row.jalon, color: "#dbeafe", fontSize: 10 },
  }));

  return (
    <div className="timeline-enterprise-shell">
      <div className="timeline-insight-strip">
        {insights.map((item) => (
          <span key={item.label}>
            <strong>{item.value}</strong>
            {item.label}
          </span>
        ))}
      </div>
      <BIChart
        height={372}
        chartKey={`timeline-v2-${dates.join("|")}-${capex.join("|")}`}
        option={{
          backgroundColor: "transparent",
          animationDuration: 1000,
          tooltip: {
            ...chartTheme.tooltip,
            trigger: "axis",
            axisPointer: { type: "cross", label: { backgroundColor: "#0f172a" } },
            formatter: (params) => {
              const index = params?.[0]?.dataIndex ?? 0;
              const row = rows[index] || {};
              return [
                `<b>${row.date} - ${row.scenario}</b>`,
                `Jalon: <b>${row.jalon}</b>`,
                `Budget: <b>${formatMoney(row.capex)}</b>`,
                `Economies: <b>${formatMoney(row.economie)}</b>`,
                `ROI: <b>${formatPercent(row.roi)}</b>`,
                `Risque: <b>${Math.round(row.risque || 0)}/100</b>`,
                "Cliquer pour ouvrir l'etat projet a cette date",
              ].join("<br/>");
            },
          },
          legend: { top: 0, textStyle: { color: "#cbd5e1" } },
          grid: { left: 58, right: 54, top: 52, bottom: 78 },
          dataZoom: [
            { type: "inside", start: 0, end: 100 },
            { type: "slider", start: 0, end: 100, bottom: 18, height: 18, textStyle: { color: analyticsColors.muted } },
          ],
          xAxis: { type: "category", data: dates, boundaryGap: false, axisLabel: { ...chartTheme.axisLabel, rotate: 12 } },
          yAxis: [
            {
              type: "value",
              name: "Budget travaux",
              axisLabel: { color: analyticsColors.muted, formatter: (value) => `${Math.round(value / 1_000_000)}M` },
              splitLine: chartTheme.splitLine,
            },
            {
              type: "value",
              name: "ROI / risque",
              min: 0,
              max: 100,
              axisLabel: { color: analyticsColors.muted, formatter: (value) => `${Math.round(value)}%` },
              splitLine: { show: false },
            },
          ],
          series: [
            {
              name: "Budget",
              type: "line",
              smooth: true,
              data: capex,
              color: analyticsColors.blue,
              symbolSize: 10,
              areaStyle: { opacity: 0.16, color: analyticsColors.blue },
              markPoint: { symbolSize: 42, data: milestones },
              emphasis: { focus: "series" },
            },
            {
              name: "Economies cumulees",
              type: "line",
              smooth: true,
              data: savings,
              color: analyticsColors.green,
              symbolSize: 9,
              areaStyle: { opacity: 0.10, color: analyticsColors.green },
            },
            {
              name: "ROI",
              type: "line",
              yAxisIndex: 1,
              smooth: true,
              data: roi,
              color: analyticsColors.cyan,
              symbolSize: 8,
            },
            {
              name: "Risque",
              type: "line",
              yAxisIndex: 1,
              smooth: true,
              data: risk,
              color: analyticsColors.red,
              symbolSize: 8,
              lineStyle: { type: "dashed" },
            },
          ],
        }}
        onEvents={{
          click: (params) => {
            const row = rows[params?.dataIndex ?? 0];
            if (!row) return;
            applyDrilldown(
              { dateDebut: row.date, dateFin: row.date, scenario: row.scenario },
              {
                source: "timeline",
                title: `Etat projet - ${row.date} / ${row.scenario}`,
                metric: formatMoney(row.capex),
              }
            );
          },
        }}
      />
    </div>
  );
}
