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
      <AnalyticsCard title="Etat du pilotage SP2I" eyebrow={metadata.qa_status || "Controle"}>
        <div className="health-list">
          {Object.entries(checks).map(([key, ok]) => (
            <span key={key} className={ok ? "ok" : "ko"}>
              {ok ? "OK" : "KO"} {key.replaceAll("_", " ")}
            </span>
          ))}
        </div>
      </AnalyticsCard>
      <AnalyticsCard title="Donnees projet et rapidite" eyebrow="Base cloud">
        <ul className="signal-list">
          <li>Memoire de calcul : {cache.backend || "n/a"}</li>
          <li>Donnees en cache : {cache.entries ?? "n/a"}</li>
          <li>Lignes budgetaires : {data.kpis?.nb_lignes || 0} lignes</li>
          <li>Budget travaux : {Number(data.kpis?.capex_brut || 0).toLocaleString("fr-FR")} FCFA</li>
        </ul>
      </AnalyticsCard>
      <AnalyticsCard title="Points d'attention" eyebrow="Controle qualite">
        {data.warnings?.length ? (
          <ul className="signal-list">{data.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
        ) : (
          <p className="empty-state">Aucune anomalie critique detectee.</p>
        )}
      </AnalyticsCard>
    </section>
  );
}
