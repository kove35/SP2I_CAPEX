# Architecture simulation CAPEX

Le moteur de simulation SP2I CAPEX est organise pour rester simple aujourd'hui
et evoluer vers une plateforme SaaS demain.

## Flux principal

```text
Excel / DQE
    -> FastAPI
    -> ServiceSimulation
    -> DataCleaner
    -> CalculateurCAPEX
    -> PostgreSQL
    -> Power BI
```

## Role des classes

### ServiceSimulation

`ServiceSimulation` est la facade applicative. C'est le point d'entree du moteur
pour FastAPI.

Il fait :

- recevoir une demande Pydantic ;
- choisir le mode `strict` ou `tolerant` ;
- lancer le nettoyage ;
- lancer le calcul CAPEX ;
- retourner KPI, lignes, warnings, erreurs et metadata.

Il ne doit pas contenir les formules financieres.

### DataCleaner

`DataCleaner` transforme une ligne brute en ligne metier stable.

Il fait :

- conversion des nombres ;
- normalisation des lots ;
- normalisation des familles ;
- normalisation des niveaux ;
- detection des anomalies.

En mode `strict`, il bloque les donnees invalides.

En mode `tolerant`, il conserve les donnees et ajoute des warnings.

### CalculateurCAPEX

`CalculateurCAPEX` est le moteur pur de calcul.

Il fait :

- estimation FOB ;
- calcul du landed cost ;
- calcul CAPEX import ;
- calcul CAPEX local ;
- calcul CAPEX optimise ;
- calcul economie ;
- decision `IMPORT` ou `LOCAL`.

Il ne depend pas de FastAPI, SQLAlchemy ou pandas.

## Parametres globaux

Les constantes metier sont centralisees ici :

```text
07_API_BACKEND/app/core/global_parameters.py
```

Objectif :

- eviter les magic numbers ;
- documenter les hypotheses ;
- preparer un futur ecran d'administration.

## Erreurs metier

Les erreurs structurees sont ici :

```text
07_API_BACKEND/app/core/errors.py
```

Elles permettent de distinguer :

- erreur simulation ;
- erreur qualite data ;
- scenario invalide ;
- erreur decision import.

## Logs

Les logs sont ecrits dans :

```text
logs/simulation.log
logs/pipeline.log
logs/errors.log
```

Ils tracent :

- temps de calcul ;
- nombre de lignes ;
- economies globales ;
- erreurs metier ;
- warnings data quality.
