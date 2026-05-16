import React from "react";
import KpiCard from "../components/kpi/KpiCard";
import ContainerTable from "../components/logistics/ContainerTable";
import ShipmentTable from "../components/logistics/ShipmentTable";
import { defaultSimulationPayload, simulateCapex } from "../services/simulationService";
import { getContainerPlan, getFreightCost, getShipmentAnalysis, getSiteDelivery } from "../services/logisticsService";

export default function Logistics() {
  const [simulationId, setSimulationId] = React.useState("");
  const [containers, setContainers] = React.useState([]);
  const [shipments, setShipments] = React.useState([]);
  const [freight, setFreight] = React.useState([]);
  const [site, setSite] = React.useState([]);
  const [error, setError] = React.useState("");
  const [loading, setLoading] = React.useState(false);

  const runWorkflow = async () => {
    setLoading(true);
    setError("");
    try {
      const simulation = await simulateCapex({
        ...defaultSimulationPayload,
        scenario_name: "FRONT_LOGISTICS_TEST",
      });
      const id = simulation.metadata.simulation_id;
      setSimulationId(id);
      const [containerData, shipmentData, freightData, siteData] = await Promise.all([
        getContainerPlan(id),
        getShipmentAnalysis(id),
        getFreightCost(id),
        getSiteDelivery(id),
      ]);
      setContainers(containerData.container_plan || []);
      setShipments(shipmentData.shipment_analysis || []);
      setFreight(freightData.freight_cost || []);
      setSite(siteData.site_delivery || []);
    } catch (apiError) {
      setError(apiError.message);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    runWorkflow();
  }, []);

  const totalFreight = freight.reduce((sum, row) => sum + Number(row.shipment_cost || 0), 0);
  const maxEta = shipments.reduce((max, row) => Math.max(max, Number(row.lead_time_total || 0)), 0);

  return (
    <main className="page analytics-page">
      <header className="entete-page">
        <p>Logistics</p>
        <h1>Containers, shipment et livraison chantier</h1>
      </header>

      <section className="analytics-toolbar">
        <label>
          Simulation ID
          <input value={simulationId} onChange={(event) => setSimulationId(event.target.value)} />
        </label>
        <button type="button" onClick={runWorkflow} disabled={loading}>
          {loading ? "Chargement..." : "Tester workflow logistique"}
        </button>
      </section>

      {error ? <div className="analytics-error">{error}</div> : null}

      <section className="analytics-grid three">
        <KpiCard label="Containers" value={containers.length} />
        <KpiCard label="Cout shipment" value={`${totalFreight.toLocaleString("fr-FR")} FCFA`} tone="warning" />
        <KpiCard label="ETA max" value={`${maxEta} j`} />
      </section>

      <section className="analytics-grid two">
        <article className="analytics-card">
          <div className="section-title">
            <h2>Plan container</h2>
            <span>ContainerEngine</span>
          </div>
          <ContainerTable rows={containers} />
        </article>
        <article className="analytics-card">
          <div className="section-title">
            <h2>Shipments</h2>
            <span>ShipmentEngine</span>
          </div>
          <ShipmentTable rows={shipments} />
        </article>
      </section>

      <section className="analytics-card">
        <div className="section-title">
          <h2>Livraison chantier</h2>
          <span>{site.length} ligne(s)</span>
        </div>
        <ShipmentTable rows={site.map((row) => ({ ...row, shipment_strategy: row.delivery_risk }))} />
      </section>
    </main>
  );
}
