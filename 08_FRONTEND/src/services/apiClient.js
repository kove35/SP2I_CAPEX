import axios from "axios";
import { markPerformance, measurePerformance, recordRequest } from "./performanceMonitor";

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

export function buildApiUrl(path) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL.replace(/\/$/, "")}${normalizedPath}`;
}
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

let activeAnalyticsRequests = 0;
let maxConcurrentAnalyticsRequests = 0;

function now() {
  return typeof performance !== "undefined" ? performance.now() : Date.now();
}

function isAnalyticsEndpoint(url = "") {
  return String(url || "").startsWith("/analytics/");
}

apiClient.interceptors.request.use((config) => {
  const timeoutMs = config.timeout ?? apiClient.defaults.timeout;
  const endpoint = `${(config.method || "GET").toUpperCase()} ${config.url}`;
  const analyticsEndpoint = isAnalyticsEndpoint(config.url);
  if (analyticsEndpoint) {
    activeAnalyticsRequests += 1;
    maxConcurrentAnalyticsRequests = Math.max(maxConcurrentAnalyticsRequests, activeAnalyticsRequests);
    console.log("analytics_request_started", {
      endpoint: config.url,
      timestamp: new Date().toISOString(),
      active_requests: activeAnalyticsRequests,
      max_concurrent_requests: maxConcurrentAnalyticsRequests,
      timeout_ms: timeoutMs,
    });
  }
  console.log("API URL", config.baseURL || apiClient.defaults.baseURL);
  console.log("REQUEST", {
    endpoint,
    params: config.params,
    timeout_ms: timeoutMs,
  });
  markPerformance(`REQUEST_START:${endpoint}`);
  return {
    ...config,
    metadata: {
      ...(config.metadata || {}),
      startedAt: now(),
      endpoint,
      analyticsEndpoint,
    },
  };
});

apiClient.interceptors.response.use(
  (response) => {
    const startedAt = response.config.metadata?.startedAt || now();
    const endpoint = response.config.metadata?.endpoint || `${(response.config.method || "GET").toUpperCase()} ${response.config.url}`;
    const elapsedMs = Math.round(now() - startedAt);
    if (response.config.metadata?.analyticsEndpoint) {
      activeAnalyticsRequests = Math.max(activeAnalyticsRequests - 1, 0);
      console.log("analytics_request_finished", {
        endpoint: response.config.url,
        status: response.status,
        timestamp: new Date().toISOString(),
        elapsed_ms: elapsedMs,
        active_requests: activeAnalyticsRequests,
        max_concurrent_requests: maxConcurrentAnalyticsRequests,
      });
    }
    console.log("AXIOS TIMING", {
      baseURL: response.config.baseURL || apiClient.defaults.baseURL,
      endpoint,
      status: response.status,
      elapsed_ms: elapsedMs,
      timeout_ms: response.config.timeout ?? apiClient.defaults.timeout,
    });
    console.log("AXIOS RESPONSE", {
      endpoint,
      status: response.status,
      data: response.data,
    });
    recordRequest(endpoint, elapsedMs, response.status);
    markPerformance(`RESPONSE_RECEIVED:${endpoint}`);
    measurePerformance(`REQUEST_DURATION:${endpoint}`, `REQUEST_START:${endpoint}`, `RESPONSE_RECEIVED:${endpoint}`);
    return response;
  },
  (error) => {
    const startedAt = error.config?.metadata?.startedAt || now();
    const endpoint = error.config?.metadata?.endpoint || `${(error.config?.method || "GET").toUpperCase()} ${error.config?.url}`;
    const elapsedMs = Math.round(now() - startedAt);
    if (error.config?.metadata?.analyticsEndpoint) {
      activeAnalyticsRequests = Math.max(activeAnalyticsRequests - 1, 0);
      console.log("analytics_request_finished", {
        endpoint: error.config?.url,
        status: error.response?.status,
        code: error.code,
        timestamp: new Date().toISOString(),
        elapsed_ms: elapsedMs,
        active_requests: activeAnalyticsRequests,
        max_concurrent_requests: maxConcurrentAnalyticsRequests,
      });
    }
    console.error("AXIOS ERROR TIMING", {
      baseURL: error.config?.baseURL || apiClient.defaults.baseURL,
      endpoint,
      status: error.response?.status,
      elapsed_ms: elapsedMs,
      timeout_ms: error.config?.timeout ?? apiClient.defaults.timeout,
      code: error.code,
      message: error.message,
      data: error.response?.data,
    });
    recordRequest(endpoint, elapsedMs, error.response?.status || 0);
    markPerformance(`RESPONSE_RECEIVED:${endpoint}`);
    measurePerformance(`REQUEST_DURATION:${endpoint}`, `REQUEST_START:${endpoint}`, `RESPONSE_RECEIVED:${endpoint}`);
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
  const startedAt = now();
  const timeoutMs = config.timeout ?? apiClient.defaults.timeout;
  try {
    const response = await apiClient(config);
    const elapsedMs = Math.round(now() - startedAt);
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
    markPerformance(`JSON_PARSED:${config.method || "GET"} ${config.url}`);
    return response.data;
  } catch (error) {
    const elapsedMs = Math.round(now() - startedAt);
    console.error("API ERROR", {
      baseURL: API_BASE_URL,
      url: config.url,
      method: config.method || "GET",
      status: error.response?.status,
      elapsed_ms: elapsedMs,
      timeout_ms: timeoutMs,
      code: error.code,
      data: error.response?.data,
      message: error.message,
    });
    throw normalizeApiError(error, config);
  }
}
