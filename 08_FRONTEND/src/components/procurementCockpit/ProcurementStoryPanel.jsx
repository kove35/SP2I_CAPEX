import React from "react";
import { AlertTriangle, BrainCircuit, CheckCircle2, Download, Route, ShieldAlert } from "lucide-react";
import { formatMoney, formatPercent } from "../../shared/formatters";

export default function ProcurementStoryPanel({ data, selectedLine, onExport }) {
  const kpis = data?.kpis || {};
  const criticalAlerts = (data?.lines || []).filter((row) => Number(row.anomaly_score || 0) >= 60);
  const warningAlerts = (data?.lines || []).filter((row) => Number(row.anomaly_score || 0) >= 30 && Number(row.anomaly_score || 0) < 60);
  const infoAlerts = (data?.lines || []).filter((row) => Number(row.anomaly_score || 0) > 0 && Number(row.anomaly_score || 0) < 30);
  const alerts = [...criticalAlerts, ...warningAlerts, ...infoAlerts].slice(0, 5);
  const topLot = data?.lots?.[0];
  const topFamily = data?.families?.[0];

  return (
    <aside className="procurement-story-stack">
      <article className="procurement-panel story-panel">
        <header>
          <span><BrainCircuit size={14} /> Storytelling IA</span>
          <strong>Lecture executive</strong>
        </header>
        <p>
          Le cockpit detecte {criticalAlerts.length} anomalie(s) critique(s) et {warningAlerts.length} warning(s). {topLot?.label || "Le portefeuille"} concentre
          {` ${formatMoney(topLot?.amount || 0)} `} et la famille {topFamily?.label || "non classee"} porte le principal enjeu de benchmark.
        </p>
        <p>
          Le ROI achat est de {formatPercent(kpis.roi)} avec une confiance financiere moyenne de {Math.round(kpis.financialConfidence || 0)}/100.
        </p>
      </article>

      <article className="procurement-panel alert-panel">
        <header>
          <span><ShieldAlert size={14} /> Anomaly alerts</span>
          <strong>Files de controle</strong>
        </header>
        <div className="anomaly-severity-strip">
          <span className="critical"><b>{criticalAlerts.length}</b> Critical</span>
          <span className="warning"><b>{warningAlerts.length}</b> Warning</span>
          <span className="info"><b>{infoAlerts.length}</b> Info</span>
        </div>
        {alerts.length ? alerts.map((row) => (
          <div className={`alert-row ${Number(row.anomaly_score || 0) >= 60 ? "critical" : Number(row.anomaly_score || 0) >= 30 ? "warning" : "info"}`} key={row.id}>
            <AlertTriangle size={15} />
            <div>
              <b>{row.designation || row.famille}</b>
              <small>{row.alert} | {formatMoney(row.amount)} | benchmark {formatMoney(row.benchmark_min)} - {formatMoney(row.benchmark_max)}</small>
            </div>
          </div>
        )) : (
          <div className="alert-row ok"><CheckCircle2 size={15} /><div><b>Aucune anomalie critique</b><small>Les ranges financiers restent coherents.</small></div></div>
        )}
      </article>

      <article className="procurement-panel story-panel">
        <header>
          <span><Route size={14} /> Drill-through fournisseur</span>
          <strong>{selectedLine?.supplier || "Selectionner une ligne"}</strong>
        </header>
        <dl className="selected-line-dl">
          <div><dt>Article</dt><dd>{selectedLine?.designation || "Aucun article selectionne"}</dd></div>
          <div><dt>Lot</dt><dd>{selectedLine?.lot || "-"}</dd></div>
          <div><dt>Decision</dt><dd>{selectedLine?.decision || "-"}</dd></div>
          <div><dt>Sanity</dt><dd>{Math.round(selectedLine?.financial_confidence_score || 0)}/100</dd></div>
        </dl>
        <button type="button" onClick={onExport}><Download size={15} /> Export Power BI ready</button>
      </article>
    </aside>
  );
}
