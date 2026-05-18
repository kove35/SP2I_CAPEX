import React from "react";
import { useQueryClient } from "@tanstack/react-query";
import { analyticsFilterLabels, defaultAnalyticsFilters, useAnalyticsFilterStore } from "../stores/analyticsFilterStore";
import { normalizeAnalyticsFilters } from "../services/analyticsQueryBuilder";
import { useDashboardStore } from "../store/dashboardStore";

const chipKeys = ["projet", "scenario", "batiment", "niveau", "lot", "famille", "fournisseur", "importLocal", "dateDebut", "dateFin"];

export function useCrossFiltering() {
  const queryClient = useQueryClient();
  const filters = useAnalyticsFilterStore((state) => state.filters);
  const setFilter = useAnalyticsFilterStore((state) => state.setFilter);
  const setFilters = useAnalyticsFilterStore((state) => state.setFilters);
  const resetFilters = useAnalyticsFilterStore((state) => state.resetFilters);
  const openDrilldown = useAnalyticsFilterStore((state) => state.openDrilldown);
  const syncLegacyFilters = useDashboardStore((state) => state.setFilters);
  const resetLegacyFilters = useDashboardStore((state) => state.resetFilters);

  const normalizedFilters = React.useMemo(() => normalizeAnalyticsFilters(filters), [filters]);
  const activeChips = React.useMemo(
    () =>
      chipKeys
        .map((key) => [key, normalizedFilters[key]])
        .filter(([key, value]) => value && value !== defaultAnalyticsFilters[key])
        .map(([key, value]) => ({ key, label: analyticsFilterLabels[key] || key, value })),
    [normalizedFilters]
  );

  const invalidateAnalytics = React.useCallback(() => {
    queryClient.invalidateQueries({
      predicate: (query) => String(query.queryKey?.[0] || "").startsWith("analytics"),
    });
  }, [queryClient]);

  const applyFilter = React.useCallback(
    (key, value) => {
      setFilter(key, value);
      syncLegacyFilters({ [key]: value });
      invalidateAnalytics();
    },
    [invalidateAnalytics, setFilter, syncLegacyFilters]
  );

  const applyFilters = React.useCallback(
    (values) => {
      setFilters(values);
      syncLegacyFilters(values);
      invalidateAnalytics();
    },
    [invalidateAnalytics, setFilters, syncLegacyFilters]
  );

  const applyDrilldown = React.useCallback(
    (values, metadata = {}) => {
      setFilters(values);
      syncLegacyFilters(values);
      openDrilldown({ ...metadata, filters: values });
      invalidateAnalytics();
      window.requestAnimationFrame(() => {
        document.querySelector("[data-fact-metre-grid]")?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    },
    [invalidateAnalytics, openDrilldown, setFilters, syncLegacyFilters]
  );

  const clearFilter = React.useCallback(
    (key) => {
      const value = defaultAnalyticsFilters[key] || "";
      setFilter(key, value);
      syncLegacyFilters({ [key]: value });
      invalidateAnalytics();
    },
    [invalidateAnalytics, setFilter, syncLegacyFilters]
  );

  const reset = React.useCallback(() => {
    resetFilters();
    resetLegacyFilters();
    invalidateAnalytics();
  }, [invalidateAnalytics, resetFilters, resetLegacyFilters]);

  return {
    filters: normalizedFilters,
    activeChips,
    applyFilter,
    applyFilters,
    applyDrilldown,
    clearFilter,
    reset,
    invalidateAnalytics,
  };
}
