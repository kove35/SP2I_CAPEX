# Integration Power BI Service

## Role de Power BI

Power BI reste la couche analytique strategique de SP2I.

Il doit afficher :

- KPI CAPEX.
- arbitrages import/local.
- qualite DQE.
- lots, familles, niveaux, batiments.
- scenarios.
- analyses procurement et chantier.

Il ne doit pas recalculer :

- CAPEX local.
- CAPEX importe.
- economie.
- decision import/local.
- taux economie global.

## Source recommandee

Power BI doit se connecter a PostgreSQL Render.

Tables et vues a charger :

- `fact_metre`
- `dim_famille`
- `dim_lot`
- `dim_niveau`
- `dim_batiment`
- `dim_projet`
- `v_kpi_capex`
- `v_kpi_lot`
- `v_kpi_famille`
- `v_kpi_niveau`
- `v_kpi_batiment`

## Integration Streamlit

Streamlit integre les rapports Power BI via iframe.

Variables :

```text
POWERBI_DIRECTION_URL
POWERBI_FINANCE_URL
POWERBI_IMPORT_URL
POWERBI_CHANTIER_URL
POWERBI_DQE_URL
```

Ces URLs doivent etre configurees dans les secrets Streamlit.

## Strategie dashboard

### Direction

- CAPEX total.
- economie totale.
- taux economie global.
- risques majeurs.

### Finance

- CAPEX local vs optimise.
- economies par lot.
- scenarios.

### Import

- decisions import/local.
- procurement.
- risques pays/fournisseurs.

### Chantier

- lots critiques.
- livraisons.
- risques planning.

### DQE intelligent

- qualite donnees.
- lots detectes.
- anomalies.
- mapping IA.

## Bonne pratique ratio

Un taux global financier doit etre calcule ainsi :

```sql
SUM(economie) / SUM(capex_local)
```

Ne pas utiliser :

```text
AVERAGE(taux_economie)
```

La moyenne des ratios ligne par ligne donne souvent un KPI faux.
