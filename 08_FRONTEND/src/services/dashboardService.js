import { request } from "./apiClient";

function compactParams(params = {}) {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== "")
  );
}

export function getCapexSummary() {
  return request({ url: "/capex/summary" });
}

export function getFactMetre(filters = {}, limit = 500) {
  return request({
    url: "/fact_metre",
    params: compactParams({
      famille: filters.famille,
      lot: filters.lot,
      batiment: filters.batiment,
      limit,
    }),
  });
}

export function getMonitoringStatus() {
  return request({ url: "/monitoring/status" });
}

export function getScenarioHistory() {
  return request({ url: "/simulation/scenarios" });
}
