import React from "react";
import AnalyticsCard from "../../ui/AnalyticsCard";
import KpiCard from "../../ui/KpiCard";
import ContainerTable from "../../components/logistics/ContainerTable";
import ShipmentTable from "../../components/logistics/ShipmentTable";
import { formatMoney } from "../../shared/formatters";
import { defaultSimulationPayload, simulateCapex } from "../../services/simulationService";
import { getContainerPlan, getFreightCost, getShipmentAnalysis, getSiteDelivery } from "../../services/logisticsService";

export default function LogisticsPage() {
  const [data, setData] = React.useState({ containers: [], shipments: [], freight: [], site: [] });
  const [error, setError] = React.useState("");
  const [tab, setTab] = React.useState(new URLSearchParams(window.location.search).get("tab") || "containers");

  React.useEffect(() => {
    setTab(new URLSearchParams(window.location.search).get("tab") || "containers");
  }, [window.location.search]);

  const run = async () => {
    setError("");
    try {
      const simulation = await simulateCapex({ ...defaultSimulationPayload, scenario_name: "LOGISTICS_SECURITY" });
      const id = simulation.metadata.simulation_id;
      const [containers, shipments, freight, site] = await Promise.all([
        getContainerPlan(id),
        getShipmentAnalysis(id),
        getFreightCost(id),
        getSiteDelivery(id),
      ]);
      setData({
        containers: containers.container_plan || [],
        shipments: shipments.shipment_analysis || [],
        freight: freight.freight_cost || [],
        site: site.site_delivery || [],
      });
    } catch (apiError) {
      setError(apiError.message);
    }
  };

  React.useEffect(() => { run(); }, []);

  const totalFreight = data.freight.reduce((sum, row) => sum + Number(row.shipment_cost || 0), 0);
  const avgFill = data.containers.length
    ? data.containers.reduce((sum, row) => sum + Number(row.fill_rate || 0), 0) / data.containers.length
    : 0;

  return (
    <main className="cockpit-page cockpit-page-fit">
      <section className="page-hero compact">
        <p className="eyebrow">Logistique projet</p>
        <h1>Livraisons, transport et stockage pour securiser le chantier</h1>
      </section>
      <div className="tab-row">
        <button className={tab === "containers" ? "active" : ""} onClick={() => setTab("containers")} type="button">Containers</button>
        <button className={tab === "shipments" ? "active" : ""} onClick={() => setTab("shipments")} type="button">Expeditions</button>
        <button className={tab === "freight" ? "active" : ""} onClick={() => setTab("freight")} type="button">Transport</button>
        <button className={tab === "site" ? "active" : ""} onClick={() => setTab("site")} type="button">ETA chantier</button>
      </div>
      {error ? <div className="app-error">{error}</div> : null}
      <section className="metric-grid">
        <KpiCard label="Containers" value={data.containers.length} />
        <KpiCard label="Taux de remplissage" value={`${Math.round(avgFill * 100)}%`} tone="success" />
        <KpiCard label="Cout transport" value={formatMoney(totalFreight)} tone="warning" />
        <KpiCard label="Livraisons site" value={data.site.length} />
      </section>
      <section className="cockpit-split">
        <AnalyticsCard title={tab === "shipments" ? "Expeditions" : tab === "freight" ? "Couts de transport" : tab === "site" ? "Livraison chantier" : "Containers"} eyebrow="Logistique projet">
          <div className="panel-scroll">
            {tab === "shipments" ? <ShipmentTable rows={data.shipments} /> : <ContainerTable rows={data.containers} />}
          </div>
        </AnalyticsCard>
        <aside className="context-panel">
          <AnalyticsCard title="Impact chantier" eyebrow="Contexte decisionnel">
            <ul className="signal-list">
              <li>Containers, expeditions et transport restent dans le meme cockpit.</li>
              <li>Les details logistiques doivent rester relies au budget travaux.</li>
              <li>Les retards critiques doivent remonter dans Pilotage Projet.</li>
            </ul>
          </AnalyticsCard>
        </aside>
      </section>
    </main>
  );
}
