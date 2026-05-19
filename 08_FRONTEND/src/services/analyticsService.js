import { apiClient, request } from "./apiClient";
import { buildAnalyticsParams } from "./analyticsQueryBuilder";

export const toAnalyticsParams = buildAnalyticsParams;

export function getAnalyticsDashboard(filters, dashboardType = "direction", extras = {}) {
  return request({
    url: "/analytics/dashboard",
    params: toAnalyticsParams(filters, { dashboard_type: dashboardType, page_size: 100, ...extras }),
  });
}

export function getAnalyticsCapex(filters, extras = {}) {
  return request({ url: "/analytics/capex", params: toAnalyticsParams(filters, { page_size: 100, ...extras }) });
}

export function getAnalyticsProcurement(filters, extras = {}) {
  return request({ url: "/analytics/procurement", params: toAnalyticsParams(filters, { page_size: 300, ...extras }) });
}

export function getAnalyticsSuppliers(filters, extras = {}) {
  return request({ url: "/analytics/suppliers", params: toAnalyticsParams(filters, { page_size: 100, ...extras }) });
}

export function getAnalyticsProcurementLines(filters, extras = {}) {
  return request({ url: "/analytics/procurement-lines", params: toAnalyticsParams(filters, { page_size: 500, ...extras }) });
}

export function getAnalyticsProcurementScenarios(filters, extras = {}) {
  return request({ url: "/analytics/procurement-scenarios", params: toAnalyticsParams(filters, { page_size: 50, ...extras }) });
}

export function getAnalyticsCurrency(filters, extras = {}) {
  return request({ url: "/analytics/currency", params: toAnalyticsParams(filters, extras) });
}

export function getAnalyticsImportRisks(filters, extras = {}) {
  return request({ url: "/analytics/import-risks", params: toAnalyticsParams(filters, { page_size: 50, ...extras }) });
}

export function getAnalyticsGainAnalysis(filters, extras = {}) {
  return request({ url: "/analytics/gain-analysis", params: toAnalyticsParams(filters, { page_size: 500, ...extras }) });
}

export async function exportAnalyticsProcurementFile(filters, extras = {}) {
  const response = await apiClient({
    url: "/analytics/procurement-export",
    params: toAnalyticsParams(filters, { page_size: 500, ...extras }),
    responseType: "blob",
  });
  return response.data;
}

export async function exportAnalyticsGainAnalysis(filters, extras = {}) {
  const response = await apiClient({
    url: "/analytics/gain-analysis/export",
    params: toAnalyticsParams(filters, { page_size: 500, ...extras }),
    responseType: "blob",
  });
  return response.data;
}

export function getAnalyticsHeatmap(filters, extras = {}) {
  return request({ url: "/analytics/heatmap", params: toAnalyticsParams(filters, extras) });
}

export function getAnalyticsRisk(filters, extras = {}) {
  return request({ url: "/analytics/risk", params: toAnalyticsParams(filters, extras) });
}

export function getAnalyticsTimeline(filters, extras = {}) {
  return request({ url: "/analytics/timeline", params: toAnalyticsParams(filters, extras) });
}

export function getAnalyticsDrilldown(filters, extras = {}) {
  return request({
    url: "/analytics/drilldown",
    params: toAnalyticsParams(filters, { page_size: 500, drilldown_level: "lot", ...extras }),
  });
}

export function getAnalyticsQaSummary() {
  return request({ url: "/analytics/qa-summary" });
}

export function getAnalyticsDataQuality() {
  return request({ url: "/analytics/data-quality" });
}
