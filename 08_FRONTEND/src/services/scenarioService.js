import { request } from "./apiClient";

export function listScenarios() {
  return request({ url: "/simulation/scenarios" });
}

export function getScenario(scenarioId) {
  return request({ url: `/simulation/scenario/${scenarioId}` });
}

export function compareScenarios(scenarioA, scenarioB) {
  return request({
    url: "/simulation/compare",
    params: { scenario_a: scenarioA, scenario_b: scenarioB },
  });
}
