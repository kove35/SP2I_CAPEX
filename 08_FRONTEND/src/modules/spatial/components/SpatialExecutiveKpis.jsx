import React from "react";
import { formatSpatialMoney } from "../utils/spatialFormatters";

export default function SpatialExecutiveKpis({ summary }) {
  const kpis = summary?.kpis || {};
  const planning = summary?.planning || {};
  const storage = summary?.storage || [];
  const criticalStorage = storage.filter((item) => item.saturation_level === "HIGH").length;

  const items = [
    { label: "CAPEX exposé spatial", value: formatSpatialMoney(kpis.capex_spatialized) },
    { label: "Zones à risque", value: Number(kpis.spatial_risks_count || 0).toLocaleString("fr-FR"), tone: kpis.spatial_risks_count ? "warning" : "" },
    { label: "Chemins critiques", value: Number(planning.critical_path_count || 0).toLocaleString("fr-FR"), tone: planning.critical_path_count ? "warning" : "" },
    { label: "Stockage sensible", value: Number(criticalStorage).toLocaleString("fr-FR"), tone: criticalStorage ? "warning" : "" },
  ];

  return (
    <section className="spatial-executive-kpis" data-testid="spatial-executive-kpis">
      {items.map((item) => (
        <article key={item.label} className={`spatial-executive-kpi ${item.tone || ""}`}>
          <span>{item.label}</span>
          <strong>{item.value}</strong>
        </article>
      ))}
    </section>
  );
}
