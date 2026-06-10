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
    <AnalyticsCard
      title="Generation Engine"
      eyebrow="CAPEX génératif séparé"
    >
      {query.isLoading ? <Skeleton rows={3} /> : null}

      <section className="metric-grid">
        <article className="metric-card">
          <span>CAPEX local généré</span>
          <strong>
            {formatMoney(data.generated_capex_local || 0)}
          </strong>
        </article>

        <article className="metric-card">
          <span>CAPEX import généré</span>
          <strong>
            {formatMoney(data.generated_capex_import || 0)}
          </strong>
        </article>

        <article className="metric-card">
          <span>Économie générée</span>
          <strong>
            {formatMoney(data.generated_savings || 0)}
          </strong>
        </article>

        <article className="metric-card">
          <span>Lignes générées</span>
          <strong>
            {formatNumber(data.generated_lines)}
          </strong>
        </article>
      </section>

      <div
        style={{
          marginTop: "1rem",
          marginBottom: "0.75rem",
          fontWeight: 600,
        }}
      >
        Lots générés ({byLot.length})
      </div>

      <div className="fact-grid-shell">
        {byLot.map((row) => (
          <div
            className="filter-chip-row"
            key={row.lot_code}
          >
            <span>{row.lot_code}</span>

            <strong>
              {formatNumber(row.nb_lignes)} lignes •{" "}
              {formatNumber(row.nb_articles)} articles
            </strong>
          </div>
        ))}
      </div>

      {!query.isLoading && !byLot.length ? (
        <p className="empty-state">
          Aucune ligne générative détaillée disponible.
        </p>
      ) : null}
    </AnalyticsCard>
  );
}