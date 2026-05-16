import React from "react";
import KpiCard from "../../ui/KpiCard";
import AnalyticsCard from "../../ui/AnalyticsCard";
import { average } from "../../shared/formatters";
import { defaultSimulationPayload, simulateCapex } from "../../services/simulationService";
import { getProcurementCashflow, getProcurementImportComplexity, getProcurementLeadTime, getProcurementRiskAnalysis } from "../../services/procurementService";

function rowsFromSimulation(lines = []) {
  return {
    risk: lines.map((line) => ({
      id_ligne: line.id_ligne,
      designation: line.designation,
      global_risk_score: line.global_risk_score,
      procurement_reason: line.procurement_analysis,
    })),
    lead: lines.map((line) => ({
      id_ligne: line.id_ligne,
      designation: line.designation,
      lead_time_days: line.lead_time_days,
      procurement_reason: line.procurement_analysis,
    })),
    cash: lines.map((line) => ({
      id_ligne: line.id_ligne,
      designation: line.designation,
      cashflow_score: line.cashflow_score,
      capex_import: line.capex_import,
      procurement_reason: line.procurement_analysis,
    })),
    complexity: lines.map((line) => ({
      id_ligne: line.id_ligne,
      designation: line.designation,
      complexity_score: line.complexity_score,
      moq_risk_score: line.moq_risk_score,
      procurement_reason: line.procurement_analysis,
    })),
  };
}

export default function ProcurementPage() {
  const [rows, setRows] = React.useState({ risk: [], lead: [], cash: [], complexity: [] });
  const [error, setError] = React.useState("");
  const [tab, setTab] = React.useState(new URLSearchParams(window.location.search).get("tab") || "suppliers");

  React.useEffect(() => {
    setTab(new URLSearchParams(window.location.search).get("tab") || "suppliers");
  }, [window.location.search]);

  const run = async () => {
    setError("");
    try {
      const simulation = await simulateCapex({ ...defaultSimulationPayload, scenario_name: "SAAS_PROCUREMENT" });
      setRows(rowsFromSimulation(simulation.lignes || []));

      const id = simulation.metadata.simulation_id;
      try {
        const [risk, lead, cash, complexity] = await Promise.all([
          getProcurementRiskAnalysis(id),
          getProcurementLeadTime(id),
          getProcurementCashflow(id),
          getProcurementImportComplexity(id),
        ]);
        setRows({
          risk: risk.risk_analysis || [],
          lead: lead.lead_time_analysis || [],
          cash: cash.cashflow_analysis || [],
          complexity: complexity.import_complexity_analysis || [],
        });
      } catch (historyError) {
        console.warn("PROCUREMENT HISTORY UNAVAILABLE", historyError);
      }
    } catch (apiError) {
      setError(`Analyse procurement indisponible : ${apiError.message}`);
    }
  };

  React.useEffect(() => { run(); }, []);

  return (
    <main className="cockpit-page cockpit-page-fit">
      <section className="page-hero compact">
        <p className="eyebrow">Moteur d'optimisation integre</p>
        <h1>Procurement, import et supply chain au service du CAPEX</h1>
      </section>
      <div className="tab-row">
        <button className={tab === "suppliers" ? "active" : ""} onClick={() => setTab("suppliers")} type="button">Fournisseurs</button>
        <button className={tab === "import" ? "active" : ""} onClick={() => setTab("import")} type="button">Import</button>
        <button className={tab === "cashflow" ? "active" : ""} onClick={() => setTab("cashflow")} type="button">Cashflow</button>
        <button className={tab === "moq" ? "active" : ""} onClick={() => setTab("moq")} type="button">MOQ</button>
        <button className={tab === "risks" ? "active" : ""} onClick={() => setTab("risks")} type="button">Risques</button>
      </div>
      {error ? <div className="app-error">{error}</div> : null}
      <section className="metric-grid">
        <KpiCard label="Risque moyen" value={`${Math.round(average(rows.risk, "global_risk_score"))}/100`} />
        <KpiCard label="Lead time" value={`${Math.round(average(rows.lead, "lead_time_days"))} j`} />
        <KpiCard label="Cashflow score" value={`${Math.round(average(rows.cash, "cashflow_score"))}/100`} tone="success" />
        <KpiCard label="Complexite" value={`${Math.round(average(rows.complexity, "complexity_score"))}/100`} tone="warning" />
      </section>
      <section className="cockpit-split">
        <AnalyticsCard title="Analyse procurement" eyebrow={`Vue ${tab}`}>
        <div className="data-table-wrap panel-scroll">
          <table className="data-table">
            <thead><tr><th>Produit</th><th>Risque</th><th>Lead time</th><th>Cashflow</th><th>Complexite</th></tr></thead>
            <tbody>
              {rows.risk.map((row, index) => (
                <tr key={row.id_ligne}>
                  <td>{row.designation}</td>
                  <td>{row.global_risk_score}</td>
                  <td>{rows.lead[index]?.lead_time_days || 0} j</td>
                  <td>{rows.cash[index]?.cashflow_score || 0}</td>
                  <td>{rows.complexity[index]?.complexity_score || 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        </AnalyticsCard>
        <aside className="context-panel">
          <AnalyticsCard title="Priorite cockpit" eyebrow="Optimisation CAPEX">
            <ul className="signal-list">
              <li>{tab === "suppliers" ? "Comparer les fournisseurs par risque, qualite et delai." : "Conserver le CAPEX comme decision principale."}</li>
              <li>{tab === "cashflow" ? "Identifier les lignes rentables mais dangereuses pour la tresorerie." : "Les analyses cashflow restent disponibles en un clic."}</li>
              <li>{tab === "risks" ? "Remonter les risques critiques vers le cockpit global." : "Les risques alimentent le DecisionEngine."}</li>
            </ul>
          </AnalyticsCard>
        </aside>
      </section>
    </main>
  );
}
