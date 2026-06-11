# Validation Backend V5.3

Objectif: verifier la bascule de lecture backend via `SP2I_FACT_SOURCE`.

## Mode historique

Variable:

```text
SP2I_FACT_SOURCE=fact_metre
```

Controles attendus:

```sql
SELECT COUNT(*) FROM fact_metre;
SELECT COUNT(DISTINCT lot) FROM fact_metre;
```

Attendus historiques:

- lignes: 290
- lots: 7
- Analytics lit le modele historique
- Pipeline, imports et synchronisations continuent d'ecrire dans `fact_metre`

## Mode V5.3

Variable:

```text
SP2I_FACT_SOURCE=vw_fact_metre_current
```

Controles attendus:

```sql
SELECT COUNT(*) FROM vw_fact_metre_current;
SELECT COUNT(DISTINCT article_code) FROM vw_fact_metre_current;
SELECT COUNT(DISTINCT lot_code) FROM vw_fact_metre_current;
SELECT SUM(capex_local), SUM(capex_import), SUM(capex_optimise), SUM(economie)
FROM vw_fact_metre_current;
```

Attendus V5.3:

- lignes: 4734
- articles: 2524
- lots: 18
- CAPEX local > 0
- CAPEX import > 0
- CAPEX optimise > 0
- economie > 0

## Endpoints a tester

- `GET /analytics/dashboard`
- `GET /analytics/drilldown`
- `GET /analytics/heatmap`
- `GET /analytics/risk`
- `GET /analytics/cost-intelligence`
- `GET /analytics/spatial`

Critere GO:

- HTTP 200
- aucune erreur backend
- `nb_lignes` ou equivalent coherent avec la source choisie
- 18 lots visibles en mode V5.3
