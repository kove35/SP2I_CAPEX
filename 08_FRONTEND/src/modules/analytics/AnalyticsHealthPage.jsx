import React from "react";
import AnalyticsCard from "../../ui/AnalyticsCard";
import Skeleton from "../../ui/Skeleton";

export default function AnalyticsHealthPage({ qa }) {
  const data = qa.data || {};
  const metadata = data.metadata || {};
  const checks = metadata.checks || {};
  const cache = metadata.cache || {};

  if (qa.isLoading) {
    return <Skeleton rows={5} />;
  }

  return (
    <section className="analytics-health-grid">
      <AnalyticsCard title="Santé Analytics Engine" eyebrow={metadata.qa_status || "QA"}>
        <div className="health-list">
          {Object.entries(checks).map(([key, ok]) => (
            <span key={key} className={ok ? "ok" : "ko"}>
              {ok ? "OK" : "KO"} {key.replaceAll("_", " ")}
            </span>
          ))}
        </div>
      </AnalyticsCard>
      <AnalyticsCard title="PostgreSQL & Cache" eyebrow="Runtime">
        <ul className="signal-list">
          <li>Backend cache : {cache.backend || "n/a"}</li>
          <li>Entrées cache : {cache.entries ?? "n/a"}</li>
          <li>FACT_METRE : {data.kpis?.nb_lignes || 0} lignes</li>
          <li>CAPEX : {Number(data.kpis?.capex_brut || 0).toLocaleString("fr-FR")} FCFA</li>
        </ul>
      </AnalyticsCard>
      <AnalyticsCard title="Warnings" eyebrow="Observabilité">
        {data.warnings?.length ? (
          <ul className="signal-list">{data.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
        ) : (
          <p className="empty-state">Aucune anomalie QA critique détectée.</p>
        )}
      </AnalyticsCard>
    </section>
  );
}
