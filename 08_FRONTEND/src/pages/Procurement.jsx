import React from "react";
import KpiCard from "../components/kpi/KpiCard";
import RiskCard from "../components/kpi/RiskCard";
import { defaultSimulationPayload, simulateCapex } from "../services/simulationService";
import {
  getProcurementCashflow,
  getProcurementImportComplexity,
  getProcurementLeadTime,
  getProcurementRiskAnalysis,
} from "../services/procurementService";

export default function Procurement() {
  const [risk, setRisk] = React.useState([]);
  const [leadTime, setLeadTime] = React.useState([]);
  const [cashflow, setCashflow] = React.useState([]);
  const [complexity, setComplexity] = React.useState([]);
  const [error, setError] = React.useState("");
  const [loading, setLoading] = React.useState(false);

  const runProcurement = async () => {
    setLoading(true);
    setError("");
    try {
      const simulation = await simulateCapex({
        ...defaultSimulationPayload,
        scenario_name: "FRONT_PROCUREMENT_TEST",
      });
      const id = simulation.metadata.simulation_id;
      const [riskData, leadData, cashData, complexityData] = await Promise.all([
        getProcurementRiskAnalysis(id),
        getProcurementLeadTime(id),
        getProcurementCashflow(id),
        getProcurementImportComplexity(id),
      ]);
      setRisk(riskData.risk_analysis || []);
      setLeadTime(leadData.lead_time_analysis || []);
      setCashflow(cashData.cashflow_analysis || []);
      setComplexity(complexityData.import_complexity_analysis || []);
    } catch (apiError) {
      setError(apiError.message);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    runProcurement();
  }, []);

  const avgRisk = risk.length ? Math.round(risk.reduce((sum, row) => sum + Number(row.global_risk_score || 0), 0) / risk.length) : 0;
  const avgLead = leadTime.length ? Math.round(leadTime.reduce((sum, row) => sum + Number(row.lead_time_days || 0), 0) / leadTime.length) : 0;
  const avgCash = cashflow.length ? Math.round(cashflow.reduce((sum, row) => sum + Number(row.cashflow_score || 0), 0) / cashflow.length) : 0;

  return (
    <main className="page analytics-page">
      <header className="entete-page">
        <p>Procurement</p>
        <h1>Risques fournisseurs, cashflow et MOQ</h1>
      </header>

      <section className="analytics-toolbar">
        <button type="button" onClick={runProcurement} disabled={loading}>
          {loading ? "Analyse..." : "Tester procurement"}
        </button>
      </section>

      {error ? <div className="analytics-error">{error}</div> : null}

      <section className="analytics-grid four">
        <RiskCard title="Risque import" level={avgRisk >= 60 ? "HIGH" : avgRisk >= 30 ? "MEDIUM" : "LOW"} score={`${avgRisk}/100`} />
        <KpiCard label="Lead time moyen" value={`${avgLead} j`} />
        <KpiCard label="Cashflow score" value={`${avgCash}/100`} tone="success" />
        <KpiCard label="Lignes analysees" value={risk.length} />
      </section>

      <section className="analytics-card">
        <div className="section-title">
          <h2>Analyse procurement par ligne</h2>
          <span>RiskEngine + Cashflow + MOQ</span>
        </div>
        <div className="analytics-table-wrap">
          <table className="analytics-table">
            <thead>
              <tr>
                <th>Produit</th>
                <th>Risque</th>
                <th>Lead time</th>
                <th>Cashflow</th>
                <th>Complexite</th>
              </tr>
            </thead>
            <tbody>
              {risk.map((row, index) => (
                <tr key={row.id_ligne || row.designation}>
                  <td>{row.designation}</td>
                  <td>{row.global_risk_score}</td>
                  <td>{leadTime[index]?.lead_time_days || 0} j</td>
                  <td>{cashflow[index]?.cashflow_score || 0}</td>
                  <td>{complexity[index]?.complexity_score || 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
