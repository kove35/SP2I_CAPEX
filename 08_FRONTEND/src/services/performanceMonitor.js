const now = () => (typeof performance !== "undefined" ? performance.now() : Date.now());

function ensurePerformanceObject() {
  if (typeof window === "undefined") return null;
  if (!window.SP2I_PERFORMANCE) {
    window.SP2I_PERFORMANCE = {
      api_ms: 0,
      react_ms: 0,
      charts_ms: 0,
      grid_ms: 0,
      total_ms: 0,
      request_count: 0,
      requests: {},
      component_renders: {},
      endpoint_counts: {},
      events: [],
      started_at: now(),
      app_start_at: null,
      page_ready_at: null,
      page_ready_ms: null,
    };
  }
  return window.SP2I_PERFORMANCE;
}

function addEvent(event) {
  const perf = ensurePerformanceObject();
  if (!perf) return;
  perf.events.push({ ...event, ts: now() });
}

export function initPerformanceMonitor() {
  const perf = ensurePerformanceObject();
  if (!perf) return;
  perf.app_start_at = perf.app_start_at || perf.started_at;
  addEvent({ event: "INIT_PERFORMANCE", started_at: perf.started_at });
}

export function markPerformance(label) {
  const perf = ensurePerformanceObject();
  if (!perf || typeof window.performance === "undefined" || !window.performance.mark) return;
  window.performance.mark(label);
  addEvent({ event: "PERFORMANCE_MARK", label });
}

export function measurePerformance(name, startMark, endMark) {
  const perf = ensurePerformanceObject();
  if (!perf || typeof window.performance === "undefined" || !window.performance.measure) return 0;
  try {
    window.performance.measure(name, startMark, endMark);
    const entries = window.performance.getEntriesByName(name);
    const entry = entries[entries.length - 1];
    const duration = Math.round(entry?.duration || 0);
    perf[name] = (perf[name] || 0) + duration;
    addEvent({ event: "PERFORMANCE_MEASURE", name, startMark, endMark, duration });
    return duration;
  } catch (error) {
    addEvent({ event: "PERFORMANCE_MEASURE_ERROR", name, startMark, endMark, error: String(error) });
    return 0;
  }
}

export function recordRequest(endpoint, elapsedMs, status) {
  const perf = ensurePerformanceObject();
  if (!perf) return;
  perf.request_count += 1;
  const cleaned = endpoint || "unknown";
  const state = perf.requests[cleaned] || { count: 0, total_ms: 0, last_ms: 0, status: null };
  state.count += 1;
  state.total_ms += elapsedMs;
  state.last_ms = elapsedMs;
  state.status = status;
  perf.requests[cleaned] = state;
  perf.endpoint_counts[cleaned] = state.count;
  perf.api_ms += elapsedMs;
  addEvent({ event: "REQUEST", endpoint: cleaned, elapsed_ms: elapsedMs, status });
}

export function recordComponentRender(name) {
  const perf = ensurePerformanceObject();
  if (!perf) return;
  perf.component_renders[name] = (perf.component_renders[name] || 0) + 1;
  addEvent({ event: "COMPONENT_RENDER", component: name });
}

export function recordReactStage(stage, elapsedMs) {
  const perf = ensurePerformanceObject();
  if (!perf) return;
  perf.react_ms += elapsedMs;
  addEvent({ event: "REACT_STAGE", stage, elapsed_ms: elapsedMs });
}

export function recordChartStage(elapsedMs) {
  const perf = ensurePerformanceObject();
  if (!perf) return;
  perf.charts_ms += elapsedMs;
  addEvent({ event: "CHARTS_STAGE", elapsed_ms: elapsedMs });
}

export function recordGridStage(elapsedMs) {
  const perf = ensurePerformanceObject();
  if (!perf) return;
  perf.grid_ms += elapsedMs;
  addEvent({ event: "GRID_STAGE", elapsed_ms: elapsedMs });
}

export function markPageReady() {
  const perf = ensurePerformanceObject();
  if (!perf) return;
  if (perf.page_ready_at) return;
  markPerformance("PAGE_READY");
  perf.page_ready_at = now();
  perf.page_ready_ms = Math.round(perf.page_ready_at - (perf.app_start_at || perf.started_at));
  perf.total_ms = perf.page_ready_ms;
  addEvent({ event: "PAGE_READY", page_ready_ms: perf.page_ready_ms });
}

export function getPerformanceSummary() {
  const perf = ensurePerformanceObject();
  if (!perf) return null;
  perf.total_ms = Math.round(now() - (perf.app_start_at || perf.started_at));
  return perf;
}
