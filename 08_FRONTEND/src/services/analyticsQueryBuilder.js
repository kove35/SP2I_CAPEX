const apiFieldMap = {
  projet: "projet",
  scenario: "scenario",
  batiment: "batiment",
  niveau: "niveau",
  lot: "lot",
  famille: "famille",
  fournisseur: "fournisseur",
  importLocal: "decision_import",
  decisionImport: "decision_import",
  dateDebut: "periode_debut",
  dateFin: "periode_fin",
  periodeDebut: "periode_debut",
  periodeFin: "periode_fin",
};

const ignoredValues = new Set(["", "Tous", "Toutes", "ALL", "All", "all"]);

export function compactParams(params = {}) {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && !ignoredValues.has(value))
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
    if (params[apiKey]) return params;
    params[apiKey] = normalized[filterKey];
    return params;
  }, {});
  const params = compactParams({ ...mapped, ...extras });
  console.log("API params", params);
  return params;
}

export function buildAnalyticsQueryKey(scope, filters = {}, extras = {}) {
  return [`analytics-${scope}`, normalizeAnalyticsFilters(filters), compactParams(extras)];
}
