import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity } from "lucide-react";
import { getAnalyticsGenerationDiagnostic } from "../../services/analyticsService";
import AnalyticsCard from "../../ui/AnalyticsCard";
import Skeleton from "../../ui/Skeleton";

function formatNumber(value) {
  return Number(value || 0).toLocaleString("fr-FR");
}

function statusClass(value) {
  return value === "DEPLOYED" ? "ok" : "ko";
}

export default function GenerationDiagnosticCard() {
  const query = useQuery({
    queryKey: ["analytics", "generation-diagnostic"],
    queryFn: getAnalyticsGenerationDiagnostic,
    staleTime: 60_000,
    retry: 1,
  });
  const data = query.data || {};
  const statuses = [
    ["V5.2", data.v52_status],
    ["V5.2.1", data.v521_status],
    ["V5.2.2", data.v522_status],
    ["V5.3", data.v53_status],
  ];
  const metrics = [
    ["BIM", data.fact_generation_bim],
    ["Reseaux", data.fact_generation_network],
    ["DQE", data.fact_generation_dqe],
    ["Expansion", data.fact_generation_expansion],
    ["Batiment", data.building_rows],
    ["Enveloppe", data.envelope_rows],
    ["Systemes", data.special_rows],
    ["Couverture", `${Number(data.coverage_pct || 0).toLocaleString("fr-FR", { maximumFractionDigits: 2 })} %`],
  ];

  return (
    <AnalyticsCard
      title="Diagnostic generation"
      eyebrow="V5.2 a V5.3"
      action={<Activity size={18} aria-hidden="true" />}
    >
      {query.isLoading ? <Skeleton rows={3} /> : null}
      <div className="health-list">
        {statuses.map(([label, value]) => (
          <span className={statusClass(value)} key={label}>{label} : {value || "UNKNOWN"}</span>
        ))}
      </div>
      <section className="metric-grid">
        {metrics.map(([label, value]) => (
          <article className="metric-card" key={label}>
            <span>{label}</span>
            <strong>{typeof value === "number" ? formatNumber(value) : value || "-"}</strong>
          </article>
        ))}
      </section>
      {query.isError ? <p className="empty-state">Diagnostic generation indisponible.</p> : null}
    </AnalyticsCard>
  );
}
