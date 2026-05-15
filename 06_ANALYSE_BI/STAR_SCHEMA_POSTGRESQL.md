# STAR SCHEMA PostgreSQL - SP2I CAPEX

Ce document explique le modele analytique PostgreSQL cree pour Power BI.

L'objectif est simple : Power BI affiche, filtre et explore. PostgreSQL et le
backend calculent.

## Audit du modele avant evolution

Le modele initial contenait :

- `fact_metre` : table principale avec les lignes DQE calculees ;
- `dim_famille` : dimension famille simple, encore reliee par texte ;
- `v_kpi_*` : vues KPI existantes, mais basees sur les colonnes texte ;
- `monitoring_logs` : table technique.

Problemes identifies :

- les relations Power BI utilisaient `famille`, `lot`, `niveau`, `batiment` en
  texte ;
- seules les familles etaient dimensionnees ;
- pas de dimension projet, lot, niveau ou batiment ;
- pas de cles techniques pour un modele scalable ;
- les vues KPI etaient utiles mais pas encore alignees sur un vrai STAR schema.

## Evolution appliquee

Le script SQL idempotent est ici :

```text
09_INFRA/sql/001_powerbi_star_schema.sql
```

Il ajoute progressivement :

- `dim_projet`
- `dim_lot`
- `dim_niveau`
- `dim_batiment`
- `famille_id` dans `dim_famille`
- les colonnes `_id` dans `fact_metre`
- les colonnes analytiques `capex_local`, `capex_import`, `economie`,
  `taux_economie`, `pu_local`, `pu_import`
- des indexes pour Power BI
- des foreign keys `DIM -> FACT`
- un trigger de compatibilite pour les futures insertions backend
- des vues KPI recalculables dans PostgreSQL

## Pourquoi garder les anciennes colonnes texte ?

Les colonnes `lot`, `famille`, `niveau`, `batiment` restent dans `fact_metre`
pour compatibilite avec :

- les routes FastAPI existantes ;
- les tests actuels ;
- les exports historiques ;
- les scripts de pipeline deja presents.

Mais Power BI ne doit pas les utiliser comme relations. Les relations doivent
passer par les colonnes `_id`.

## Relations attendues dans Power BI

```text
dim_projet[projet_id]     1 -> * fact_metre[projet_id]
dim_lot[lot_id]           1 -> * fact_metre[lot_id]
dim_niveau[niveau_id]     1 -> * fact_metre[niveau_id]
dim_batiment[batiment_id] 1 -> * fact_metre[batiment_id]
dim_famille[famille_id]   1 -> * fact_metre[famille_id]
```

Configuration :

- cardinalite : `1 vers plusieurs`
- sens de filtrage : `simple`
- direction : dimension vers fact

## Vues KPI disponibles

```text
v_kpi_capex
v_kpi_lot
v_kpi_famille
v_kpi_niveau
v_kpi_batiment
v_kpi_import_local
v_qualite_dqe
```

Ces vues servent a controler les totaux et a creer rapidement des pages de
synthese. Elles ne remplacent pas le STAR schema, elles le completent.

## Regle KPI : Ratio des totaux

Pour les indicateurs financiers globaux, SP2I utilise toujours un ratio des
totaux :

```text
Taux economie = SUM(economie) / SUM(capex_local) * 100
```

Il ne faut jamais utiliser une moyenne de ratios ligne par ligne :

```text
AVG(taux_economie)
```

Pourquoi ? Une petite ligne avec 90% d'economie et une grosse ligne avec 5%
d'economie n'ont pas le meme poids financier. La moyenne simple donne la meme
importance aux deux lignes, alors que le ratio des totaux respecte les montants.

Les vues corrigees sont creees par :

```text
09_INFRA/sql/003_correct_kpi_ratios.sql
```

Resultat controle :

```text
CAPEX local total : 1 132 312 145,00
Economie totale   :   165 636 236,65
Taux economie     : 14,63%
```

## Resultat observe

Apres application du script et synchronisation du fichier Excel complet :

```text
fact_metre  : 441 lignes
dim_projet  : 1 ligne
dim_lot     : 14 lignes
dim_niveau  : 4 lignes
dim_batiment: 2 lignes
dim_famille : 7 lignes
```

Aucune ligne de `fact_metre` n'a un ID dimensionnel nul.

## Diagnostics apres import

Les requetes de controle sont ici :

```text
09_INFRA/sql/002_diagnostics_pipeline_powerbi.sql
```

Elles verifient :

- le nombre de lignes par lot ;
- les lignes sans lot ;
- les lignes sans ID dimensionnel ;
- les dimensions orphelines ;
- les KPI pre-calcules ;
- la repartition `IMPORT` / `LOCAL`.

## Bonne pratique Power BI

Charger les dimensions et la table de faits.

Utiliser les dimensions pour les slicers :

- projet ;
- lot ;
- niveau ;
- batiment ;
- famille ;
- categorie ;
- importable.

Utiliser `fact_metre` pour les montants :

- `capex_local`
- `capex_import`
- `capex_optimise`
- `economie`
- `taux_economie`
- `decision_import`

Garder les mesures DAX simples : `SUM`, `COUNT`, `DIVIDE`.

Ne pas recreer les formules CAPEX dans Power BI.
