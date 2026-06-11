# SP2I CAPEX - Rollback Plan 023

Rollback target: return Analytics reads to the historical model without deleting V5.3 objects.

## Immediate Backend Rollback

Set Render environment variable:

```text
SP2I_FACT_SOURCE=fact_metre
```

Redeploy or restart backend.

Expected effect:

- Analytics reads return to historical `fact_metre`.
- Writes remain unchanged.
- No Neon data deletion.
- V5.3 views can remain in place for investigation.

## Power BI Rollback

Option A: return only backend reads to historical mode and keep Power BI V5.3 for inspection.

Option B: restore historical Power BI views by re-running one baseline:

```text
09_INFRA/sql/011_powerbi_neon_integrity_fix.sql
```

or:

```text
sql/powerbi/001_powerbi_views.sql
```

Choose the baseline that matches the desired historical reporting contract.

## Verification After Rollback

```sql
SELECT COUNT(*) FROM fact_metre;
SELECT COUNT(DISTINCT lot) FROM fact_metre;
```

Expected:

- 290 rows
- 7 lots

Backend endpoints to retest:

- `/health`
- `/analytics/dashboard`
- `/analytics/cost-intelligence`
- `/analytics/spatial`
- `/analytics/spatial/dashboard`

## Non-Destructive Guarantees

Rollback does not require:

- `DROP TABLE`
- `TRUNCATE`
- `DELETE`
- `UPDATE fact_metre`
- changing imports DQE
- changing historical pipeline
- changing historical simulation
- changing historical procurement

## Estimated Time

- Backend env rollback and redeploy: 5 to 10 minutes.
- Power BI metadata refresh: 5 to 15 minutes.
- Full validation: 15 to 30 minutes.
