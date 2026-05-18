import { request } from "./apiClient";
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
