# Connexion Power BI - SP2I CAPEX

La source officielle Power BI est PostgreSQL.

Power BI doit visualiser les donnees deja preparees par le backend et la base.
Il ne doit pas recalculer le CAPEX, les economies ou la decision `IMPORT` /
`LOCAL`.

## Connexion PostgreSQL

Dans Power BI Desktop :

1. `Obtenir les donnees`
2. `Base de donnees PostgreSQL`
3. Renseigner :

```text
Serveur : localhost
Base    : sp2i_capex
```

4. Mode conseille pendant le developpement :

```text
DirectQuery
```

5. Identifiants locaux :

```text
Utilisateur : user
Mot de passe : password
```

## Tables a charger

Charger le STAR schema :

```text
fact_metre
dim_projet
dim_lot
dim_niveau
dim_batiment
dim_famille
```

Charger aussi les vues KPI si tu veux des cartes deja agregees :

```text
v_kpi_capex
v_kpi_lot
v_kpi_famille
v_kpi_niveau
v_kpi_batiment
v_kpi_import_local
v_qualite_dqe
v_kpi_scenario
v_compare_scenarios
v_scenario_evolution
```

Pour les simulations historisees, charger aussi :

```text
dim_scenario
simulation_run
fact_simulation
```

Pour l'analytics decisionnel procurement, charger :

```text
dim_supplier
dim_country
dim_risk_level
v_decision_summary
v_decision_risk
v_supplier_performance
v_import_risk_analysis
```

## Relations Power BI

Creer uniquement des relations en sens unique, de la dimension vers la fact.

```text
dim_projet[projet_id]     1 -> * fact_metre[projet_id]
dim_lot[lot_id]           1 -> * fact_metre[lot_id]
dim_niveau[niveau_id]     1 -> * fact_metre[niveau_id]
dim_batiment[batiment_id] 1 -> * fact_metre[batiment_id]
dim_famille[famille_id]   1 -> * fact_metre[famille_id]
```

Pour les scenarios historises :

```text
dim_scenario[scenario_id]   1 -> * fact_simulation[scenario_id]
dim_supplier[supplier_id]   1 -> * fact_simulation[supplier_id]
dim_country[country_id]     1 -> * fact_simulation[country_id]
dim_lot[lot_id]             1 -> * fact_simulation[lot_id]
dim_famille[famille_id]     1 -> * fact_simulation[famille_id]
```

Ne pas creer de relation sur les colonnes texte comme `lot`, `famille`,
`niveau` ou `batiment`. Elles restent utiles pour l'affichage, mais les
relations doivent utiliser les colonnes `_id`.

## Champs a utiliser

Dans `fact_metre`, utiliser les mesures deja calculees :

```text
capex_local
capex_import
capex_optimise
economie
taux_economie
decision_import
quantite
pu_local
pu_import
date_import
```

Dans les dimensions, utiliser les libelles pour les slicers :

```text
dim_projet[projet_nom]
dim_lot[lot]
dim_niveau[niveau]
dim_batiment[batiment]
dim_famille[famille]
dim_famille[categorie]
dim_famille[importable]
```

## Champs a masquer

Pour rendre le modele plus propre dans Power BI, masquer :

```text
fact_metre[lot]
fact_metre[famille]
fact_metre[niveau]
fact_metre[batiment]
fact_metre[prix_total_ht]
fact_metre[economie_nette]
fact_metre[created_at]
fact_metre[updated_at]
```

Les anciennes colonnes restent en base pour compatibilite backend, mais les
rapports doivent utiliser les nouvelles colonnes analytiques.

## Mesures DAX minimales

Les calculs sont deja prepares en base. Les mesures DAX doivent donc rester des
sommes simples.

Ne jamais utiliser :

```DAX
AVERAGE(fact_metre[taux_economie])
```

Cette formule fait une moyenne de ratios ligne par ligne. Elle peut afficher un
taux faux, par exemple `61,80%`, alors que le ratio financier global reel est
autour de `14,63%`.

```DAX
CAPEX Local = SUM(fact_metre[capex_local])
```

```DAX
CAPEX Import = SUM(fact_metre[capex_import])
```

```DAX
CAPEX Optimise = SUM(fact_metre[capex_optimise])
```

```DAX
Economie = SUM(fact_metre[economie])
```

```DAX
Taux Economie = DIVIDE([Economie], [CAPEX Local], 0)
```

Cette mesure DAX retourne une fraction (`0,1463`). Si tu la formates en
pourcentage dans Power BI, elle s'affichera correctement comme `14,63%`.

Pour une carte KPI sans logique DAX, tu peux aussi utiliser directement :

```text
v_kpi_capex[taux_economie_global]
```

Cette colonne PostgreSQL contient deja une valeur en points de pourcentage
(`14,63`). Dans Power BI, l'afficher comme nombre decimal avec un suffixe `%`,
ou diviser par 100 si tu veux utiliser le format natif `Pourcentage`.

## Decision Engine

Les champs decisionnels sont calcules avant Power BI et historises dans
`fact_simulation` :

```text
decision_score
risk_score
lead_time_score
criticality_score
decision_reason
decision_type
decision_confidence
supplier_id
country_id
```

Power BI doit les afficher, filtrer et agreger, mais ne doit pas recalculer le
score decisionnel. Les vues `v_decision_*` sont les sources conseillees pour
les pages de synthese risque, fournisseur et arbitrage import/local.

## Vues KPI

Les vues `v_kpi_*` sont utiles pour :

- verifier les totaux ;
- construire rapidement des cartes KPI ;
- alimenter des pages de synthese ;
- comparer Power BI avec PostgreSQL.

Exemple :

```sql
SELECT * FROM v_kpi_capex;
```

Valeur attendue apres correction :

```text
capex_local_total     : 1 132 312 145,00
economie_totale       : 165 636 236,65
taux_economie_global  : 14,63
```

## Verification rapide

Depuis PowerShell :

```powershell
$env:PGPASSWORD="password"
psql -h localhost -U user -d sp2i_capex -c "SELECT COUNT(*) FROM fact_metre;"
psql -h localhost -U user -d sp2i_capex -c "SELECT * FROM v_kpi_capex;"
```

Valeurs observees apres creation du STAR schema :

```text
fact_metre  : 441 lignes
dim_projet  : 1 ligne
dim_lot     : 14 lignes
dim_niveau  : 4 lignes
dim_batiment: 2 lignes
dim_famille : 7 lignes
```
