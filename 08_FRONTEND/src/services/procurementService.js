import { request } from "./apiClient";

export function getProcurementRiskAnalysis(simulationId) {
  return request({ url: `/procurement/risk-analysis/${simulationId}` });
}

export function getProcurementLeadTime(simulationId) {
  return request({ url: `/procurement/lead-time/${simulationId}` });
}

export function getProcurementCashflow(simulationId) {
  return request({ url: `/procurement/cashflow/${simulationId}` });
}

export function getProcurementImportComplexity(simulationId) {
  return request({ url: `/procurement/import-complexity/${simulationId}` });
}
