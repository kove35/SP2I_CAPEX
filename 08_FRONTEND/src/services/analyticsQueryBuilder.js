const apiFieldMap = {
  projet: "projet",
  scenario: "scenario",
  batiment: "batiment",
  niveau: "niveau",
  lot: "lot",
  famille: "famille",
  fournisseur: "fournisseur",
  decisionImport: "decision_import",
  periodeDebut: "periode_debut",
  periodeFin: "periode_fin",
};

export function compactParams(params = {}) {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== "")
  );
}

export function normalizeAnalyticsFilters(filters = {}) {
  return Object.fromEntries(
    Object.keys(apiFieldMap)
      .sort()
      .map((key) => [key, typeof filters[key] === "string" ? filters[key].trim() : filters[key] || ""])
  );
}

export function buildAnalyticsParams(filters = {}, extras = {}) {
  const normalized = normalizeAnalyticsFilters(filters);
  const mapped = Object.entries(apiFieldMap).reduce((params, [filterKey, apiKey]) => {
    params[apiKey] = normalized[filterKey];
    return params;
  }, {});
  return compactParams({ ...mapped, ...extras });
}

export function buildAnalyticsQueryKey(scope, filters = {}, extras = {}) {
  return ["analytics", scope, normalizeAnalyticsFilters(filters), compactParams(extras)];
}
