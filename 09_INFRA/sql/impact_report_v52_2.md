# SP2I CAPEX - Impact Report V5.2.2 Energy Resilience

## Executive Summary

V5.2.2 adds a dedicated BAT_01 energy resilience layer without changing the current SP2I CAPEX, Analytics, Procurement or Power BI production model.

It models:

- public E2C grid;
- photovoltaic solar;
- batteries;
- 150 kVA generator;
- ATS;
- EMS;
- earth system;
- lightning protection;
- remote monitoring.

## Functional Gain

BAT_01 can now be evaluated on:

- solar installed power;
- battery autonomy;
- fuel autonomy;
- total energy resilience;
- solar coverage ratio;
- generated energy DQE lines;
- generator operation and consumption.

## Expected BAT_01 Setup

```text
Surface: 1263.90 m2
Apartments: 6
Solar: 60 kWc
Panels: ~110 x 550 W
Batteries: 200 kWh
Generator: GEN_150KVA
Fuel tank: 5000 liters
```

## Expected DQE Energy Volume

The migration exposes detailed energy quantities through:

- `vw_energy_sources_dashboard`

Expected additional DQE lines:

```text
120 to +250 lines
```

This volume is intentionally separated from `fact_metre` and from V5.2/V5.2.1 generated facts to prevent accidental CAPEX double counting.

## Power BI Impact

New views only:

- `vw_energy_resilience_dashboard`
- `vw_generator_dashboard`
- `vw_energy_sources_dashboard`

Existing Power BI views remain unchanged.

Recommended usage:

- use `vw_energy_resilience_dashboard` for executive KPIs;
- use `vw_generator_dashboard` for generator monitoring and fuel cost;
- use `vw_energy_sources_dashboard` for detailed generated energy DQE.

## CAPEX Double Counting Risk

Risk: medium if generated energy DQE is added to current `fact_metre` CAPEX in the same measure.

Mitigation:

- label this dataset as `DQE energie genere / previsionnel`;
- keep current validated CAPEX on `fact_metre`;
- create dedicated Power BI measure folders for resilience scenarios;
- only compare generated DQE against current CAPEX through explicit scenario measures.

## Technical Risk

Low.

Reasons:

- no writes to critical historical fact tables;
- no mutation of existing dimensions;
- no dependency on critical historical views;
- idempotent inserts;
- non-destructive rollback.

## Residual Limitations

- Energy DQE lines are rule/reference based, not yet priced against a validated BPU.
- Solar production and autonomy are engineering estimates.
- Detailed electrical single-line diagram and physical routing remain a future engineering layer.

## Deployment Recommendation

1. Run on a Neon branch first.
2. Execute `validation_queries_013_v52_2.sql`.
3. Confirm `vw_energy_sources_dashboard` returns between 120 and 250 rows.
4. Validate that `/analytics/dashboard` remains unchanged.
5. Promote to production if validation is green.
