import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Building2 } from "lucide-react";
import { getAnalyticsBuildingCompletion } from "../../services/analyticsService";
import AnalyticsCard from "../../ui/AnalyticsCard";
import Skeleton from "../../ui/Skeleton";

function formatNumber(value) {
  return Number(value || 0).toLocaleString("fr-FR");
}

export default function BuildingCompletionPanel() {
  const query = useQuery({
    queryKey: ["analytics", "building-completion"],
    queryFn: getAnalyticsBuildingCompletion,
    staleTime: 60_000,
    retry: 1,
  });
  const data = query.data || {};
  const metrics = [
    ["GO", data.go_rows],
    ["Maconnerie", data.masonry_rows],
    ["Toiture", data.roof_rows],
    ["Facades", data.facade_rows],
    ["VRD", data.vrd_rows],
    ["Securite", data.security_rows],
    ["Incendie", data.fire_rows],
    ["Ascenseur", data.elevator_rows],
  ];

  return (
    <AnalyticsCard
      title="Completude batiment"
      eyebrow="V5.3"
      action={<Building2 size={18} aria-hidden="true" />}
    >
      {query.isLoading ? <Skeleton rows={3} /> : null}
      <section className="metric-grid">
        <article className="metric-card">
          <span>Total V5.3</span>
          <strong>{formatNumber(data.total_rows)}</strong>
        </article>
        {metrics.map(([label, value]) => (
          <article className="metric-card" key={label}>
            <span>{label}</span>
            <strong>{formatNumber(value)}</strong>
          </article>
        ))}
      </section>
    </AnalyticsCard>
  );
}
