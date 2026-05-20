import React from "react";
import BIChart from "../charts/BIChart";
import { formatMoney, formatPercent } from "../../shared/formatters";

const palette = ["#67e8c9", "#60a5fa", "#f59e0b", "#a78bfa", "#f87171", "#34d399"];

function heatmapColor(value) {
  if (value >= 75) return "#ef4444";
  if (value >= 50) return "#f97316";
  if (value >= 25) return "#facc15";
  return "#22c55e";
}

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
  const points = rows.slice(0, 12).flatMap((row, y) => {
    const anomaly = Math.min(100, row.anomalies * 18);
    const risk = Math.round(row.risk || 0);
    const confidenceGap = Math.max(0, Math.round(100 - (row.confidence || 0)));
    return [
      { value: [0, y, anomaly], itemStyle: { color: heatmapColor(anomaly) }, context: row.label },
      { value: [1, y, risk], itemStyle: { color: heatmapColor(risk) }, context: row.label },
      { value: [2, y, confidenceGap], itemStyle: { color: heatmapColor(confidenceGap) }, context: row.label },
    ];
  });
  return {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      formatter: ({ data }) => {
        const metric = ["Anomalie", "Risque", "Confiance"][data?.value?.[0]] || "Signal";
        const value = data?.value?.[2] || 0;
        const level = value >= 75 ? "CRITICAL" : value >= 50 ? "WARNING" : value >= 25 ? "A surveiller" : "Stable";
        return `<b>${data?.context || ""}</b><br/>${metric}: ${value}/100<br/>Niveau: ${level}`;
      },
    },
    grid: { top: 24, right: 18, bottom: 70, left: 108 },
    xAxis: { type: "category", data: ["Anomalie", "Risque", "Confiance"], axisLabel: { color: "#9fb4d1" } },
    yAxis: { type: "category", data: families, axisLabel: { color: "#9fb4d1", width: 86, overflow: "truncate" } },
    visualMap: {
      min: 0,
      max: 100,
      orient: "horizontal",
      right: 8,
      bottom: 0,
      text: ["Critical", "Stable"],
      textStyle: { color: "#9fb4d1", fontSize: 10 },
      inRange: { color: ["#22c55e", "#facc15", "#f97316", "#ef4444"] },
    },
    series: [{
      type: "heatmap",
      data: points,
      emphasis: { itemStyle: { borderColor: "#f8fafc", borderWidth: 1 } },
      label: { show: true, color: "#07111f", fontSize: 10, fontWeight: 900 },
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
    tooltip: {
      trigger: "item",
      formatter: ({ name, value }) => `<b>${name}</b><br/>ROI: ${value?.[0] || 0}/100<br/>Risque: ${value?.[1] || 0}/100<br/>Confiance: ${value?.[2] || 0}/100<br/>Gain: ${value?.[3] || 0}/100`,
    },
    legend: { top: 0, right: 0, textStyle: { color: "#9fb4d1", fontSize: 11 } },
    radar: { indicator: [
      { name: "ROI", max: 100 },
      { name: "Risque", max: 100 },
      { name: "Confiance", max: 100 },
      { name: "Gain", max: 100 },
      { name: "Delai", max: 100 },
    ], radius: "66%", center: ["50%", "56%"], axisName: { color: "#dbeafe", fontSize: 12, fontWeight: 700 }, splitLine: { lineStyle: { color: "rgba(148,163,184,.22)" } }, axisLine: { lineStyle: { color: "rgba(148,163,184,.22)" } }, splitArea: { areaStyle: { color: ["rgba(15,23,42,.18)", "rgba(15,23,42,.48)"] } } },
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
        areaStyle: { opacity: index === 2 ? 0.14 : 0.07 },
        lineStyle: { width: index === 2 ? 3 : 2 },
        symbolSize: 5,
      })),
      animationDuration: 650,
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
        chartKey={`${title}-${option?.series?.[0]?.data?.length || 0}`}
        onEvents={onEvents}
      />
    </article>
  );
}
