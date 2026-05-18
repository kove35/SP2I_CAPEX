import React from "react";
import BIChart from "./BIChart";
import { formatMoney, formatPercent } from "../../shared/formatters";
import { useCrossFiltering } from "../../hooks/useCrossFiltering";
import { analyticsColors } from "../../theme/colors";
import { chartTheme } from "../../theme/chartTheme";

function buildWaterfallSteps(summary = {}) {
  const capexBrut = Number(summary.capex_brut || summary.capex_local || 0);
  const capexFinalRaw = Number(summary.capex_optimise || 0);
  const economieTotale = Math.max(Number(summary.economie || summary.economie_nette || capexBrut - capexFinalRaw || 0), 0);
  const capexFinal = capexFinalRaw || Math.max(capexBrut - economieTotale, 0);
  const gainImport = Math.round(economieTotale * 0.58);
  const optimisation = Math.max(economieTotale - gainImport, 0);
  const surcouts = Math.max(capexFinal - (capexBrut - optimisation - gainImport), 0);

  return [
    { key: "capex_brut", label: "CAPEX brut", value: capexBrut, kind: "start", filter: {} },
    { key: "optimisations", label: "Optimisations", value: -optimisation, kind: "saving", filter: { importLocal: "" } },
    { key: "gains_import", label: "Gains import", value: -gainImport, kind: "saving", filter: { importLocal: "IMPORT", decisionImport: "IMPORT" } },
    { key: "surcouts", label: "Surcouts", value: surcouts, kind: "cost", filter: { importLocal: "LOCAL", decisionImport: "LOCAL" } },
    { key: "capex_final", label: "CAPEX final", value: capexFinal, kind: "end", filter: {} },
  ];
}

function toWaterfallSeries(steps) {
  let running = 0;
  const base = [];
  const bars = [];
  const cumulative = [];

  steps.forEach((step, index) => {
    if (step.kind === "start") {
      base.push(0);
      bars.push(step.value);
      running = step.value;
    } else if (step.kind === "end") {
      base.push(0);
      bars.push(step.value);
      running = step.value;
    } else {
      const next = running + step.value;
      base.push(Math.min(running, next));
      bars.push(Math.abs(step.value));
      running = next;
    }
    cumulative.push(running);
  });

  return { base, bars, cumulative };
}

export default function CapexWaterfall({ summary = {} }) {
  const { applyFilters } = useCrossFiltering();
  const steps = React.useMemo(() => buildWaterfallSteps(summary), [summary]);
  const { base, bars, cumulative } = React.useMemo(() => toWaterfallSeries(steps), [steps]);
  const capexBrut = Number(summary.capex_brut || summary.capex_local || 0);
  const maxValue = Math.max(...cumulative, ...bars, 1);

  return (
    <BIChart
      height={350}
      chartKey={`waterfall-${steps.map((step) => step.value).join("|")}`}
      option={{
        backgroundColor: "transparent",
        animationDuration: 900,
        animationEasing: "cubicOut",
        tooltip: {
          ...chartTheme.tooltip,
          trigger: "axis",
          axisPointer: { type: "shadow" },
          formatter: (params) => {
            const dataIndex = params?.[0]?.dataIndex ?? 0;
            const step = steps[dataIndex];
            const cumulativeValue = cumulative[dataIndex];
            const deltaRate = capexBrut ? Math.abs(step.value) / capexBrut : 0;
            const direction = step.value < 0 ? "Reduction" : step.kind === "cost" ? "Surcout" : "Base";
            return [
              `<b>${step.label}</b>`,
              `${direction}: <b>${formatMoney(Math.abs(step.value))}</b>`,
              `Delta: <b>${formatPercent(deltaRate)}</b>`,
              `Cumul: <b>${formatMoney(cumulativeValue)}</b>`,
              step.key === "gains_import" ? "Drill-down: decisions IMPORT et top economies" : "Drill-down: detail FACT_METRE",
            ].join("<br/>");
          },
        },
        grid: { left: 58, right: 24, top: 42, bottom: 72 },
        xAxis: {
          type: "category",
          data: steps.map((step) => step.label),
          axisLabel: { color: analyticsColors.muted, rotate: 18, fontSize: 11, interval: 0 },
          axisLine: { lineStyle: { color: "rgba(148,163,184,.18)" } },
        },
        yAxis: {
          type: "value",
          max: Math.ceil(maxValue * 1.12),
          axisLabel: { color: analyticsColors.muted, formatter: (value) => `${Math.round(value / 1_000_000)}M` },
          splitLine: chartTheme.splitLine,
        },
        series: [
          {
            name: "Offset",
            type: "bar",
            stack: "waterfall",
            data: base,
            itemStyle: { color: "transparent" },
            emphasis: { itemStyle: { color: "transparent" } },
            silent: true,
          },
          {
            name: "Variation",
            type: "bar",
            stack: "waterfall",
            barWidth: 34,
            data: bars.map((value, index) => {
              const step = steps[index];
              const color =
                step.kind === "start" ? analyticsColors.blue :
                step.kind === "end" ? analyticsColors.amber :
                step.kind === "cost" ? "#f97316" :
                analyticsColors.green;
              return { value, itemStyle: { color, borderRadius: [5, 5, 2, 2] } };
            }),
            label: {
              show: true,
              position: "top",
              color: analyticsColors.text,
              fontSize: 11,
              fontWeight: 900,
              formatter: ({ dataIndex }) => `${Math.round(cumulative[dataIndex] / 1_000_000)}M`,
            },
            markLine: {
              symbol: "none",
              silent: true,
              lineStyle: { color: "rgba(148,163,184,.24)", type: "dashed" },
              data: [{ yAxis: cumulative[cumulative.length - 1] || 0, label: { formatter: "CAPEX final", color: "#fbbf24" } }],
            },
          },
        ],
      }}
      onEvents={{
        click: (params) => {
          const step = steps[params?.dataIndex];
          if (step?.filter) applyFilters(step.filter);
        },
      }}
    />
  );
}
