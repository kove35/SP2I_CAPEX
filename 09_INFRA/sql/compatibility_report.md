# SP2I CAPEX - Compatibility Report 013 V5.2

## Scope

Migration: `013_v52_generative_engine.sql`

Objective: add the V5.2 generative layer without changing the current SP2I production architecture.

## Compatibility Commitments

The migration is additive only.

It does not:

- drop existing tables;
- drop existing views;
- rename existing objects;
- alter existing tables destructively;
- modify FastAPI endpoints;
- modify frontend code;
- modify existing Power BI views.

## Preserved Legacy Objects

The migration explicitly checks the following objects through `vw_sp2i_v52_migration_safety`:

- `fact_metre`
- `fact_simulation`
- `fact_shipment`
- `fact_logistics_cost`
- `fact_approvals`
- `procurement_decisions`
- `dim_batiment`
- `dim_niveau`
- `dim_appartement`
- `dim_piece`
- `dim_lot`
- `dim_sous_lot`
- `dim_famille`
- `dim_article_bpu`
- `vw_capex_summary`
- `vw_bim_dashboard`
- `vw_dim_lot_active`
- `vw_dim_sous_lot_active`
- `vw_dim_article_bpu_active`

## New V5.2 Objects

Dimensions:

- `dim_network_type`
- `dim_equipment`
- `dim_route_rule`
- `dim_generation_formula`
- `dim_facade_system`

Facts:

- `fact_generation_bim`
- `fact_generation_network`
- `fact_generation_dqe`
- `fact_water`
- `fact_solar`
- `fact_energy`
- `fact_forage`

Power BI views:

- `vw_sp2i_generated_dqe`
- `vw_sp2i_generated_networks`
- `vw_sp2i_generated_capex`
- `vw_energy_dashboard`
- `vw_water_dashboard`
- `vw_autonomy_dashboard`
- `vw_facade_dashboard`

Audit views:

- `vw_sp2i_v52_compatibility_report`
- `vw_sp2i_v52_migration_safety`

## Dependency on 012

Migration 013 expects migration 012 to be installed first because it uses:

- `dim_type_piece`

If `dim_type_piece` is missing, run:

```sql
\i 09_INFRA/sql/012_v51_dimensions.sql
```

then run:

```sql
\i 09_INFRA/sql/013_v52_generative_engine.sql
```

## DirectQuery Readiness

The new Power BI views are flat, explicit and aggregation friendly.

Indexes are added on:

- generation batch;
- appartement;
- piece;
- type piece;
- network type;
- equipment;
- article code;
- autonomy project/batiment keys.

Target performance: under 500 ms for BAT_01 scale and about 20,000 generated rows, subject to Neon plan, cache state and concurrent load.

## Rollback Strategy

Rollback file: `rollback_013_v52.sql`

The rollback is non-destructive. It:

- marks V5.2 rules and dimensions inactive;
- replaces V5.2 views with empty-compatible views;
- keeps generated data for audit;
- does not drop any table or view.

This matches the project rule: no `DROP TABLE`, no `DROP VIEW`.
