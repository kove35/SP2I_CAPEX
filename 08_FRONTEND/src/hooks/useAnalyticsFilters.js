import React from "react";
import { analyticsFilterLabels, defaultAnalyticsFilters, useAnalyticsFilterStore } from "../stores/analyticsFilterStore";
import { buildAnalyticsParams, normalizeAnalyticsFilters } from "../services/analyticsQueryBuilder";

const urlKeys = Object.keys(defaultAnalyticsFilters);

function readFiltersFromUrl() {
  if (typeof window === "undefined") return {};
  const params = new URLSearchParams(window.location.search);
  return urlKeys.reduce((values, key) => {
    if (params.has(key)) values[key] = params.get(key) || "";
    return values;
  }, {});
}

function writeFiltersToUrl(filters) {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  urlKeys.forEach((key) => {
    const value = filters[key];
    if (value && value !== defaultAnalyticsFilters[key]) url.searchParams.set(key, value);
    else url.searchParams.delete(key);
  });
  window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
}

function useDebouncedValue(value, delay = 280) {
  const [debounced, setDebounced] = React.useState(value);
  React.useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

export function useAnalyticsFilters() {
  const filters = useAnalyticsFilterStore((state) => state.filters);
  const setFilter = useAnalyticsFilterStore((state) => state.setFilter);
  const setFilters = useAnalyticsFilterStore((state) => state.setFilters);
  const replaceFilters = useAnalyticsFilterStore((state) => state.replaceFilters);
  const resetFilters = useAnalyticsFilterStore((state) => state.resetFilters);

  React.useEffect(() => {
    const hydrate = () => {
      const fromUrl = readFiltersFromUrl();
      if (Object.keys(fromUrl).length) replaceFilters({ ...defaultAnalyticsFilters, ...fromUrl });
    };
    hydrate();
    window.addEventListener("popstate", hydrate);
    return () => window.removeEventListener("popstate", hydrate);
  }, [replaceFilters]);

  React.useEffect(() => {
    writeFiltersToUrl(filters);
  }, [filters]);

  const normalizedFilters = React.useMemo(() => normalizeAnalyticsFilters(filters), [filters]);
  const debouncedFilters = useDebouncedValue(normalizedFilters);
  const queryParams = React.useMemo(() => buildAnalyticsParams(debouncedFilters), [debouncedFilters]);
  const activeChips = React.useMemo(
    () =>
      Object.entries(normalizedFilters)
        .filter(([key, value]) => value && value !== defaultAnalyticsFilters[key])
        .map(([key, value]) => ({ key, label: analyticsFilterLabels[key] || key, value })),
    [normalizedFilters]
  );

  const removeFilter = React.useCallback((key) => setFilter(key, defaultAnalyticsFilters[key] || ""), [setFilter]);

  return {
    filters: normalizedFilters,
    debouncedFilters,
    queryParams,
    activeChips,
    setFilter,
    setFilters,
    removeFilter,
    resetFilters,
  };
}
