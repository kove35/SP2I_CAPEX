# Architecture scenarios SP2I CAPEX

La phase 2 ajoute l'historisation sans remplacer le moteur existant.

## Objectif

Transformer SP2I CAPEX :

```text
moteur de calcul temps reel
```

en :

```text
plateforme analytique CAPEX historisee
```

## Nouveau flux

```text
POST /simulation/simulate?persist=true
    -> ServiceSimulation
    -> CalculateurCAPEX
    -> RepositoryScenario
    -> RepositoryRun
    -> RepositorySimulation
    -> PostgreSQL
    -> Power BI
```

## Tables

### dim_scenario

Stocke les hypotheses :

- nom du scenario ;
- type de scenario ;
- description ;
- parametres JSON ;
- baseline ou non ;
- auteur ;
- dates.

### simulation_run

Trace chaque execution :

- nombre de lignes en entree ;
- nombre de lignes calculees ;
- warnings ;
- erreurs ;
- duree ;
- statut.

### fact_simulation

Historise chaque ligne simulee :

- CAPEX local ;
- CAPEX import ;
- CAPEX optimise ;
- economie ;
- decision import/local ;
- score de confiance ;
- cles dimensions.

## Compatibilite

Si `persist=false`, le moteur se comporte comme avant.

Si `persist=true`, le meme calcul est execute, puis sauvegarde dans PostgreSQL.

Les endpoints existants restent disponibles.
