import { request } from "./apiClient";

export function getContainerPlan(simulationId) {
  return request({ url: `/logistics/container-plan/${simulationId}` });
}

export function getShipmentAnalysis(simulationId) {
  return request({ url: `/logistics/shipment-analysis/${simulationId}` });
}

export function getFreightCost(simulationId) {
  return request({ url: `/logistics/freight-cost/${simulationId}` });
}

export function getSiteDelivery(simulationId) {
  return request({ url: `/logistics/site-delivery/${simulationId}` });
}
