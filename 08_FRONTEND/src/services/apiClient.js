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
console.group("SP2I Environment");
console.log("Origin:", window.location.origin);
console.log("API_BASE_URL:", API_BASE_URL);
console.log("VITE_API_URL:", import.meta.env.VITE_API_URL);
console.log("VITE_API_BASE_URL:", import.meta.env.VITE_API_BASE_URL);
console.groupEnd();
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

apiClient.interceptors.request.use((config) => ({
  ...config,
  metadata: {
    ...(config.metadata || {}),
    startedAt: performance.now(),
  },
}));

apiClient.interceptors.response.use(
  (response) => {
    const startedAt = response.config.metadata?.startedAt || performance.now();
    console.log("AXIOS TIMING", {
      endpoint: response.config.url,
      status: response.status,
      elapsed_ms: Math.round(performance.now() - startedAt),
      timeout_ms: response.config.timeout ?? apiClient.defaults.timeout,
    });
    return response;
  },
  (error) => {
    const startedAt = error.config?.metadata?.startedAt || performance.now();
    console.error("AXIOS ERROR TIMING", {
      endpoint: error.config?.url,
      status: error.response?.status,
      elapsed_ms: Math.round(performance.now() - startedAt),
      timeout_ms: error.config?.timeout ?? apiClient.defaults.timeout,
      message: error.message,
    });
    return Promise.reject(error);
  }
);

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
  const startedAt = performance.now();
  const timeoutMs = config.timeout ?? apiClient.defaults.timeout;
  try {
    const response = await apiClient(config);
    const elapsedMs = Math.round(performance.now() - startedAt);
    console.log(config.url, response.data);
    console.log("API TIMING", {
      endpoint: config.url,
      status: response.status,
      elapsed_ms: elapsedMs,
      timeout_ms: timeoutMs,
    });
    console.log("API RESPONSE", {
      url: config.url,
      method: config.method || "GET",
      data: response.data,
    });
    return response.data;
  } catch (error) {
    const elapsedMs = Math.round(performance.now() - startedAt);
    console.error("API ERROR", {
      baseURL: API_BASE_URL,
      url: config.url,
      method: config.method || "GET",
      status: error.response?.status,
      elapsed_ms: elapsedMs,
      timeout_ms: timeoutMs,
      data: error.response?.data,
      message: error.message,
    });
    throw normalizeApiError(error, config);
  }
}
