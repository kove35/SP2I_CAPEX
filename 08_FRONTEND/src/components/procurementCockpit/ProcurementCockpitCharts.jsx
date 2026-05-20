import React from "react";
import BIChart from "../charts/BIChart";
import { formatMoney, formatPercent } from "../../shared/formatters";

const palette = ["#67e8c9", "#60a5fa", "#f59e0b", "#a78bfa", "#f87171", "#34d399"];

export function buildWaterfallOption(kpis = {}) {
  const items = [
    ["Budget initial", Number(kpis.capexBrut || 0), "#60a5fa"],
    ["Optimisation achat", -Number(kpis.gain || 0) * 0.48, "#34d399"],
    ["Import intelligent", -Number(kpis.gain || 0) * 0.36, "#67e8c9"],
    ["Risques & logistique", Number(kpis.gain || 0) * 0.12, "#f59e0b"],
    ["Budget optimise", Number(kpis.capexOptimise || 0), "#a78bfa"],
  ];
  let running = 0;
  return {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { top: 20, right: 16, bottom: 58, left: 52 },
    xAxis: { type: "category", data: items.map(([label]) => label), axisLabel: { color: "#9fb4d1", rotate: 18 } },
    yAxis: { type: "value", axisLabel: { color: "#9fb4d1", formatter: (value) => `${Math.round(value / 1000000)}M` }, splitLine: { lineStyle: { color: "rgba(148,163,184,.12)" } } },
    series: [
      {
        type: "bar",
        data: items.map(([label, value, color], index) => {
          running = index === 0 || index === items.length - 1 ? value : running + value;
          return { value: Math.abs(value), name: label, itemStyle: { color, borderRadius: [5, 5, 0, 0] }, raw: value, running };
        }),
        label: { show: true, position: "top", color: "#e5edf5", formatter: ({ data }) => formatMoney(Math.abs(data.raw)) },
      },
    ],
  };
}

export function buildHeatmapOption(rows = []) {
  const families = rows.slice(0, 12).map((row) => row.label);
  return {
    backgroundColor: "transparent",
    tooltip: { trigger: "item" },
    grid: { top: 18, right: 18, bottom: 62, left: 92 },
    xAxis: { type: "category", data: ["Anomalie", "Risque", "Confiance"], axisLabel: { color: "#9fb4d1" } },
    yAxis: { type: "category", data: families, axisLabel: { color: "#9fb4d1", width: 86, overflow: "truncate" } },
    visualMap: { min: 0, max: 100, show: false, inRange: { color: ["#0f766e", "#f59e0b", "#f87171"] } },
    series: [{
      type: "heatmap",
      data: rows.slice(0, 12).flatMap((row, y) => [
        [0, y, Math.min(100, row.anomalies * 18)],
        [1, y, Math.round(row.risk || 0)],
        [2, y, Math.round(100 - (row.confidence || 0))],
      ]),
      label: { show: true, color: "#f8fafc", fontSize: 10 },
    }],
  };
}

export function buildScenarioOption(rows = [], kpis = {}) {
  const scenarios = rows.length ? rows.slice(0, 6) : [
    { label: "Baseline", roi: kpis.roi, risk: kpis.riskScore, gain: kpis.gain },
    { label: "Conservateur", roi: kpis.roi * 0.75, risk: 28, gain: kpis.gain * 0.72 },
    { label: "Equilibre", roi: kpis.roi * 1.08, risk: 42, gain: kpis.gain * 1.08 },
    { label: "Agressif", roi: kpis.roi * 1.34, risk: 68, gain: kpis.gain * 1.26 },
  ];
  return {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis" },
    radar: { indicator: [
      { name: "ROI", max: 100 },
      { name: "Risque", max: 100 },
      { name: "Confiance", max: 100 },
      { name: "Gain", max: 100 },
      { name: "Delai", max: 100 },
    ], axisName: { color: "#9fb4d1" }, splitLine: { lineStyle: { color: "rgba(148,163,184,.18)" } }, splitArea: { areaStyle: { color: ["rgba(15,23,42,.2)", "rgba(15,23,42,.45)"] } } },
    series: [{
      type: "radar",
      data: scenarios.map((scenario, index) => ({
        name: scenario.label || scenario.code || `Scenario ${index + 1}`,
        value: [
          Math.min(100, Math.round(Number(scenario.roi || kpis.roi || 0) * 100)),
          Math.round(Number(scenario.risk || kpis.riskScore || 0)),
          Math.round(Number(scenario.confidence || kpis.financialConfidence || 70)),
          Math.min(100, Math.round(Number(scenario.gain || kpis.gain || 0) / Math.max(Number(kpis.gain || 1), 1) * 74)),
          Math.max(10, 100 - Math.round(Number(scenario.lead_time || 45))),
        ],
        areaStyle: { opacity: 0.08 },
        lineStyle: { width: 2 },
      })),
    }],
  };
}

export function buildBenchmarkOption(rows = []) {
  const data = rows.slice(0, 10);
  return {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis", formatter: (params) => params.map((p) => `${p.marker}${p.name}: ${formatPercent((p.value || 0) / 100)}`).join("<br/>") },
    grid: { top: 16, right: 22, bottom: 80, left: 36 },
    xAxis: { type: "category", data: data.map((row) => row.label), axisLabel: { color: "#9fb4d1", rotate: 30 } },
    yAxis: { type: "value", max: 100, axisLabel: { color: "#9fb4d1" }, splitLine: { lineStyle: { color: "rgba(148,163,184,.12)" } } },
    series: [
      { name: "Procurement", type: "bar", data: data.map((row) => Math.round(row.procurement || 0)), itemStyle: { color: palette[0], borderRadius: [5, 5, 0, 0] } },
      { name: "Confiance", type: "line", smooth: true, data: data.map((row) => Math.round(row.confidence || 0)), itemStyle: { color: palette[1] } },
    ],
  };
}

export function ChartPanel({ title, eyebrow, option, height = 300, onEvents }) {
  return (
    <article className="procurement-panel chart-panel">
      <header>
        <span>{eyebrow}</span>
        <strong>{title}</strong>
      </header>
      <BIChart
        option={option}
        height={height}
        chartKey={`${title}-${JSON.stringify(option?.series?.[0]?.data || []).length}`}
        onEvents={onEvents}
      />
    </article>
  );
}
