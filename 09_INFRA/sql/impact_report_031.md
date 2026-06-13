# Impact Report 031 - V6 Financial Production Readiness

## Executive Summary

Phase 031 prepares the V6 financial engine in parallel with the existing V5/V5.3 stack. It creates a governed pricing layer, recalculates direct CAPEX from the canonical consolidated DQE, and adds Total Project Cost views for Direction and Power BI.

No existing production view is replaced.

## Financial Baseline

| Metric | Value |
|---|---:|
| V5.3 raw CAPEX before consolidation | 145,494,512,580 FCFA |
| Canonical CAPEX after 026A | 4,353,910,380 FCFA |
| Simulated CAPEX after 029B | 1,211,507,240 FCFA |
| Simulated CAPEX after P1/P2 pricing rebuild | 724,383,183 FCFA |
| Surface | 1,263.90 m2 |
| Target direct CAPEX/m2 | 573,133 FCFA/m2 |

## V6 Project Cost Model

`vw_project_cost_summary` transforms direct CAPEX into Total Project Cost using the Phase 030 assumptions.

| Component | Rate | Expected amount based on 724,383,183 FCFA |
|---|---:|---:|
| CAPEX_DIRECT | 100.00% | 724,383,183 FCFA |
| INDIRECT_COSTS | 11.00% | 79,682,150 FCFA |
| SITE_INSTALLATION | 4.20% | 30,424,094 FCFA |
| IMPORT_LOGISTICS | 3.50% | 25,353,411 FCFA |
| CONTINGENCY | 12.00% of subtotal | 103,181,141 FCFA |
| TOTAL_PROJECT_COST | n/a | 963,023,979 FCFA |

Expected KPI:

| KPI | Value |
|---|---:|
| Total Project Cost / m2 | 761,946 FCFA/m2 |
| Total Project Cost / appartement | 160,503,996 FCFA |
| Total Project Cost / niveau | 321,007,993 FCFA |
| Recommended investor budget | about 1.0 B FCFA |

## Analytics Impact

| Consumer | Existing behavior | V6 impact |
|---|---|---|
| `/analytics/dashboard` | Current configured source | No automatic change |
| `/analytics/cost-intelligence` | Current financial source | No automatic change unless wired to V6 |
| Spatial Analytics | `vw_fact_metre_current` | No change |
| Drilldown BIM | `vw_fact_metre_current` | No change |
| Heatmap | `vw_fact_metre_current` | No change |
| Timeline | Current source | No change |

Phase 031 provides the V6 data contract but does not alter backend routing.

## Power BI Impact

New importable views:

- `vw_project_cost_summary`
- `vw_dashboard_direction_v6`
- `vw_cost_intelligence_v6`

Existing Power BI views remain unchanged. A Power BI refresh can add V6 views without breaking the current model.

Recommended Power BI rollout:

1. Import V6 views into a copy of the production dataset.
2. Build a Direction V6 page using `vw_project_cost_summary`.
3. Compare V5/V6 totals side by side.
4. Promote V6 visuals only after finance validation.

## Procurement Impact

Phase 031 is read-only from the procurement workflow perspective:

- No change to `procurement_decisions`.
- No change to approvals.
- No change to simulations.
- No supplier order is recalculated automatically.

Procurement can use V6 views for decision support after validation.

## Pricing Impact

V6 pricing source priority:

1. Article mapping
2. Family mapping
3. Unit mapping
4. Lot fallback
5. Legacy V5 price as emergency fallback

The key production criterion is that `fallback_legacy_lot_pct` remains below 5% of direct CAPEX.

## Operational Risks

| Risk | Level | Comment |
|---|---|---|
| Budgetary unit prices need supplier validation | Medium | V6 is operational but not a signed supplier BPU |
| Broad family matching may overmatch rare article names | Medium | Exposed by `price_reference_code` and `pricing_scope` |
| V6 Power BI adoption requires dataset changes | Low | Existing views are untouched |
| Total Project Cost rates are assumptions | Medium | Rates should be approved by Direction |

## Rollback

Use `rollback_031.sql`.

Rollback removes only:

- `vw_cost_intelligence_v6`
- `vw_dashboard_direction_v6`
- `vw_project_cost_summary`
- `vw_bpu_v53_priced_v2`

It intentionally preserves:

- `dim_price_reference`
- `dim_article_price_mapping`
- all V5/V5.3 views
- all fact tables

## Deployment Order

1. Apply `031_v6_production_readiness.sql`.
2. Run `validation_queries_031.sql`.
3. Review `fallback_legacy_lot_pct`.
4. Validate Direction KPIs with finance.
5. Add V6 views to Power BI as parallel tables.
6. Only then decide whether backend endpoints should expose V6.

## Verdict

`PRODUCTION_READY` for parallel V6 deployment.

`REQUIRES_ADJUSTMENT` before replacing any current production source, because supplier-level price validation and Power BI acceptance remain required.
