# Architecture backend SP2I CAPEX

Ce document explique l'architecture cible du backend SP2I CAPEX et la premiere
refactorisation mise en place. Il est volontairement pedagogique : un nouveau
developpeur doit pouvoir comprendre ou placer son code sans connaitre tout le
projet.

## Objectif du backend

Le backend est la source de verite metier. Il doit centraliser :

- le nettoyage des donnees DQE ;
- le mapping des familles travaux ;
- le calcul du prix import ;
- l'arbitrage `IMPORT` vs `LOCAL` ;
- les KPI CAPEX ;
- les datasets analytiques consommes par React et Power BI.

Power BI doit rester une couche de visualisation. Il peut filtrer, afficher et
mettre en forme, mais il ne doit pas porter les formules critiques.

## Audit de l'existant

### 1. Logique metier trop proche des fichiers

Avant refactorisation, l'API appelait des scripts dans `04_TRAITEMENT` via des
manipulations de `sys.path`. Cela fonctionnait pour un prototype, mais c'etait
fragile pour un SaaS : un endpoint API dependait directement de chemins locaux
et de scripts batch.

Correction progressive : le backend possede maintenant `app/core`, qui contient
les classes pures `DataCleaner`, `CalculateurCAPEX` et `MapperFamilles`.

### 2. Routes FastAPI trop responsables

Certaines routes instanciaient directement les services, validaient des fichiers
et portaient des decisions techniques. Une route SaaS doit rester fine :

1. recevoir la requete ;
2. laisser Pydantic valider ;
3. appeler un service ;
4. retourner une reponse.

Correction progressive : `routes/simulation.py` utilise des schemas Pydantic et
une dependance FastAPI `get_service_simulation`.

### 3. Pas de vraie couche schemas

Les schemas etaient regroupes dans un fichier plat. Cela limite la lisibilite de
Swagger quand l'API grandit.

Correction progressive : les schemas de simulation vivent dans
`app/schemas/simulation.py`, avec export depuis `app/schemas/__init__.py` pour
garder les imports simples.

### 4. Acces donnees melange aux services

`ServiceDB` contenait les requetes SQL et le cas d'usage applicatif. Pour faire
evoluer le stockage vers PostgreSQL, parquet ou MongoDB, il faut une couche
dediee.

Correction progressive : `app/repositories/repository_simulation.py` porte les
requetes SQL. `ServiceDB` reste une facade de compatibilite.

### 5. Pandas non necessaire pour l'API temps reel

Les KPI simples ne doivent pas imposer pandas. Les sommes, compteurs et taux de
l'API temps reel sont maintenant calcules en Python natif dans
`CalculateurCAPEX.calculer_kpi`.

## Architecture cible

Flux de responsabilites :

```text
routes FastAPI
    -> schemas Pydantic
    -> services applicatifs
    -> core metier pur
    -> repositories
    -> datasources fichiers / PostgreSQL / futur stockage
```

## Role des dossiers

### `app/routes`

Expose les endpoints HTTP. Les routes ne doivent pas contenir de formule CAPEX.
Exemples :

- `routes/simulation.py` : simulation temps reel et scenarios ;
- `routes/import.py` : endpoint historique `/import/optimize`, conserve pour
  compatibilite ;
- `routes/dqe.py` : upload DQE et synchronisation.

### `app/schemas`

Contient les contrats API Pydantic :

- `SimulationItem` : une ligne DQE envoyee par React ;
- `SimulationParameters` : hypotheses modifiables ;
- `SimulationRequest` : requete complete ;
- `SimulationResponse` : reponse stable pour React ;
- `ScenarioRequest` : analyse de sensibilite.

Ces schemas ameliorent Swagger, le typage et la securite API.

### `app/services`

Orchestre les cas d'usage. Un service peut appeler plusieurs repositories et le
core metier, mais il ne doit pas contenir les formules de calcul.

- `ServiceSimulation` : simulation CAPEX, batch courant, scenarios ;
- `ServicePipeline` : upload DQE, generation CSV/BI, synchronisation SQL ;
- `ServiceDB` : facade de compatibilite vers le repository SQL.

### `app/core`

Contient la logique metier pure :

- `cleaner.py` : normalisation DQE et conversion numerique defensive ;
- `calculator.py` : calcul import/local, CAPEX, economie, KPI, sensibilite ;
- `mapper.py` : mapping familles et categories achat.

Regle importante : `core` ne doit pas importer FastAPI, SQLAlchemy, pandas ou
des chemins de fichiers projet.

### `app/repositories`

Isole l'acces aux donnees :

- `RepositoryBPU` : lecture/ecriture des fichiers DQE et optimisation actuels ;
- `RepositoryMapping` : parametres et referentiels ;
- `RepositorySimulation` : tables PostgreSQL analytiques.

Demain, cette couche permettra de brancher parquet, MongoDB ou stockage objet
sans changer les routes ni les formules.

### `app/dependencies.py`

Centralise l'injection FastAPI. On evite les singletons globaux dangereux :
chaque requete recoit un service construit proprement avec ses repositories.

## Endpoints principaux

### `POST /api/upload/excel`

Endpoint progressif pour le futur drag & drop React.

Il analyse un fichier Excel sans modifier les donnees courantes :

- detection des feuilles ;
- detection de la ligne d'en-tete ;
- proposition de mapping vers le standard SP2I ;
- score de confiance ;
- preview de lignes normalisees ;
- simulation CAPEX de preview sur les lignes exploitables.

Exemple teste avec `03_DONNEES_ENTREE/Fichier_Source_Complet.xlsx` :

- feuille recommandee : `METRE` ;
- ligne d'en-tete : `4` ;
- score DQE : `1.0` ;
- lignes detectees : `446`.

Ce endpoint ne synchronise pas encore PostgreSQL. C'est volontaire : la phase IA
commence par analyser et proposer, puis le pipeline de validation viendra dans
une etape suivante.

### `POST /api/upload/excel/sync`

Endpoint d'import complet Excel vers PostgreSQL.

Il remplace le DQE analytique courant, regenere les JSON/CSV, synchronise
PostgreSQL et retourne le `lineage` du pipeline. Il est separe de la preview
pour eviter qu'un simple test React modifie les donnees Power BI.

### `POST /simulation/simulate`

Endpoint moderne pour React. Il accepte des lignes DQE et des parametres, puis
retourne :

- KPI ;
- lignes detaillees ;
- decision import/local ;
- score de confiance ;
- analyse de sensibilite optionnelle.

### `POST /simulation/scenarios`

Endpoint dedie aux hypotheses. Il calcule plusieurs variations du landed cost
pour comparer les decisions CAPEX.

### `POST /import/optimize`

Endpoint historique conserve. Il lit le DQE normalise courant, lance le nouveau
moteur `ServiceSimulation`, puis regenere le CSV attendu.

### `POST /dqe/upload`

Upload un DQE JSON, normalise les donnees, calcule les arbitrages, genere les
datasets Power BI et synchronise PostgreSQL si une session DB est disponible.

## Flux React

React appellera d'abord `/api/upload/excel` pour analyser un fichier depose par
l'utilisateur :

1. l'utilisateur depose un Excel ;
2. le backend detecte la feuille DQE/BPU la plus probable ;
3. React affiche le mapping propose et les scores de confiance ;
4. l'utilisateur valide ou corrige le mapping.

React doit ensuite appeler `/simulation/simulate` pour une simulation
interactive :

1. l'utilisateur modifie les parametres ;
2. React envoie `items` et `parameters` ;
3. l'API renvoie KPI et lignes detaillees ;
4. React affiche tableaux, decisions et scenarios.

Les noms de champs sont stables pour eviter de casser le frontend :

- `capex_local` ;
- `capex_import` ;
- `capex_optimise` ;
- `economie_nette` ;
- `decision_import` ;
- `score_confiance`.

## Flux Power BI

Power BI doit consommer les exports deja calcules :

- `06_ANALYSE_BI/dataset/FACT_METRE.csv` ;
- `06_ANALYSE_BI/dataset/DIM_FAMILLE.csv` ;
- ou les tables PostgreSQL synchronisees.

Les colonnes critiques sont preparees cote backend :

- `PU_IMPORT_HT` ;
- `CAPEX_IMPORT` ;
- `CAPEX_LOCAL` ;
- `ECONOMIE_NETTE` ;
- `DECISION_IMPORT`.

Power BI ne doit donc pas recalculer l'arbitrage.

## Flux IA Excel

La couche IA est ajoutee sans remplacer les calculs metier :

```text
Upload Excel
    -> ServiceAIMapping
    -> RepositoryExcel
    -> mapping standard SP2I
    -> preview normalisee
    -> ServiceSimulation pour preview CAPEX
```

Responsabilites autorisees pour l'IA :

- reconnaitre les feuilles ;
- detecter les colonnes ;
- proposer un mapping ;
- scorer la confiance ;
- signaler les anomalies.

Responsabilites interdites pour l'IA :

- calculer le CAPEX final ;
- arbitrer `IMPORT` vs `LOCAL` ;
- modifier les formules financieres ;
- remplacer `ServiceSimulation`.

Aujourd'hui, `ServiceAIMapping` utilise des regles heuristiques explicables.
Demain, un LLM ou des embeddings pourront enrichir ces propositions, mais ils
devront rester encapsules dans ce service.

## Data lineage

Le pipeline trace maintenant les volumes a chaque etape :

- lignes source ;
- lignes apres nettoyage ;
- lignes apres mapping ;
- lignes apres simulation ;
- lots distincts ;
- lignes sans lot ;
- pertes expliquees.

L'utilitaire transverse est :

```text
app/utils/data_lineage.py
```

Exemple de resultat apres import de `Fichier_Source_Complet.xlsx` :

```text
source          : 441 lignes, 14 lots
nettoyage       : 441 lignes, 0 perte
mapping         : 441 lignes, 0 perte
simulation      : 441 lignes, 0 perte
PostgreSQL      : 441 lignes FACT_METRE
```

## Regles pour les prochains developpements

- Ajouter une formule CAPEX dans `app/core`, jamais dans une route.
- Ajouter un nouvel endpoint dans `app/routes`, avec un schema Pydantic.
- Ajouter une lecture/ecriture de donnees dans `app/repositories`.
- Ajouter une analyse IA dans `app/services/service_ai_mapping.py` ou `app/ai`.
- Garder les anciens endpoints tant que le frontend ou Power BI les utilise.
- Ajouter des adaptateurs de compatibilite plutot que renommer brutalement.
- Utiliser pandas uniquement pour ETL lourd ou preparation BI volumineuse.

## Limites restantes

Cette refactorisation est progressive. Les scripts historiques de
`04_TRAITEMENT` existent encore pour compatibilite batch. Ils pourront etre
transformes plus tard en wrappers CLI autour de `app/core`, lorsque tous les
usages seront confirmes.
