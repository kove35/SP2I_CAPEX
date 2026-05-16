import React from "react";
import AnalyticsCard from "../../ui/AnalyticsCard";
import KpiCard from "../../ui/KpiCard";

export default function SiteExecutionPage() {
  const [tab, setTab] = React.useState(new URLSearchParams(window.location.search).get("tab") || "planning");
  React.useEffect(() => {
    setTab(new URLSearchParams(window.location.search).get("tab") || "planning");
  }, [window.location.search]);

  const messages = {
    planning: ["Synchroniser les simulations CAPEX avec le planning directeur.", "Prioriser les lots qui bloquent le chemin critique."],
    dependencies: ["Identifier les dependances entre lots techniques et gros oeuvre.", "Eviter les validations achat qui creent un retard chantier."],
    deliveries: ["Suivre les ETA critiques et les livraisons attendues sur site.", "Prioriser les containers necessaires a la prochaine phase."],
    criticality: ["Classer les lots par criticite chantier et risque financier.", "Remonter les alertes vers le cockpit global."],
  };

  return (
    <main className="cockpit-page cockpit-page-fit">
      <section className="page-hero compact">
        <p className="eyebrow">Site Execution</p>
        <h1>Planning, dependances, livraisons et stockage chantier</h1>
      </section>
      <div className="tab-row">
        <button className={tab === "planning" ? "active" : ""} onClick={() => setTab("planning")} type="button">Planning</button>
        <button className={tab === "dependencies" ? "active" : ""} onClick={() => setTab("dependencies")} type="button">Dependances</button>
        <button className={tab === "deliveries" ? "active" : ""} onClick={() => setTab("deliveries")} type="button">Livraisons</button>
        <button className={tab === "criticality" ? "active" : ""} onClick={() => setTab("criticality")} type="button">Criticite</button>
      </div>
      <section className="metric-grid">
        <KpiCard label="Livraisons critiques" value="3" tone="warning" />
        <KpiCard label="Stockage site" value="72%" />
        <KpiCard label="Lots bloques" value="1" />
        <KpiCard label="ETA a surveiller" value="2" />
      </section>
      <section className="cockpit-split">
        <AnalyticsCard title={`Pilotage ${tab}`} eyebrow="Execution cockpit">
          <ul className="signal-list">
            {(messages[tab] || messages.planning).map((message) => <li key={message}>{message}</li>)}
          </ul>
        </AnalyticsCard>
        <aside className="context-panel">
          <AnalyticsCard title="Actions chantier" eyebrow="Decision rapide">
            <ul className="signal-list">
              <li>Valider les lots qui securisent le planning.</li>
              <li>Ouvrir Power BI pour l'analyse direction si besoin.</li>
              <li>Eviter de multiplier les pages : chaque tab garde le contexte.</li>
            </ul>
          </AnalyticsCard>
        </aside>
      </section>
    </main>
  );
}
