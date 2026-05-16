import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

export function normalizeApiError(error) {
  const detail = error.response?.data?.detail || error.response?.data?.message || error.response?.data?.error;
  return new Error(detail || error.message || "Erreur API inconnue");
}

export async function request(config) {
  try {
    const response = await apiClient(config);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
