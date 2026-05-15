# Historisation simulation

## Pourquoi historiser ?

Sans historisation, une simulation existe seulement pendant l'appel API.

Avec historisation, on peut :

- comparer plusieurs strategies CAPEX ;
- conserver les hypotheses ;
- auditer les resultats ;
- alimenter Power BI ;
- preparer les futures analyses IA.

## Exemple

```json
{
  "persist": true,
  "scenario_name": "IMPORT_AGRESSIF_2026",
  "scenario_type": "IMPORT_AGRESSIF",
  "parameters": {
    "taux_landed_cost": {
      "transport_maritime": 0.12,
      "droits_douane": 0.15
    },
    "seuil_decision_import": 0.97
  }
}
```

## Identifiants

Chaque simulation retourne :

- `simulation_id` : identifiant du lot de lignes simulees ;
- `scenario_id` : identifiant du scenario ;
- `run_id` : identifiant de l'execution.

Ces IDs permettent de relier API, PostgreSQL, logs et Power BI.

## Repositories

```text
RepositoryScenario   -> dim_scenario
RepositoryRun        -> simulation_run
RepositorySimulation -> fact_simulation
```

Le SQL ne vit pas dans `ServiceSimulation`. Le service orchestre, les
repositories persistent.
