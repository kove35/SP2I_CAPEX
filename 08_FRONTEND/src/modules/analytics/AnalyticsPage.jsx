import React from "react";
import AnalyticsCard from "../../ui/AnalyticsCard";

const dashboards = [
  ["direction", "Direction"],
  ["capex", "CAPEX"],
  ["site", "Projet"],
  ["procurement", "Procurement"],
  ["logistics", "Logistics"],
  ["risks", "Risks"],
  ["heatmaps", "Heatmaps"],
  ["drilldown", "Drill-down"],
  ["timeline", "Timeline"],
  ["admin", "Administration"],
  ["monitoring", "Monitoring"],
  ["users", "Utilisateurs"],
];

export default function AnalyticsPage() {
  const [dashboard, setDashboard] = React.useState(new URLSearchParams(window.location.search).get("dashboard") || "direction");

  React.useEffect(() => {
    setDashboard(new URLSearchParams(window.location.search).get("dashboard") || "direction");
  }, [window.location.search]);

  const label = dashboards.find(([key]) => key === dashboard)?.[1] || "Direction";

  return (
    <main className="cockpit-page cockpit-page-fit">
      <section className="page-hero compact">
        <p className="eyebrow">Power BI Embedded</p>
        <h1>Dashboards decisionnels pour investissements immobiliers</h1>
        <p>Power BI est la couche analytique strategique pour direction, finance et pilotage projet.</p>
      </section>
      <div className="tab-row">
        {dashboards.map(([key, name]) => (
          <button key={key} className={dashboard === key ? "active" : ""} type="button" onClick={() => setDashboard(key)}>
            {name}
          </button>
        ))}
      </div>
      <section className="cockpit-split analytics-embed-layout">
        <AnalyticsCard title={`Dashboard ${label}`} eyebrow="Power BI actif">
          <div className="powerbi-placeholder powerbi-embed-large">
            <strong>Power BI Embedded</strong>
            <span>Un seul dashboard charge a la fois pour garder l'interface fluide.</span>
            <small>Contexte attendu : projet Pointe-Noire, scenario actif, periode et filtres metier.</small>
          </div>
        </AnalyticsCard>
        <aside className="context-panel">
          <AnalyticsCard title="Contexte analytics" eyebrow="React vers Power BI">
            <ul className="signal-list">
              <li>Projet actif transmis comme filtre.</li>
              <li>Scenario actif synchronise avec le cockpit.</li>
              <li>React pilote, Power BI analyse en profondeur.</li>
            </ul>
          </AnalyticsCard>
        </aside>
      </section>
    </main>
  );
}
