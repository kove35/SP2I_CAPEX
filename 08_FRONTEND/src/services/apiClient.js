import axios from "axios";

const isLocalBrowser =
  typeof window !== "undefined" &&
  ["localhost", "127.0.0.1"].includes(window.location.hostname);

const DEFAULT_API_URL = isLocalBrowser
  ? "http://localhost:8000"
  : "https://sp2i-backend.onrender.com";

export const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  DEFAULT_API_URL;

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

export function normalizeApiError(error, config = {}) {
  const endpoint = config.url || "endpoint inconnu";

  if (error.code === "ECONNABORTED") {
    return new Error(
      `Temps d'attente depasse pour ${endpoint}. Render peut encore traiter la demande, surtout sur analyse ou synchronisation volumineuse.`
    );
  }

  if (!error.response) {
    return new Error(
      `Connexion interrompue sur ${endpoint}. Si l'import fonctionne, le probleme vient probablement de cette action precise et non de l'API globale.`
    );
  }

  const detail = error.response?.data?.detail || error.response?.data?.message || error.response?.data?.error;
  return new Error(detail || error.message || `Erreur API HTTP ${error.response.status}`);
}

export async function request(config) {
  try {
    const response = await apiClient(config);
    console.log("API RESPONSE", {
      url: config.url,
      method: config.method || "GET",
      data: response.data,
    });
    return response.data;
  } catch (error) {
    console.error("API ERROR", {
      baseURL: API_BASE_URL,
      url: config.url,
      method: config.method || "GET",
      status: error.response?.status,
      data: error.response?.data,
      message: error.message,
    });
    throw normalizeApiError(error, config);
  }
}
