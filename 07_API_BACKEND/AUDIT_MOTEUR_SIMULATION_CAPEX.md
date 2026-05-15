# Audit moteur de simulation CAPEX - SP2I CAPEX

Date : 2026-05-15

Ce document audite le moteur de simulation CAPEX actuel sans proposer de
refactor brutal. L'objectif est de consolider progressivement l'architecture
existante :

```text
Excel / DQE / Metre
    -> FastAPI
    -> ServiceSimulation
    -> PostgreSQL
    -> Power BI
```

## Synthese executive

Le moteur actuel est fonctionnel et deja correctement oriente :

- la logique CAPEX principale est sortie des routes ;
- `ServiceSimulation` orchestre le cas d'usage ;
- `CalculateurCAPEX` contient les formules metier pures ;
- `DataCleaner` prepare les lignes DQE ;
- les KPI globaux Power BI sont maintenant calcules cote PostgreSQL.

Mais le moteur reste encore un moteur V1 :

- stateless ;
- mono-scenario par appel ;
- sans historisation ;
- sans table `dim_scenario` ou `fact_simulation` ;
- avec des parametres metier encore trop implicites ;
- avec un score de confiance simple ;
- avec une auditabilite encore limitee au pipeline, pas aux simulations.

Conclusion : le socle est bon pour une evolution progressive. Il ne faut pas le
reecrire. Il faut ajouter des couches specialisees autour du moteur existant.

## Architecture actuelle

```text
routes/simulation.py
    -> schemas/simulation.py
    -> services/service_simulation.py
    -> core/cleaner.py
    -> core/calculator.py
```

### Roles actuels

`routes/simulation.py`

- expose `/simulation/simulate` ;
- expose `/simulation/scenarios` ;
- valide via Pydantic ;
- appelle `ServiceSimulation`.

`schemas/simulation.py`

- definit `SimulationItem` ;
- definit `SimulationParameters` ;
- definit `SimulationRequest` ;
- definit `SimulationResponse` ;
- definit `ScenarioRequest`.

`ServiceSimulation`

- transforme les schemas Pydantic en dictionnaires ;
- appelle `DataCleaner` ;
- appelle `CalculateurCAPEX` ;
- formate la reponse API ;
- conserve la compatibilite avec `/import/optimize`.

`DataCleaner`

- nettoie les nombres ;
- normalise lots, familles, niveaux ;
- calcule les statuts qualite ligne ;
- genere une structure DQE stable.

`CalculateurCAPEX`

- estime le FOB si absent ;
- calcule le landed cost ;
- calcule CAPEX local/import/optimise ;
- calcule economie ;
- decide `IMPORT` ou `LOCAL` ;
- calcule quelques KPI de synthese ;
- effectue une analyse de sensibilite simple.

## Points forts

### 1. Bonne separation initiale

Les routes ne portent pas les formules CAPEX. C'est sain pour FastAPI, Swagger
et les tests.

### 2. Core metier pur

`CalculateurCAPEX` ne depend pas de FastAPI, SQLAlchemy, pandas ou PostgreSQL.
Cela facilite les tests unitaires et l'evolution future.

### 3. Python natif pour le temps reel

Les KPI simples utilisent `sum()` et des comprehensions. C'est adapte a des
simulations interactives de quelques centaines ou milliers de lignes.

### 4. Compatibilite preservee

`ServiceImport` et `/import/optimize` continuent a fonctionner. C'est important
pour ne pas casser Power BI, les scripts historiques ou le frontend.

### 5. PostgreSQL devient source analytique

Le STAR schema et les vues KPI corrigent la trajectoire : Power BI visualise,
PostgreSQL agrege.

## Audit architecture

### Observation

`ServiceSimulation` orchestre correctement, mais il commence a concentrer
plusieurs responsabilites :

- simulation temps reel ;
- simulation source courante ;
- scenario/sensibilite ;
- formatage API ;
- export CSV historique.

Ce n'est pas encore critique, mais c'est le prochain point de pression.

### Risque futur

Quand il faudra ajouter multi-projets, utilisateurs, scenarios sauvegardes,
comparaison et audit, `ServiceSimulation` deviendra trop gros si tout est ajoute
dedans.

### Recommandation progressive

Ne pas deplacer brutalement le service. Ajouter plutot des modules autour :

```text
services/service_simulation.py       # facade existante
core/scenario_engine.py              # generation scenarios
core/sensitivity_analysis.py         # variations parametres
core/risk_engine.py                  # score risque / confiance
repositories/repository_simulation_history.py
```

`ServiceSimulation` reste la facade publique, mais delegue progressivement.

## Audit metier

### Calcul PU import

Aujourd'hui :

```text
FOB estime = PU local * ratio famille * coefficient risque
PU import = FOB * (1 + somme taux landed cost)
```

Points positifs :

- logique simple et explicable ;
- ratios par famille ;
- parametres modifiables.

Limites :

- les ratios FOB sont codifies en dur ;
- le coefficient risque `1.1` est fixe ;
- pas de distinction devise / incoterm / fournisseur / pays origine ;
- pas de gestion MOQ, containerisation, delais, stock, change.

Recommandation :

- garder la formule actuelle comme baseline V1 ;
- externaliser progressivement les ratios en PostgreSQL ou JSON parametre ;
- ajouter un champ `source_prix_import` : `fob_fourni`, `estime_famille`,
  `estime_ia`, `catalogue_fournisseur`.

### Calcul CAPEX

La logique actuelle est coherente :

```text
CAPEX_IMPORT = PU_IMPORT * quantite
CAPEX_LOCAL = montant local
CAPEX_OPTIMISE = min selon decision
ECONOMIE = CAPEX_LOCAL - CAPEX_OPTIMISE
```

Point d'attention :

- le moteur accepte `prix_total_ht = 0` dans certains chemins ;
- `quantite` tombe a `1` dans `CalculateurCAPEX` si absente ;
- cela evite les crashs, mais peut masquer une donnee invalide.

Recommandation :

- distinguer mode `strict` et mode `tolerant` ;
- en mode API frontend, refuser les lignes invalides ;
- en mode pipeline Excel, garder les lignes mais taguer `statut_ligne`.

### Decision import/local

Aujourd'hui :

```text
IMPORT si CAPEX_IMPORT < CAPEX_LOCAL * seuil_decision_import
```

Avec seuil par defaut `0.97`, l'import doit etre au moins environ 3% moins cher
que le local.

Points positifs :

- la formule evite de choisir import pour un gain marginal ;
- le seuil est parametable.

Limites :

- le seuil ne depend pas de la famille ;
- pas de penalite delai ;
- pas de penalite risque qualite ;
- pas de contrainte d'importabilite ;
- pas de cout de non-conformite ou SAV.

Recommandation :

Créer plus tard un `DecisionEngine` :

```text
decision = economie_financiere
         - cout_risque
         - cout_delai
         - cout_complexite
```

Mais conserver la decision actuelle comme baseline.

### Score confiance

Aujourd'hui :

```text
base 0.75
+ prix FOB fourni
+ famille connue
+ taux import plausible
```

C'est utile pour une V1, mais insuffisant pour procurement analytics.

Recommandation :

Ajouter `risk_engine.py` avec des composantes explicites :

- confiance prix ;
- confiance mapping famille ;
- confiance fournisseur ;
- confiance delai ;
- confiance quantite ;
- maturite devis.

## Audit scenarios

### Etat actuel

Le moteur sait faire une sensibilite simple :

```text
variations landed cost : -10%, 0%, +10%
```

Mais il ne gere pas encore de vrais scenarios metier persistants.

Limites :

- pas de `scenario_id` applicatif cree par l'API ;
- pas de nom de scenario ;
- pas de version ;
- pas de comparaison persistante ;
- pas d'historique des parametres ;
- pas de lien utilisateur/projet.

### Architecture cible progressive

```text
ScenarioRequest
    -> ScenarioEngine
    -> CalculateurCAPEX
    -> SimulationHistoryRepository
    -> PostgreSQL
```

Nouveaux modules proposes :

- `core/scenario_engine.py`
- `core/sensitivity_analysis.py`
- `repositories/repository_simulation_history.py`
- `services/service_scenario.py` seulement quand le besoin grossit.

## Audit performance

### Etat actuel

Pour 441 lignes, les boucles Python sont parfaitement suffisantes.

Complexite :

```text
normalisation : O(n)
calcul CAPEX  : O(n)
sensibilite   : O(n * nombre_scenarios)
```

### Risques futurs

Pour 100 000 lignes et 50 scenarios, Python pur pourrait devenir lent :

```text
100 000 * 50 = 5 000 000 calculs ligne
```

Ce n'est pas dramatique pour du batch, mais trop lourd pour du temps reel si
l'API doit repondre vite.

### Recommandations

Court terme :

- conserver Python natif ;
- ajouter tests de performance sur 1k, 10k, 100k lignes ;
- limiter le nombre de scenarios temps reel.

Moyen terme :

- utiliser pandas pour batch massif uniquement ;
- conserver Python pur pour simulation interactive ;
- deplacer les agregations globales dans PostgreSQL.

Long terme :

- jobs asynchrones ;
- table `simulation_job` ;
- cache de resultats scenario ;
- queue de traitement.

## Audit data quality

### Points forts

`DataCleaner` gere :

- nombres heterogenes ;
- lots normalises ;
- familles ;
- niveaux ;
- statut qualite ligne.

Le parsing Excel recent ajoute :

- preservation du contexte lot ;
- data lineage ;
- detection des lignes rejetees.

### Points faibles

- `clean_lot` conserve parfois le libelle et parfois seulement le numero selon
  la source ;
- `famille = default` reste encore trop frequent ;
- les regles familles sont simples ;
- les unites contiennent encore des caracteres encodes historiques ;
- la notion de ligne structurelle est geree surtout cote Excel.

### Recommandations

- separer `lot_code = LOT 1` et `lot_libelle = Gros oeuvre` ;
- ajouter `famille_source` et `famille_confiance` ;
- enrichir le mapping via `mapping_familles.xlsx` ;
- creer un audit `v_qualite_mapping_famille`.

## Audit API

### Points forts

- schemas Pydantic clairs ;
- route `/simulation/simulate` simple ;
- route `/simulation/scenarios` dediee ;
- compatibilite des anciens endpoints.

### Points faibles

- `/simulation/scenarios` ne declare pas encore de `response_model` ;
- les erreurs metier ne sont pas structurees ;
- pas de `simulation_id` retourne ;
- pas de pagination pour de tres grosses reponses ;
- pas de mode `summary_only`.

### Recommandations

Ajouter progressivement :

```text
SimulationError
SimulationWarning
SimulationMetadata
SimulationScenarioResponse
```

Et des options :

```text
return_lines: true/false
summary_only: true/false
persist: true/false
```

## Audit PostgreSQL

### Ce qui doit rester dans Python

- nettoyage Excel/DQE ;
- mapping intelligent ;
- simulation ligne par ligne ;
- construction de scenarios ;
- IA future ;
- calculs exploratoires.

### Ce qui doit etre dans PostgreSQL

- historisation ;
- KPI globaux ;
- agregations Power BI ;
- comparaison scenarios sauvegardes ;
- audit de qualite ;
- vues analytiques.

### Tables recommandees

```sql
dim_scenario(
    scenario_id,
    projet_id,
    scenario_nom,
    scenario_type,
    created_by,
    created_at,
    parameters_json,
    is_baseline
)
```

```sql
fact_simulation(
    simulation_id,
    scenario_id,
    id_ligne,
    projet_id,
    lot_id,
    famille_id,
    capex_local,
    capex_import,
    capex_optimise,
    economie,
    taux_economie,
    decision_import,
    score_confiance,
    created_at
)
```

```sql
simulation_run(
    run_id,
    projet_id,
    source_file,
    status,
    rows_in,
    rows_out,
    warnings_json,
    lineage_json,
    started_at,
    ended_at
)
```

## Audit scalabilite SaaS

### Pret aujourd'hui

- architecture compatible extension ;
- services separes ;
- PostgreSQL central ;
- Power BI connecte a un STAR schema.

### Pas encore pret

- multi-utilisateur ;
- isolation par tenant ;
- droits d'acces ;
- projets multiples robustes ;
- historisation scenario ;
- jobs asynchrones ;
- audit complet des simulations.

### Recommandation SaaS

Ajouter d'abord `projet_id` partout dans les flux applicatifs, puis seulement
ensuite `tenant_id` / `user_id`. Ne pas commencer par une architecture multi-
tenant complexe tant que le moteur metier n'est pas stabilise.

## Audit design metier procurement

Le moteur peut devenir un outil procurement analytics, mais il lui manque :

- fournisseurs ;
- pays origine ;
- devise ;
- incoterm ;
- delai ;
- MOQ ;
- colisage/container ;
- fiabilite fournisseur ;
- risque douane ;
- risque planning ;
- score qualite.

Modules futurs proposes :

```text
core/procurement_rules.py
core/risk_engine.py
core/roi_engine.py
core/forecast_engine.py
repositories/repository_supplier.py
```

## Problemes prioritaires

### Critique

1. Pas d'historisation des simulations.
   Impossible de comparer proprement deux simulations dans le temps.

2. Pas de vraie table scenario.
   Les scenarios existent seulement en memoire pendant l'appel API.

3. Parametres metier encore peu audites.
   Les taux et ratios peuvent changer sans trace historique.

### Important

1. Score confiance trop simple.
2. Pas de `response_model` pour `/simulation/scenarios`.
3. Pas de separation explicite entre scenario baseline et scenario alternatif.
4. Trop de `default` dans le mapping famille.
5. Pas de tests unitaires dedies au moteur CAPEX.

### Amelioration

1. Ajouter mode `summary_only`.
2. Ajouter pagination des lignes simulees.
3. Ajouter benchmarks performance.
4. Externaliser ratios FOB et coefficient risque.
5. Ajouter vues PostgreSQL de comparaison scenario.

## Architecture cible progressive

### Aujourd'hui

```text
Route
  -> ServiceSimulation
      -> DataCleaner
      -> CalculateurCAPEX
  -> JSON response
```

### Cible V3

```text
Route
  -> ServiceSimulation
      -> DataCleaner
      -> ScenarioEngine
      -> CalculateurCAPEX
      -> RiskEngine
      -> SimulationHistoryRepository
  -> PostgreSQL
  -> Power BI views
```

`ServiceSimulation` reste la facade. Les nouveaux modules absorbent la
complexite sans casser les endpoints.

## Roadmap progressive

### V1 - Stabilisation moteur

- ajouter tests unitaires `CalculateurCAPEX` ;
- ajouter tests `DataCleaner` ;
- ajouter `response_model` sur `/simulation/scenarios` ;
- documenter les formules ;
- externaliser ratios FOB dans un fichier parametre.

### V2 - Multi-scenarios

- creer `core/scenario_engine.py` ;
- enrichir `ScenarioRequest` avec noms de scenarios ;
- permettre plusieurs jeux de parametres ;
- comparer les KPI scenario A/B dans la reponse API.

### V3 - Historisation

- creer `dim_scenario` ;
- creer `fact_simulation` ;
- creer `simulation_run` ;
- ajouter `persist=true` dans l'API ;
- creer vues `v_kpi_scenario` et `v_compare_scenarios`.

### V4 - IA simulation

- utiliser embeddings pour aider le mapping famille ;
- proposer des ratios FOB selon historique ;
- detecter anomalies de prix ;
- suggerer importabilite.

### V5 - Simulation predictive

- prevision inflation ;
- risque change ;
- delais import ;
- scoring fournisseur ;
- optimisation multi-contrainte cout/delai/risque.

## Recommandations Power BI

Power BI doit charger :

- `fact_metre` pour le baseline courant ;
- futures `fact_simulation` pour scenarios historises ;
- `dim_scenario` pour slicers scenario ;
- vues `v_kpi_*` pour cartes KPI ;
- vues `v_compare_scenarios` pour comparaisons.

Power BI peut faire :

- formatage ;
- slicers ;
- drill-down ;
- `SUM`, `COUNT`, `DIVIDE` simples.

Power BI ne doit pas faire :

- arbitrage import/local ;
- recalcul CAPEX ;
- moyenne de ratios financiers ;
- mapping famille ;
- nettoyage DQE.

## Conclusion

Le moteur SP2I CAPEX est un bon moteur V1. Il est assez simple, lisible et
testable pour continuer. La bonne strategie est de le garder comme noyau et
d'ajouter progressivement :

- scenario engine ;
- history repository ;
- risk engine ;
- tables de simulation ;
- vues analytiques scenario.

La priorite absolue est l'historisation des scenarios, car elle transforme le
moteur d'un calculateur temps reel en plateforme SaaS analytique.
