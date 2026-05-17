# SP2I Analytics Engine V1

## Objectif

SP2I Analytics Engine V1 ajoute une couche BI proprietaire au-dessus de
PostgreSQL, sans casser les endpoints existants.

Il sert a alimenter :

- KPI cards React ;
- ECharts ;
- AG Grid ;
- filtres globaux Zustand ;
- cross-filtering ;
- drill-down ;
- dashboards temps reel ;
- Power BI Embedded futur.

---

## Architecture

```text
React / Vercel
    |
    v
/analytics/*
    |
    v
AnalyticsService
    |
    v
AnalyticsRepository
    |
    v
PostgreSQL views + fact_metre
```

Le moteur est ajoute dans :

```text
07_API_BACKEND/app/analytics/
  cache/
  repositories/
  routes/
  schemas/
  services/
  sql/
  utils/
```

---

## Integration FastAPI

`app.main` monte le routeur :

```text
app.include_router(analytics_router, prefix="/analytics")
```

Au startup, `cloud_migrations.py` execute aussi les vues SQL analytics. Cela
permet a Render de mettre a jour une base PostgreSQL existante progressivement.

---

## Contrat API standard

Tous les endpoints analytics retournent :

```json
{
  "status": "SUCCESS",
  "filters": {},
  "pagination": {},
  "kpis": {},
  "charts": {},
  "table": [],
  "metadata": {}
}
```

Ce format est concu pour :

- React Query ;
- ECharts ;
- AG Grid ;
- dashboards filtrables ;
- evolution future vers Power BI Embedded.

---

## Endpoints disponibles

| Endpoint | Role |
|---|---|
| `/analytics/dashboard` | Dataset cockpit complet |
| `/analytics/kpis` | KPI centralises |
| `/analytics/capex` | Analyse CAPEX |
| `/analytics/risk` | Analyse risque |
| `/analytics/procurement` | Analyse procurement |
| `/analytics/logistics` | Analyse logistique |
| `/analytics/scenarios` | Analyse scenarios |
| `/analytics/heatmap` | Dataset heatmap |
| `/analytics/drilldown` | Drill-down hierarchique |
| `/analytics/timeline` | Donnees temporelles |
| `/analytics/system-health` | Etat moteur analytics |
| `/analytics/query-performance` | Performance requetes |
| `/analytics/cache-status` | Etat cache |
| `/analytics/debug/pipeline` | Diagnostic DQE -> PostgreSQL -> KPI |

---

## Filtres supportes

Les filtres cibles sont :

```text
projet
scenario
batiment
niveau
lot
famille
fournisseur
decision_import
periode_debut
periode_fin
criticite
statut_chantier
```

La V1 supporte les filtres disponibles selon les colonnes presentes dans
PostgreSQL. Les filtres manquants doivent etre ignores proprement ou retournes
dans `warnings`.

---

## Drill-down

Hierarchie metier cible :

```text
Projet
  -> Batiment
    -> Niveau
      -> Lot
        -> Famille
          -> Article
```

Le frontend peut utiliser cette hierarchie pour :

- charts interactifs ;
- navigation analytique ;
- details ligne ;
- comparaison par niveau de granularite.

---

## KPI centralises

Le moteur doit centraliser les KPI :

- CAPEX local ;
- CAPEX importe ;
- CAPEX optimise ;
- economie nette ;
- taux economie ;
- taux importable ;
- risque global ;
- delai moyen ;
- cout logistique ;
- criticite chantier.

Regle financiere importante :

```text
taux economie global = SUM(economie) / SUM(capex_local)
```

Ne jamais calculer un taux global par `AVG(taux_economie)`.

---

## Vues SQL creees

Les vues creees par la migration douce sont :

```text
vw_capex_summary
vw_capex_by_lot
vw_capex_by_building
vw_import_analysis
vw_procurement_risk
vw_logistics_summary
vw_project_kpis
vw_dashboard_direction
vw_dashboard_import
vw_dashboard_chantier
```

Elles sont volontairement compatibles avec les schemas progressifs : si certaines
colonnes avancees ne sont pas encore alimentees, le moteur doit rester tolerant.

---

## Cache

La V1 contient un cache memoire simple :

```text
app/analytics/cache/
```

Objectif :

- eviter de recalculer des petites aggregations frequentes ;
- preparer une migration Redis ;
- conserver une API simple pour les services.

Le cache memoire est suffisant pour les tests Render, mais il ne remplace pas un
cache distribue pour une V2 multi-instance.

---

## Compatibilite frontend

Le frontend peut brancher :

- `useQuery(["analytics-dashboard", filters], ...)`
- `GlobalFilterBar`
- `EnterpriseKpiCard`
- `BIChart`
- `SmartDataGrid`

Les filtres Zustand doivent etre transformes en query params vers
`/analytics/dashboard` ou les endpoints specialises.

---

## Diagnostic pipeline

Si les KPI retournent `0` alors que l'upload fonctionne, utiliser :

```text
GET /analytics/debug/pipeline
```

Ce endpoint retourne :

- nombre de lignes dans `fact_metre` ;
- colonnes reelles de la table ;
- sommes SQL directes ;
- preview des 20 dernieres lignes ;
- resultat des vues `vw_capex_summary`, `vw_project_kpis`,
  `vw_dashboard_direction` ;
- warnings explicites si la table est vide ou si `capex_local` vaut 0.

Cause typique corrigee :

```text
Le preview IA detectait les lignes Excel, mais la generation FACT_METRE ignorait
les lignes dont `prix_total_ht` etait absent. Le pipeline recalcule maintenant
capex_local avec quantite x prix_unitaire quand le montant total n'est pas
fourni explicitement.
```

---

## Roadmap V2

1. Materialized views PostgreSQL pour dashboards lourds.
2. Pagination serveur avancee pour AG Grid.
3. Exports Excel serveur.
4. Cache Redis.
5. Isolation multi-tenant.
6. JWT et permissions dashboard.
7. Refresh temps reel.
8. Power BI Embedded avec contexte projet/scenario.
