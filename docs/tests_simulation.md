# Tests simulation

## Tests unitaires

Les tests principaux sont :

```text
tests/test_calculateur_capex.py
tests/test_data_cleaner.py
tests/test_service_simulation.py
```

Commande :

```powershell
python -m unittest tests.test_calculateur_capex tests.test_data_cleaner tests.test_service_simulation
```

## Ce qui est controle

### CalculateurCAPEX

- PU import ;
- CAPEX import ;
- CAPEX local ;
- economie ;
- decision import/local ;
- seuil decision ;
- FOB fourni ;
- KPI ratio des totaux ;
- valeurs invalides tolerantes.

### DataCleaner

- conversion numerique ;
- normalisation lot ;
- normalisation famille ;
- normalisation niveau ;
- mode strict ;
- mode tolerant ;
- preservation du contexte lot.

### ServiceSimulation

- metadata ;
- IDs techniques ;
- mode strict ;
- mode tolerant ;
- warnings ;
- erreurs structurees ;
- option `summary_only`.

## Benchmarks performance

Le benchmark est ici :

```text
tests/performance/test_simulation_performance.py
```

Commande :

```powershell
python -m unittest tests.performance.test_simulation_performance
```

Par defaut :

- 100 lignes ;
- 1 000 lignes ;
- 10 000 lignes.

Le benchmark 100 000 lignes est volontairement desactive par defaut.

Pour l'activer :

```powershell
$env:SP2I_RUN_100K_BENCH="1"
python -m unittest tests.performance.test_simulation_performance
```

## Tests projet complets

La suite existante reste :

```powershell
python run_tests.py
```

Elle verifie PostgreSQL, les tables, les KPI et la coherence API/SQL.
