import React, { useMemo } from "react";
import BIChart from "./BIChart";
import { formatMoney } from "../../shared/formatters";
import { useCrossFiltering } from "../../hooks/useCrossFiltering";
import { analyticsColors } from "../../theme/colors";
import { chartTheme } from "../../theme/chartTheme";

const MILLION = 1_000_000;

function riskColor(value) {
  if (value >= 72) return analyticsColors.red;
  if (value >= 55) return analyticsColors.amber;
  return analyticsColors.green;
}

function normalizeRiskRow(row, index) {
  const impact = Number(row.impact || row.capex_local || row.value || row.capex_brut || 0);
  const capexExpose = Number(row.capex_expose || row.capex_optimise || impact || 1);
  const probabilite = Number(row.probabilite || row.global_risk_score || 35 + index);
  const criticite = Number(row.criticite || probabilite);
  const lot = row.lot || row.label || `Risque ${index + 1}`;
  const fournisseur = row.fournisseur || row.famille || "SP2I Supply";
  const decision = row.decision_import || row.decision || "LOCAL";
  return {
    lot,
    fournisseur,
    decision,
    impact,
    capexExpose,
    probabilite: Math.min(Math.max(probabilite, 5), 100),
    criticite: Math.min(Math.max(criticite, 5), 100),
    delai: Number(row.delai || (decision === "IMPORT" ? 75 : 14)),
    risqueType: row.risque_type || (criticite >= 72 ? "Critique" : "Surveillance"),
    economie: Number(row.economie || 0),
    nbLignes: Number(row.nb_lignes || 0),
  };
}

function buildInsight(rows) {
  const sorted = [...rows].sort((a, b) => b.criticite - a.criticite);
  const critical = rows.filter((row) => row.criticite >= 72);
  const exposed = rows.reduce((sum, row) => sum + row.capexExpose, 0);
  const top = sorted[0];
  return {
    top,
    criticalCount: critical.length,
    exposed,
    recommendation: top
      ? `${top.lot} concentre la priorite risque: arbitrer ${top.decision} et securiser le delai.`
      : "Aucun risque prioritaire detecte sur le perimetre filtre.",
  };
}

export default function RiskMatrix({ rows = [] }) {
  const { applyFilters } = useCrossFiltering();
  const riskRows = useMemo(() => rows.slice(0, 72).map(normalizeRiskRow), [rows]);
  const insight = useMemo(() => buildInsight(riskRows), [riskRows]);
  const maxImpactM = Math.max(...riskRows.map((row) => row.impact / MILLION), 10);
  const xThreshold = maxImpactM * 0.5;

  const data = riskRows.map((row) => ({
    value: [
      Number((row.impact / MILLION).toFixed(2)),
      row.probabilite,
      Number((row.capexExpose / MILLION).toFixed(2)),
      row.lot,
      row.criticite,
      row.fournisseur,
      row.delai,
      row.decision,
      row.risqueType,
      row.impact,
      row.economie,
      row.nbLignes,
    ],
    itemStyle: {
      color: riskColor(row.criticite),
      opacity: 0.9,
      shadowBlur: row.criticite >= 72 ? 18 : 9,
      shadowColor: riskColor(row.criticite),
    },
  }));

  return (
    <div className="risk-matrix-shell">
      <div className="risk-insight-strip">
        <article>
          <span>Priorite</span>
          <strong>{insight.top?.lot || "Aucun risque"}</strong>
        </article>
        <article>
          <span>CAPEX expose</span>
          <strong>{formatMoney(insight.exposed)}</strong>
        </article>
        <article>
          <span>Alertes critiques</span>
          <strong>{insight.criticalCount} zones</strong>
        </article>
      </div>
      <BIChart
        height={360}
        option={{
          backgroundColor: "transparent",
          tooltip: {
            ...chartTheme.tooltip,
            formatter: (params) => {
              const value = params.data.value;
              return [
                `<b>${value[3]}</b>`,
                `Impact: <b>${formatMoney(value[9])}</b>`,
                `Criticite: <b>${Math.round(value[4])}/100</b>`,
                `Probabilite: <b>${Math.round(value[1])}/100</b>`,
                `Risque: <b>${value[8]}</b>`,
                `Fournisseur/famille: <b>${value[5]}</b>`,
                `Delai: <b>${value[6]} j</b>`,
                `Decision: <b>${value[7]}</b>`,
              ].join("<br/>");
            },
          },
          grid: { left: 54, right: 30, top: 30, bottom: 52 },
          xAxis: {
            name: "Impact financier (M FCFA)",
            min: 0,
            max: Math.ceil(maxImpactM * 1.15),
            axisLabel: { ...chartTheme.axisLabel, formatter: (value) => `${Math.round(value)}M` },
            splitLine: chartTheme.splitLine,
          },
          yAxis: {
            name: "Probabilite / criticite",
            min: 0,
            max: 100,
            axisLabel: chartTheme.axisLabel,
            splitLine: chartTheme.splitLine,
          },
          series: [
            {
              type: "scatter",
              data,
              symbolSize: (value) => Math.min(Math.max(Math.sqrt(value[2]) * 2.4, 10), 48),
              emphasis: {
                focus: "self",
                scale: 1.25,
                label: {
                  show: true,
                  formatter: (params) => String(params.data.value[3]).slice(0, 28),
                  color: "#f8fafc",
                  fontWeight: 900,
                },
              },
              label: {
                show: true,
                formatter: (params) => (params.data.value[4] >= 72 ? String(params.data.value[3]).slice(0, 14) : ""),
                color: "#dbeafe",
                fontSize: 10,
                fontWeight: 800,
              },
              markLine: {
                silent: true,
                symbol: "none",
                lineStyle: { color: "rgba(203,213,225,.28)", type: "dashed" },
                data: [{ xAxis: xThreshold }, { yAxis: 50 }],
              },
              markArea: {
                silent: true,
                label: { color: "rgba(226,232,240,.72)", fontWeight: 900, fontSize: 11 },
                data: [
                  [{ name: "Faible priorite", xAxis: 0, yAxis: 0, itemStyle: { color: "rgba(34,197,94,.07)" } }, { xAxis: xThreshold, yAxis: 50 }],
                  [{ name: "Quick wins", xAxis: xThreshold, yAxis: 0, itemStyle: { color: "rgba(45,212,191,.08)" } }, { xAxis: Math.ceil(maxImpactM * 1.15), yAxis: 50 }],
                  [{ name: "Surveillance", xAxis: 0, yAxis: 50, itemStyle: { color: "rgba(245,158,11,.08)" } }, { xAxis: xThreshold, yAxis: 100 }],
                  [{ name: "Critique", xAxis: xThreshold, yAxis: 50, itemStyle: { color: "rgba(239,68,68,.10)" } }, { xAxis: Math.ceil(maxImpactM * 1.15), yAxis: 100 }],
                ],
              },
            },
          ],
        }}
        onEvents={{
          click: (params) => {
            const value = params?.data?.value;
            if (value?.[3]) {
              applyFilters({
                lot: value[3],
                famille: value[5],
                importLocal: value[7],
              });
            }
          },
        }}
      />
      <div className="risk-recommendation">
        <span>SP2I Decision Intelligence</span>
        <strong>{insight.recommendation}</strong>
      </div>
    </div>
  );
}
