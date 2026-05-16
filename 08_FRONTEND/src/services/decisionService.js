import { request } from "./apiClient";

export function getDecisionRules() {
  return request({ url: "/decision/rules" });
}

export function explainDecision(simulationId) {
  return request({ url: `/decision/explain/${simulationId}` });
}

export function getDecisionRiskAnalysis(scenarioId) {
  return request({ url: `/decision/risk-analysis/${scenarioId}` });
}
