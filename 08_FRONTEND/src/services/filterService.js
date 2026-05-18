import { request } from "./apiClient";

export function toSelectOptions(values = []) {
  return values
    .filter(Boolean)
    .map((value) => ({ value: String(value), label: String(value) }));
}

export async function getAnalyticsFilters() {
  const data = await request({ url: "/analytics/filters" });
  return {
    batiments: toSelectOptions(data.batiments || []),
    niveaux: toSelectOptions(data.niveaux || []),
    lots: toSelectOptions(data.lots || []),
    familles: toSelectOptions(data.familles || []),
    importLocal: toSelectOptions(data.import_local || ["IMPORT", "LOCAL"]),
  };
}
