import React from "react";
import { formatSpatialMoney, spatialMaturityLabel } from "../utils/spatialFormatters";

export default function SpatialKpiBand({ summary }) {
  const kpis = summary?.kpis || {};
  const maturity = summary?.maturity || {};
  const mode = maturity.mode || maturity.maturity || "NON_BIM";

  if (mode === "NON_BIM" && Number(kpis.spatialized_lines_count || 0) <= 0) return null;

  const items = [
    { label: "Mode spatial", value: spatialMaturityLabel(maturity) },
    { label: "Lignes spatialisées", value: Number(kpis.spatialized_lines_count || 0).toLocaleString("fr-FR") },
    { label: "Bâtiments", value: Number(kpis.batiments_count || 0).toLocaleString("fr-FR") },
    { label: "Niveaux", value: Number(kpis.niveaux_count || 0).toLocaleString("fr-FR") },
    { label: "Pièces", value: Number(kpis.pieces_count || 0).toLocaleString("fr-FR") },
    { label: "CAPEX spatialisé", value: formatSpatialMoney(kpis.capex_spatialized) },
    { label: "Risques spatiaux", value: Number(kpis.spatial_risks_count || 0).toLocaleString("fr-FR"), tone: Number(kpis.spatial_risks_count || 0) > 0 ? "warning" : "" },
  ];

  return (
    <section className="spatial-kpi-band" data-testid="spatial-kpi-band">
      {items.map((item) => (
        <article key={item.label} className={`spatial-kpi ${item.tone || ""}`}>
          <span>{item.label}</span>
          <strong>{item.value}</strong>
        </article>
      ))}
    </section>
  );
}
