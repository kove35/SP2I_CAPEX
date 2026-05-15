# Power BI scenarios

Power BI peut maintenant consommer les tables historisees.

## Tables a charger

```text
dim_scenario
simulation_run
fact_simulation
```

Avec les dimensions existantes :

```text
dim_projet
dim_lot
dim_famille
dim_niveau
dim_batiment
```

## Vues a charger

```text
v_kpi_scenario
v_compare_scenarios
v_scenario_evolution
```

## Relations

```text
dim_scenario[scenario_id] 1 -> * fact_simulation[scenario_id]
dim_scenario[scenario_id] 1 -> * simulation_run[scenario_id]
dim_lot[lot_id]           1 -> * fact_simulation[lot_id]
dim_famille[famille_id]   1 -> * fact_simulation[famille_id]
dim_niveau[niveau_id]     1 -> * fact_simulation[niveau_id]
dim_batiment[batiment_id] 1 -> * fact_simulation[batiment_id]
```

Sens de filtre conseille :

```text
Dimension -> Fact
```

## Regle KPI

Les taux financiers doivent venir des vues PostgreSQL ou de mesures DAX basees
sur le ratio des totaux.

Ne pas utiliser :

```DAX
AVERAGE(fact_simulation[taux_economie])
```

Utiliser :

```DAX
Taux Economie = DIVIDE(SUM(fact_simulation[economie]), SUM(fact_simulation[capex_local]), 0)
```

Ou directement :

```text
v_kpi_scenario[taux_economie_global]
```
