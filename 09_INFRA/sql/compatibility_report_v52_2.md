# SP2I CAPEX - Compatibility Report V5.2.2 Energy Resilience

## Scope

Migration: `013_v52_2_energy_resilience.sql`

Purpose: add BAT_01 energy resilience references, facts and Power BI views without modifying existing production objects.

## Compatibility Commitments

The migration does not modify:

- `fact_metre`
- `fact_simulation`
- `fact_approvals`
- `procurement_decisions`
- backend endpoints
- frontend code
- existing Power BI reports or views
- `013_v52_generative_engine.sql`
- `013_v52_1_quantity_expansion.sql`

The migration creates only additive objects:

- `dim_energy_system`
- `dim_generator_system`
- `dim_energy_equipment`
- `fact_generator`
- `fact_generator_consumption`
- `fact_energy_resilience`
- `vw_energy_resilience_dashboard`
- `vw_generator_dashboard`
- `vw_energy_sources_dashboard`

## Dependency Chain

Recommended order:

1. `012_v51_dimensions.sql`
2. `013_v52_generative_engine.sql`
3. `013_v52_1_quantity_expansion.sql`
4. `013_v52_2_energy_resilience.sql`

V5.2.2 is intentionally independent from historical critical analytics views.

## BAT_01 Configuration

The migration seeds:

- 6 apartments
- 1263.90 m2
- 60 kWc solar
- approximately 110 panels of 550 W
- 200 kWh batteries
- recommended generator: `GEN_150KVA`
- 5000 liter fuel tank
- ATS 400A
- EMS and telegestion
- earth and lightning protection

## DQE Energy Generation

The energy DQE is exposed through `vw_energy_sources_dashboard`.

The view expands each energy equipment into detailed generated DQE components using `dqe_line_count`.

Expected additional lines:

```text
120 to +250 DQE energy lines
```

## DirectQuery Compatibility

Indexes are provided on:

- energy system code;
- generator code;
- active recommended generator;
- energy equipment by system and lot;
- generator project scope;
- generator consumption by date;
- energy resilience project scope.

Views are flat and aggregation-friendly.

## Rollback

Rollback file: `rollback_013_v52_2.sql`

Rollback strategy:

- deactivate V5.2.2 energy systems and equipment;
- preserve facts for audit;
- replace V5.2.2 views with empty-compatible views;
- no destructive drop.
