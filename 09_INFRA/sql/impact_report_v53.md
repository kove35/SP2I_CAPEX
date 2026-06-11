# SP2I CAPEX - Impact Report V5.3 Building Completion

## Executive Summary

V5.3 completes BAT_01 generated DQE coverage by adding the under-covered lots identified during the V5.2.1 + V5.2.2 audit.

It adds:

- gros oeuvre N3;
- maconnerie;
- toiture terrasse;
- facade ITE + Alucobond;
- menuiseries exterieures;
- menuiseries interieures;
- ascenseur;
- incendie;
- securite;
- VRD.

## Expected Volume

Before V5.3:

```text
~2002 generated DQE lines
```

V5.3 additional generated lines:

```text
~2390 generated DQE lines
```

After V5.3:

```text
~4392 generated DQE lines
```

The target range of 3200 to 4500 generated DQE lines is met.

## Expected Coverage Gain

Before V5.3:

```text
BAT_01 coverage ~= 64%
```

After V5.3:

```text
BAT_01 coverage ~= 90%+
```

## Power BI Impact

New views only:

- `vw_sp2i_generated_building`
- `vw_sp2i_generated_envelope`
- `vw_sp2i_generated_special_systems`

Existing Power BI views remain unchanged.

## CAPEX Double Counting Risk

Risk: medium if generated V5.3 quantities are added to validated `fact_metre` CAPEX in the same KPI.

Mitigation:

- label V5.3 as `DQE genere / previsionnel`;
- keep current validated CAPEX on `fact_metre`;
- compare generated and validated CAPEX only through explicit scenario measures;
- avoid merging generated quantities into procurement decisions without validation.

## Technical Risk

Low.

Reasons:

- no writes to critical historical fact tables;
- no mutation of existing production dimensions;
- idempotent inserts;
- additive views only;
- non-destructive rollback.

## Residual Limitations

- Quantities are rule/reference based, not produced from a geometric model.
- Pricing is not attached to the V5.3 facts.
- Detailed structural engineering validation remains required for GO and facade.

## Deployment Recommendation

1. Run on a Neon branch first.
2. Execute `validation_queries_013_v53.sql`.
3. Confirm total theoretical lines are between 3200 and 4500.
4. Validate that existing `/analytics/dashboard` remains unchanged.
5. Promote if validation is green.
