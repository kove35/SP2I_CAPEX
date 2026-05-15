# Flux persistence

## Sans persistence

```text
POST /simulation/simulate
persist=false
```

Le moteur :

1. nettoie les lignes ;
2. calcule les CAPEX ;
3. retourne JSON ;
4. ne sauvegarde rien.

## Avec persistence

```text
POST /simulation/simulate
persist=true
```

Le moteur :

1. nettoie les lignes ;
2. calcule les CAPEX ;
3. cree ou met a jour `dim_scenario` ;
4. cree `simulation_run` ;
5. insere les lignes dans `fact_simulation` ;
6. complete le run avec warnings, erreurs et duree ;
7. retourne le JSON API.

## Transaction

Si une erreur arrive pendant la persistence, la transaction PostgreSQL est
annulee avec `rollback`.

Cela evite les scenarios incomplets.

## API de lecture

```text
GET /simulation/scenarios
GET /simulation/scenario/{scenario_id}
GET /simulation/compare?scenario_a=...&scenario_b=...
```

Ces endpoints lisent PostgreSQL et servent React ou des outils de controle.
