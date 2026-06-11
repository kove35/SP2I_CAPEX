# SP2I CAPEX - Compatibility Report V5.3 Building Completion

## Scope

Migration: `013_v53_building_completion.sql`

Purpose: increase BAT_01 generated DQE coverage from approximately 64% to more than 90% by adding missing building, envelope and special systems lots.

## Compatibility Commitments

The migration does not modify:

- `fact_metre`
- `fact_simulation`
- `fact_approvals`
- `procurement_decisions`
- backend endpoints
- frontend code
- existing Power BI reports or views
- V5.1, V5.2, V5.2.1 or V5.2.2 migration files

The migration creates additive objects only.

## Objects Created

Dimensions:

- `dim_go_component`
- `dim_maconnerie_component`
- `dim_toiture_component`

Facts:

- `fact_generation_go`
- `fact_generation_maconnerie`
- `fact_generation_toiture`
- `fact_generation_facade`
- `fact_generation_menu_ext`
- `fact_generation_menu_int`
- `fact_generation_ascenseur`
- `fact_generation_incendie`
- `fact_generation_securite`
- `fact_generation_vrd`

Views:

- `vw_sp2i_generated_building`
- `vw_sp2i_generated_envelope`
- `vw_sp2i_generated_special_systems`

## Dependency Chain

Recommended order:

1. `012_v51_dimensions.sql`
2. `013_v52_generative_engine.sql`
3. `013_v52_1_quantity_expansion.sql`
4. `013_v52_2_energy_resilience.sql`
5. `013_v53_building_completion.sql`

V5.3 does not depend on historical critical analytics views.

## DirectQuery Compatibility

Indexes are provided on:

- generation batch;
- lot code;
- component code;
- active rows where relevant.

The views are flat and aggregation-friendly.

## Rollback

Rollback file: `rollback_013_v53.sql`

Rollback strategy:

- deactivate V5.3 active fact rows and component dimensions;
- preserve generated data for audit;
- replace V5.3 views with empty-compatible views;
- no destructive drop.
