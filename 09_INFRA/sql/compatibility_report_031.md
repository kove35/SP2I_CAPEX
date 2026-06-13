# Compatibility Report 031 - V6 Production Readiness

## Scope

Phase 031 introduces a parallel V6 financial layer. It does not replace or drop the V5/V5.3 objects currently used in production.

## Objects Created

| Object | Type | Purpose |
|---|---|---|
| `dim_price_reference` | Table | Budgetary price reference by article, family, unit, or lot |
| `dim_article_price_mapping` | Table | Deterministic mapping between V5.3 BPU articles and price references |
| `vw_bpu_v53_priced_v2` | View | V6 priced BPU with explicit pricing source and fallback visibility |
| `vw_project_cost_summary` | View | Total Project Cost summary for Direction cockpit |
| `vw_dashboard_direction_v6` | View | Power BI / cockpit direction V6 lot-level dashboard |
| `vw_cost_intelligence_v6` | View | V6 financial analytics by lot, sous-lot, article, unit, and pricing source |

## Objects Preserved

| Object | Status |
|---|---|
| `vw_bpu_v53_priced` | Preserved |
| `vw_fact_metre_current` | Preserved |
| `vw_fact_metre_financial_canonical` | Preserved |
| `fact_metre` | Not modified |
| `fact_simulation` | Not modified |
| `fact_approvals` | Not modified |
| `procurement_decisions` | Not modified |

## Parallel Mode

Phase 031 creates V6 as a parallel financial layer:

- V5 current reads can continue through `vw_fact_metre_current`.
- Canonical consolidated V5.3 remains available through `vw_fact_metre_financial_canonical`.
- V6 financial views are exposed through dedicated names ending in `_v6` or `_v2`.

No production pointer is switched by this migration.

## Backend Compatibility

No backend file is required for Phase 031 to be valid. Existing endpoints continue to read their configured sources:

| Area | Current source | Phase 031 impact |
|---|---|---|
| Spatial Analytics | `SP2I_FACT_SOURCE` / `vw_fact_metre_current` | None |
| Drilldown / Heatmap | `SP2I_FACT_SOURCE` / `vw_fact_metre_current` | None |
| Cost Intelligence current | `SP2I_FINANCIAL_SOURCE` when configured | None unless explicitly switched |
| Direction V6 | `vw_dashboard_direction_v6` | New optional source |
| Cost Intelligence V6 | `vw_cost_intelligence_v6` | New optional source |

## Power BI Compatibility

Phase 031 does not modify existing Power BI views. It adds V6 views that can be imported as additional tables:

- `vw_dashboard_direction_v6`
- `vw_cost_intelligence_v6`
- `vw_project_cost_summary`

Existing Power BI reports can continue to use:

- `vw_cost_intelligence`
- `vw_spatial_dashboard`
- `vw_spatial_analytics`
- `vw_dashboard_direction`

## Direction Cockpit Fields

`vw_project_cost_summary` exposes the requested project cost fields:

| Field | Status |
|---|---|
| `capex_direct` | Present |
| `indirect_costs` | Present |
| `site_installation` | Present |
| `import_logistics` | Present |
| `contingency` | Present |
| `total_project_cost` | Present |

The same project-level fields are also propagated into `vw_dashboard_direction_v6`.

## Compatibility Risks

| Risk | Level | Mitigation |
|---|---|---|
| Budgetary V6 prices require supplier validation | Medium | Expose `pricing_confidence` and `price_reference_code` |
| Mapping rules may miss unusual article designations | Medium | Validation checks fallback percentage |
| Existing BI models do not automatically consume V6 views | Low | Parallel import, no breaking change |
| V6 summary uses fixed Phase 030 rates | Medium | Rates are visible in `vw_project_cost_summary` |

## Validation Required Before Production

Run `validation_queries_031.sql` after applying the migration on a validation database.

Blocking expectations:

- `vw_fact_metre_financial_canonical` remains at 1298 lines.
- 198 canonical articles.
- 18 lots.
- V6 local/import/optimized prices are all positive.
- `fallback_legacy_lot_pct < 5`.
- `capex_direct > 0`.
- `total_project_cost > 0`.

## Verdict

`PRODUCTION_READY` for a parallel V6 deployment, subject to successful execution of `validation_queries_031.sql` in Neon validation/prod.
