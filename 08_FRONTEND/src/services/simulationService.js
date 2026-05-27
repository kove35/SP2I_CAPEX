import { request } from "./apiClient";
import { buildAnalyticsParams } from "./analyticsQueryBuilder";
import { SCENARIO_OPTIONS } from "../utils/businessContext";

export const defaultSimulationPayload = {
  items: [],
  parameters: {
    taux_landed_cost: {
      transport_maritime: 0.12,
      assurance: 0.02,
      droits_douane: 0.15,
    },
    seuil_decision_import: 0.97,
    coefficient_risque: 1.1,
  },
  mode: "strict",
  persist: false,
  summary_only: false,
  return_lines: true,
  scenario_name: SCENARIO_OPTIONS[0].code,
  scenario_type: "IMPORT_OPTIMIZATION",
  created_by: "frontend",
};

export function simulateCapex(payload = defaultSimulationPayload) {
  return request({
    url: "/simulation/simulate",
    method: "POST",
    data: payload,
  });
}

export function getSimulationAnalyticsPreview(filters = {}, extras = {}) {
  return request({
    url: "/analytics/procurement-lines",
    params: buildAnalyticsParams(filters, { page_size: 300, ...extras }),
  });
}

export function simulateScenarios(payload) {
  return request({
    url: "/simulation/scenarios",
    method: "POST",
    data: payload,
  });
}
