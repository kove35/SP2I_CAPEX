import React from "react";
import { useQuery } from "@tanstack/react-query";
import { BatteryCharging } from "lucide-react";
import { getAnalyticsEnergyResilience } from "../../services/analyticsService";
import AnalyticsCard from "../../ui/AnalyticsCard";
import Skeleton from "../../ui/Skeleton";

function formatNumber(value, digits = 0) {
  return Number(value || 0).toLocaleString("fr-FR", { maximumFractionDigits: digits });
}

export default function EnergyResiliencePanel() {
  const query = useQuery({
    queryKey: ["analytics", "energy-resilience"],
    queryFn: getAnalyticsEnergyResilience,
    staleTime: 60_000,
    retry: 1,
  });
  const data = query.data || {};
  const sources = Array.isArray(data.energy_sources) ? data.energy_sources : [];

  return (
    <AnalyticsCard
      title="Resilience energetique"
      eyebrow="V5.2.2"
      action={<BatteryCharging size={18} aria-hidden="true" />}
    >
      {query.isLoading ? <Skeleton rows={3} /> : null}
      <section className="metric-grid">
        <article className="metric-card">
          <span>Solaire</span>
          <strong>{formatNumber(data.solar_kwc, 1)} kWc</strong>
        </article>
        <article className="metric-card">
          <span>Batteries</span>
          <strong>{formatNumber(data.battery_capacity_kwh, 1)} kWh</strong>
        </article>
        <article className="metric-card">
          <span>Groupe</span>
          <strong>{data.generator || "-"}</strong>
        </article>
        <article className="metric-card">
          <span>Autonomie</span>
          <strong>{formatNumber(data.autonomy_hours, 1)} h</strong>
        </article>
      </section>
      <div className="health-list">
        {sources.slice(0, 8).map((source) => (
          <span className="ok" key={`${source.system_code}-${source.lot_code}`}>
            {source.system_code} : {formatNumber(source.nb_lignes)} lignes
          </span>
        ))}
      </div>
    </AnalyticsCard>
  );
}
