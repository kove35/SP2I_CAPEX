# SP2I CAPEX - Compatibility Report V5.2.1 Quantity Expansion

## Scope

Migration: `013_v52_1_quantity_expansion.sql`

Purpose: expand V5.2 generative equipment into detailed DQE quantity lines.

## Compatibility Commitments

The migration does not modify:

- `fact_metre`
- `fact_simulation`
- `fact_approvals`
- `procurement_decisions`
- backend endpoints
- frontend code
- existing Power BI reports or views

The migration creates only:

- `dim_quantity_expansion_rule`
- `fact_generation_expansion`
- `vw_sp2i_generated_quantities`
- `vw_sp2i_generated_network_quantities`

## Dependency Chain

Required before V5.2.1:

1. `012_v51_dimensions.sql`
2. `013_v52_generative_engine.sql`

V5.2.1 reads:

- `fact_generation_bim`
- `dim_type_piece`

V5.2.1 writes only:

- `dim_quantity_expansion_rule`
- `fact_generation_expansion`

## DQE Expansion Logic

One V5.2 equipment line becomes several detailed DQE lines.

Example:

```text
PRISE_16A
-> PRISE_16A
-> CABLE_3G2_5
-> GAINE_ICTA20
-> BOITE_ENCASTREMENT
-> CONNECTEUR_PRISE
-> QUOTE_PART_TABLEAU_PRISE
-> QUOTE_PART_DISJONCTEUR_16A
-> REPERE_CIRCUIT_PRISE
```

## Expected Volume

Current V5.2 base:

```text
fact_generation_bim ~= 216 rows
```

V5.2.1 target:

```text
fact_generation_expansion / vw_sp2i_generated_quantities: 1500-3000 rows
```

The generated quantity view becomes the recommended Power BI source for detailed generated DQE.

## DirectQuery Compatibility

Indexes are provided on:

- active expansion rules by `equipment_code`;
- generated article code;
- generated batch and lot;
- generation id.

The views are flat and aggregation-friendly.

## Rollback

Rollback file: `rollback_013_v52_1.sql`

Rollback strategy:

- deactivate expansion rules;
- preserve generated rows for audit;
- replace V5.2.1 views with empty-compatible views;
- no destructive drop.
