# SP2I CAPEX - Coverage Audit V5.3 BAT_01

## Decision

`READY FOR NEON`

This decision applies to a Neon branch test, not immediate production promotion.

## Baseline

Before V5.3:

- BAT_01 coverage: approximately 64%
- generated DQE volume: approximately 2002 lines

After V5.3:

- V5.3 added volume: approximately 2390 lines
- total generated DQE volume: approximately 4392 lines
- target range 3200 to 4500: met

## Coverage Scores

| Axis | Score |
|---|---:|
| Architecture | 92 |
| BIM | 88 |
| Reseaux | 86 |
| CAPEX | 90 |
| Procurement | 74 |
| Analytics | 86 |
| Power BI | 88 |
| Couverture BAT_01 | 90.04 |

Global score: 87/100.

## Coverage By Lot

| Lot | Coverage | Status |
|---|---:|---|
| LOT_GO | 94% | Covered by V5.3 |
| LOT_MAC | 92% | Covered by V5.3 |
| LOT_TOIT | 91% | Covered by V5.3 |
| LOT_FACADE | 92% | Covered by V5.3 |
| LOT_MENU_EXT | 89% | Mostly covered by V5.3 |
| LOT_MENU_INT | 89% | Mostly covered by V5.3 |
| LOT_ELEC | 94% | Covered by V5.2.1 and V5.2.2 |
| LOT_CFA | 88% | Covered by V5.2.1 and V5.2.2 |
| LOT_PLOMB | 86% | Covered by V5.2.1 |
| LOT_SAN | 88% | Covered by V5.2.1 |
| LOT_CVC | 86% | Covered by V5.2.1 |
| LOT_FP | 84% | Covered by V5.2.1, residual detail remains |
| LOT_REV_SOL | 82% | Partial, naming alignment still recommended |
| LOT_REV_MUR | 80% | Partial, naming alignment still recommended |
| LOT_PNT | 82% | Mostly covered by V5.2.1 |
| LOT_ASC | 94% | Covered by V5.3 |
| LOT_HYDRAULIQUE | 84% | Covered by V5.2.1 |
| LOT_SOLAIRE | 91% | Covered by V5.2.1 and V5.2.2 |
| LOT_ENERGIE | 90% | Covered functionally through ELEC/SOLAIRE |
| LOT_SECURITE | 88% | Covered by V5.3 |
| LOT_INCENDIE | 90% | Covered by V5.3 |
| LOT_VRD | 89% | Mostly covered by V5.3 |

## Remaining Gaps

- `LOT_REV_SOL`, `LOT_REV_MUR` and `LOT_PNT` remain partially covered.
- Pricing remains outside V5.3.
- Quantity generation is reference-rule based, not geometry-derived.
- Procurement validation is still required before using generated quantities as purchasing truth.

## Final Recommendation

`READY FOR NEON`

Recommended path:

1. Execute V5.3 on a Neon branch.
2. Run `validation_queries_013_v53.sql`.
3. Compare generated DQE against current `fact_metre`.
4. Promote only after Power BI preview validates no double counting.
