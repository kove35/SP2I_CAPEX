import axios from "axios";

export const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

export function normalizeApiError(error) {
  if (!error.response) {
    return new Error(
      `Impossible de joindre l'API SP2I (${API_BASE_URL}). Verifie VITE_API_URL, le deploiement Render et CORS_ORIGINS.`
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
    throw normalizeApiError(error);
  }
}
