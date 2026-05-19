import { request } from "./apiClient";
import { buildAnalyticsParams } from "./analyticsQueryBuilder";
import { SCENARIO_OPTIONS } from "../utils/businessContext";

export const defaultSimulationPayload = {
  items: [
    {
      id_ligne: "FRONT-001",
      designation: "Luminaire Shanghai",
      quantite: 500,
      prix_total_ht: 25000000,
      famille: "luminaire",
      lot: "Lot Electricite",
      volume_unitaire_m3: 0.03,
      poids_unitaire_kg: 4,
      supplier_city: "Shanghai",
      shipment_status: "AT_SEA",
      project_criticality: "MEDIUM",
      supplier_moq: 200,
      cashflow_tension: "MEDIUM",
    },
    {
      id_ligne: "FRONT-002",
      designation: "Groupe electrogene",
      quantite: 1,
      prix_total_ht: 100000000,
      famille: "equipement_technique",
      lot: "Lot Technique",
      volume_unitaire_m3: 18,
      poids_unitaire_kg: 8500,
      supplier_city: "Ningbo",
      shipment_status: "READY",
      project_criticality: "HIGH",
      supplier_moq: 1,
      cashflow_tension: "HIGH",
    },
  ],
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
