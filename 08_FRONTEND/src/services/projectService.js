import { getStoredSession } from "./authService";
import { request } from "./apiClient";

export const demoProjects = [
  {
    id: "demo-pnr-medical",
    name: "Centre medical Pointe-Noire",
    client_name: "SP2I",
    city: "Pointe-Noire",
    country: "Congo-Brazzaville",
    currency: "FCFA",
    status: "ACTIVE",
    trust_score: 87,
    last_dqe: "DQE_PROJECT_SP2I.xlsx",
    budget: 1129667152,
    updated_at: "Derniere synchronisation governance",
  },
  {
    id: "demo-brazza-clinic",
    name: "Clinique pilote Brazzaville",
    client_name: "Investisseur prive",
    city: "Brazzaville",
    country: "Congo-Brazzaville",
    currency: "FCFA",
    status: "REVIEW",
    trust_score: 72,
    last_dqe: "DQE a importer",
    budget: 0,
    updated_at: "Workspace pret",
  },
];

function authHeaders() {
  const session = getStoredSession();
  if (!session?.access_token || session.token_type === "demo") return {};
  return { Authorization: `Bearer ${session.access_token}` };
}

export async function listProjects() {
  const session = getStoredSession();
  if (!session || session.token_type === "demo") return { projects: demoProjects };
  try {
    return await request({ url: "/projects", headers: authHeaders() });
  } catch {
    return { projects: demoProjects };
  }
}

export async function createProject(payload) {
  const session = getStoredSession();
  if (!session || session.token_type === "demo") {
    return { ...payload, id: `local-${Date.now()}`, trust_score: 60, last_dqe: "DQE a importer", budget: 0 };
  }
  return request({ url: "/projects", method: "POST", data: payload, headers: authHeaders() });
}
