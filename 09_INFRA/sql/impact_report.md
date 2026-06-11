# SP2I CAPEX - Impact Report 013 V5.2

## Executive Summary

`013_v52_generative_engine.sql` adds a new generative layer above the current SP2I CAPEX database.

The migration enables:

```text
PLAN
-> BIM
-> Networks
-> DQE
-> CAPEX
-> Procurement
-> Analytics
-> Power BI
```

The current production objects remain untouched.

## Functional Impact

### New Capabilities

- Generate BIM-derived quantity rows for BAT_01.
- Generate network metering for electricity, CFA, plumbing, HVAC, fire, security, solar, borehole and VRD.
- Generate a DQE-ready dataset.
- Expose generated CAPEX and network metrics to Power BI.
- Add autonomy dashboards for water, solar, energy and borehole.
- Add facade system reference data for ITE and Alucobond.

### No Direct Impact

The migration does not change:

- `/analytics/dashboard`
- `/analytics/cost-intelligence`
- `/analytics/spatial`
- procurement endpoints
- current Power BI views
- `fact_metre`
- existing dimensions

## Data Impact

New seeded dimensions:

- 10 network types
- equipment reference rows
- route rules
- generation formulas
- facade systems

New generated facts:

- `fact_generation_bim`
- `fact_generation_network`
- `fact_generation_dqe`

Autonomy facts:

- `fact_water`
- `fact_solar`
- `fact_energy`
- `fact_forage`

## Performance Impact

Indexes are created for DirectQuery and analytical filters:

- `ix_fact_generation_bim_scope`
- `ix_fact_generation_network_scope`
- `ix_fact_generation_dqe_batch_article`
- network/equipment/routing indexes
- autonomy project indexes

Expected target:

```text
< 500 ms
1 building
3 levels
6 apartments
~20,000 generated rows
```

Actual performance must be checked with:

```sql
\i 09_INFRA/sql/validation_queries_013_v52.sql
```

## Compatibility Risk

Low.

Reason:

- additive migration;
- no destructive DDL;
- no legacy view replacement;
- no backend/frontend change.

## Residual Risks

- Migration 013 depends on `dim_type_piece` from migration 012.
- If legacy `dim_piece` has incomplete `piece_id` mapping, generated rows still work but some Power BI labels may fall back to IDs or type piece.
- Generated CAPEX is a V5.2 planning estimate, not a replacement for `fact_metre`.
- The rollback is intentionally non-destructive, so generated data is preserved unless manually archived later.

## Recommended Deployment Order

1. Backup Neon or create branch.
2. Run `012_v51_dimensions.sql` if not already applied.
3. Run `013_v52_generative_engine.sql`.
4. Run `validation_queries_013_v52.sql`.
5. Verify legacy endpoints:
   - `/analytics/dashboard`
   - `/analytics/cost-intelligence`
   - `/analytics/debug/database`
6. Connect Power BI only to new V5.2 views for the generative layer.

## Success Criteria

- Legacy object safety report returns all `OK`.
- V5.2 generated views return rows.
- `vw_sp2i_generated_capex` returns a non-zero generated CAPEX.
- Existing `vw_capex_summary` remains unchanged.
- Existing cockpit KPI still matches `fact_metre`.
