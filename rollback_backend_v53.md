# Rollback Backend V5.3

Objectif: revenir aux lectures backend historiques sans modifier les faits.

## Procedure

1. Remettre la variable d'environnement:

```text
SP2I_FACT_SOURCE=fact_metre
```

2. Redeployer le backend Render.

3. Verifier la source active:

```sql
SELECT COUNT(*) FROM fact_metre;
SELECT COUNT(DISTINCT lot) FROM fact_metre;
```

4. Tester les endpoints:

- `GET /health`
- `GET /analytics/dashboard`
- `GET /analytics/cost-intelligence`
- `GET /analytics/spatial`

## Effet attendu

- Analytics relit `fact_metre`.
- Les vues/tables V5.3 restent intactes.
- `fact_metre`, `fact_simulation`, `fact_approvals` et `procurement_decisions` ne sont pas modifiees.
