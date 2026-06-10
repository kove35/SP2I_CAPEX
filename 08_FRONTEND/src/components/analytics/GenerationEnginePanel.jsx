import React from "react";
import { useQuery } from "@tanstack/react-query";
import { getAnalyticsGenerationEngine } from "../../services/analyticsService";
import AnalyticsCard from "../../ui/AnalyticsCard";
import Skeleton from "../../ui/Skeleton";
import { formatMoney } from "../../shared/formatters";

function formatNumber(value) {
  return Number(value || 0).toLocaleString("fr-FR");
}

export default function GenerationEnginePanel() {
  const query = useQuery({
    queryKey: ["analytics", "generation-engine"],
    queryFn: getAnalyticsGenerationEngine,
    staleTime: 60_000,
    retry: 1,
  });
  const data = query.data || {};
  const byLot = Array.isArray(data.by_lot) ? data.by_lot : [];

  return (
    <AnalyticsCard title="Generation engine" eyebrow="CAPEX generatif separe">
      {query.isLoading ? <Skeleton rows={3} /> : null}
      <section className="metric-grid">
        <article className="metric-card">
          <span>CAPEX local genere</span>
          <strong>{formatMoney(data.generated_capex_local || 0)}</strong>
        </article>
        <article className="metric-card">
          <span>CAPEX import genere</span>
          <strong>{formatMoney(data.generated_capex_import || 0)}</strong>
        </article>
        <article className="metric-card">
          <span>Economie generee</span>
          <strong>{formatMoney(data.generated_savings || 0)}</strong>
        </article>
        <article className="metric-card">
          <span>Lignes generees</span>
          <strong>{formatNumber(data.generated_lines)}</strong>
        </article>
      </section>
      <div className="fact-grid-shell">
        {byLot.slice(0, 10).map((row) => (
          <div className="filter-chip-row" key={row.lot_code}>
            <span>{row.lot_code}</span>
            <strong>{formatNumber(row.nb_lignes)} lignes - {formatNumber(row.nb_articles)} articles</strong>
          </div>
        ))}
      </div>
      {!query.isLoading && !byLot.length ? <p className="empty-state">Aucune ligne generative detaillee disponible.</p> : null}
    </AnalyticsCard>
  );
}
