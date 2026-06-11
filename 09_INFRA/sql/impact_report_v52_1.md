# SP2I CAPEX - Impact Report V5.2.1 Quantity Expansion

## Executive Summary

V5.2.1 increases the granularity of generated DQE quantities without changing the existing SP2I production model.

It turns high-level generated equipment into detailed article quantities.

```text
Before:
PRISE_16A -> 1 DQE line

After:
PRISE_16A -> prise + cable + gaine + boite + tableau + protection + reperage
```

## Expected Functional Gain

The generated dataset becomes closer to a real DQE:

- electricity decomposed into devices, cabling, conduits, boxes and protections;
- CFA decomposed into sockets, cables, conduits and rack shares;
- plumbing and sanitary decomposed into fixtures, water supply, drainage, fittings and joints;
- HVAC decomposed into indoor units, copper lines, condensate, power and support;
- finishing lots added through surface-based expansions;
- solar and borehole rules prepared for future global generation.

## Estimated BAT_01 Volume

Based on V5.2 rules:

```text
6 apartments
~216 base generation rows
~1500-3000 detailed generated quantity rows
```

The validation script checks the target range:

```sql
\i 09_INFRA/sql/validation_queries_013_v52_1.sql
```

## Power BI Impact

New views only:

- `vw_sp2i_generated_quantities`
- `vw_sp2i_generated_network_quantities`

Existing Power BI views remain unchanged.

Recommended usage:

- use `vw_sp2i_generated_quantities` for generated DQE detail;
- use `vw_sp2i_generated_network_quantities` for network metering and line density;
- keep `fact_metre` for validated/current CAPEX.

## CAPEX Double Counting Risk

Risk: medium if Power BI adds generated quantities to `fact_metre` in the same KPI.

Mitigation:

- label generated quantities as `DQE genere / previsionnel`;
- never combine generated CAPEX and `fact_metre` CAPEX unless the measure explicitly compares scenarios;
- use separate pages or separate measure folders.

## Technical Risk

Low.

Reasons:

- no writes to historical fact tables;
- no mutation of existing dimensions;
- idempotent inserts;
- unique constraint prevents duplicated expanded article per generated source line.

## Residual Limitations

- The expansion is rule-based, not yet plan-geometry aware.
- Network rows are estimated from quantities and lengths; detailed route topology remains a future layer.
- `fact_generation_dqe` from V5.2 remains unchanged; V5.2.1 detail lives in `fact_generation_expansion`.

## Deployment Recommendation

1. Run on a Neon branch first.
2. Validate row counts.
3. Validate Power BI preview on the two new views.
4. Promote to production if:
   - detailed generated quantities are between 1500 and 3000 rows;
   - duplicate query returns zero rows;
   - existing `/analytics/dashboard` remains unchanged.
