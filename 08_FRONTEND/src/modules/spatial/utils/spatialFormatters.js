export function formatSpatialMoney(value) {
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) return "—";
  if (number >= 1_000_000_000) return `${(number / 1_000_000_000).toFixed(1)} Md FCFA`;
  if (number >= 1_000_000) return `${Math.round(number / 1_000_000).toLocaleString("fr-FR")} M FCFA`;
  return `${Math.round(number).toLocaleString("fr-FR")} FCFA`;
}

export function spatialMaturityLabel(maturity) {
  const mode = maturity?.mode || maturity?.maturity || "NON_BIM";
  if (mode === "BIM_READY") return "BIM-ready";
  if (mode === "BIM_LITE") return "BIM-lite";
  return "Non BIM";
}

export function hasSpatialCapabilities(summary, workflow) {
  const maturity = summary?.maturity || workflow?.dqe?.bim_maturity || {};
  const mode = maturity.mode || maturity.maturity || "NON_BIM";
  return mode !== "NON_BIM" || Number(summary?.kpis?.spatialized_lines_count || 0) > 0;
}

export function compactSpatialLocation(item = {}) {
  return [item.batiment, item.niveau, item.appart, item.piece].filter(Boolean).join(" › ");
}
