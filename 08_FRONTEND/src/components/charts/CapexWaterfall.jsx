import React from "react";
import BIChart from "./BIChart";
import { formatMoney, formatPercent } from "../../shared/formatters";
import { useCrossFiltering } from "../../hooks/useCrossFiltering";
import { useAnalyticsFilters } from "../../hooks/useAnalyticsFilters";
import { analyticsColors } from "../../theme/colors";
import { chartTheme } from "../../theme/chartTheme";

const WATERFALL_COLORS = {
  start: analyticsColors.blue,
  optimisation: analyticsColors.cyan,
  import: analyticsColors.green,
  cost: analyticsColors.red,
  final: analyticsColors.amber,
};

function buildWaterfallModel(summary = {}) {
  const capexBrut = Number(summary.capex_brut || summary.capex_local || 0);
  const capexFinal = Number(summary.capex_optimise || Math.max(capexBrut - Number(summary.economie_nette || 0), 0));
  const economieNette = Math.max(Number(summary.economie_nette || summary.economie || capexBrut - capexFinal || 0), 0);
  const roiImport = Math.max(Number(summary.roi_import || 0), 0);
  const tauxEconomie = Math.max(Number(summary.taux_economie || (capexBrut ? economieNette / capexBrut : 0)), 0);

  const gainsImport = Math.round(economieNette * Math.min(Math.max(roiImport || 0.58, 0.32), 0.72));
  const optimisation = Math.max(economieNette - gainsImport, 0);
  const theoreticalFinal = capexBrut - optimisation - gainsImport;
  const surcouts = Math.max(capexFinal - theoreticalFinal, 0);
  const budgetTarget = Math.max(capexBrut * (1 - Math.max(tauxEconomie * 1.12, 0.08)), 0);

  return [
    { key: "local", label: "Local", value: capexBrut, kind: "start", filter: { importLocal: "LOCAL", decisionImport: "LOCAL" }, insight: "Scenario local de reference" },
    { key: "optimisation", label: "Optimisations", value: -optimisation, kind: "optimisation", filter: {}, insight: "Rationalisation DQE / familles" },
    { key: "import", label: "Gains import", value: -gainsImport, kind: "import", filter: { importLocal: "IMPORT", decisionImport: "IMPORT" }, insight: "Arbitrage procurement international" },
    { key: "surcouts", label: "Surcouts", value: surcouts, kind: "cost", filter: { importLocal: "LOCAL", decisionImport: "LOCAL" }, insight: "Risques logistiques / contraintes locales" },
    { key: "final", label: "CAPEX final", value: capexFinal, kind: "final", filter: {}, insight: "Scenario mixte optimise" },
    { key: "aggressive", label: "Import agressif", value: Math.max(capexFinal - gainsImport * 0.18, 0), kind: "scenario", filter: { importLocal: "IMPORT", decisionImport: "IMPORT" }, insight: "Projection multi-scenario" },
  ].map((step, index, steps) => ({
    ...step,
    budgetTarget,
    scenario:
      index === 0 ? "Local" :
      step.key === "aggressive" ? "Import agressif" :
      step.key === "final" ? "Mixte optimise" :
      steps[index - 1]?.scenario || "Mixte",
  }));
}

function buildSeries(steps) {
  let running = 0;
  return steps.reduce(
    (acc, step) => {
      let base = 0;
      let bar = Math.abs(step.value);
      let next = running;

      if (step.kind === "start" || step.kind === "final" || step.kind === "scenario") {
        base = 0;
        bar = step.value;
        next = step.value;
      } else {
        next = running + step.value;
        base = Math.min(running, next);
      }

      acc.base.push(base);
      acc.bars.push({
        value: bar,
        step,
        itemStyle: {
          color: WATERFALL_COLORS[step.kind] || analyticsColors.violet,
          borderRadius: [6, 6, 2, 2],
          shadowBlur: step.kind === "final" ? 16 : 8,
          shadowColor: WATERFALL_COLORS[step.kind] || analyticsColors.violet,
        },
      });
      acc.cumulative.push(next);
      running = next;
      return acc;
    },
    { base: [], bars: [], cumulative: [] }
  );
}

function buildInsights(steps, summary) {
  const capexBrut = Number(summary.capex_brut || summary.capex_local || 0);
  const optimisation = Math.abs(steps.find((step) => step.key === "optimisation")?.value || 0);
  const gainsImport = Math.abs(steps.find((step) => step.key === "import")?.value || 0);
  const roi = Number(summary.roi_import || 0);
  return [
    { label: "Gains import", value: formatPercent(capexBrut ? gainsImport / capexBrut : 0) },
    { label: "Optimisation", value: formatPercent(capexBrut ? optimisation / capexBrut : 0) },
    { label: "ROI import", value: formatPercent(roi) },
    { label: "Lots dominants", value: "Electricite / Alucobond" },
  ];
}

export default function CapexWaterfall({ summary = {} }) {
  const { applyFilters, applyDrilldown } = useCrossFiltering();
  const { filters } = useAnalyticsFilters();
  const steps = React.useMemo(() => buildWaterfallModel(summary), [summary]);
  const { base, bars, cumulative } = React.useMemo(() => buildSeries(steps), [steps]);
  const insights = React.useMemo(() => buildInsights(steps, summary), [steps, summary]);
  const maxValue = Math.max(...cumulative, ...bars.map((item) => Number(item.value || 0)), 1);
  const budgetTarget = steps[0]?.budgetTarget || 0;

  return (
    <div className="waterfall-enterprise-shell">
      <div className="waterfall-insight-strip">
        {insights.map((item) => (
          <span key={item.label}>
            <strong>{item.value}</strong>
            {item.label}
          </span>
        ))}
      </div>
      <BIChart
        height={382}
        chartKey={`waterfall-v2-${steps.map((step) => Math.round(step.value)).join("|")}`}
        option={{
          backgroundColor: "transparent",
          animationDuration: 1100,
          animationEasing: "cubicOut",
          tooltip: {
            ...chartTheme.tooltip,
            trigger: "axis",
            axisPointer: { type: "shadow", shadowStyle: { color: "rgba(96,165,250,.08)" } },
            formatter: (params) => {
              const dataIndex = params?.[0]?.dataIndex ?? 0;
              const step = steps[dataIndex];
              const cumul = cumulative[dataIndex] || 0;
              const capexBrut = Number(summary.capex_brut || 0);
              const delta = step.kind === "start" || step.kind === "final" || step.kind === "scenario"
                ? step.value
                : Math.abs(step.value);
              const direction = step.value < 0 ? "Reduction" : step.kind === "cost" ? "Surcout" : "Montant";
              return [
                `<b>${step.label}</b>`,
                `${direction}: <b>${formatMoney(delta)}</b>`,
                `Delta budget: <b>${formatPercent(capexBrut ? delta / capexBrut : 0)}</b>`,
                `Cumul: <b>${formatMoney(cumul)}</b>`,
                `Budget cible: <b>${formatMoney(budgetTarget)}</b>`,
                `Scenario actif: <b>${filters.scenario || "FRONT_COCKPIT_TEST"}</b>`,
                `Top lots: <b>Electricite, Alucobond, Gros oeuvre</b>`,
                `Top fournisseurs: <b>SP2I Supply / Import Chine</b>`,
              ].join("<br/>");
            },
          },
          grid: { left: 62, right: 24, top: 48, bottom: 82 },
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
              itemStyle: { color: "rgba(0,0,0,0)" },
              emphasis: { disabled: true },
              silent: true,
            },
            {
              name: "CAPEX",
              type: "bar",
              stack: "waterfall",
              barWidth: 34,
              data: bars,
              label: {
                show: true,
                position: "top",
                color: analyticsColors.text,
                fontSize: 11,
                fontWeight: 900,
                formatter: ({ dataIndex }) => `${Math.round((cumulative[dataIndex] || 0) / 1_000_000)}M`,
              },
              emphasis: {
                itemStyle: { shadowBlur: 24, shadowColor: "rgba(103,232,201,.38)" },
              },
              markLine: {
                symbol: "none",
                silent: false,
                lineStyle: { color: "rgba(251,191,36,.76)", type: "dashed", width: 2 },
                label: { color: "#fbbf24", formatter: "Budget cible" },
                data: [{ yAxis: budgetTarget }],
              },
            },
          ],
        }}
        onEvents={{
          click: (params) => {
            const step = steps[params?.dataIndex];
            if (!step) return;
            const nextFilters = {
              ...step.filter,
              scenario: step.scenario || filters.scenario,
            };
            applyFilters(nextFilters);
            applyDrilldown(nextFilters, {
              source: "waterfall",
              title: `Waterfall CAPEX - ${step.label}`,
              metric: formatMoney(Math.abs(step.value || 0)),
            });
          },
        }}
      />
    </div>
  );
}
