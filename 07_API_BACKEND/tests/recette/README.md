# Recette fonctionnelle V6 (backend réel, base isolée)

> Complète la matrice `docs/ANOMALY_MATRIX_COCKPIT_V6.md`.
> Cette recette **ne valide pas la chaîne complète de migrations** : voir
> `docs/VALIDATION_CHAINE_MIGRATIONS_V6.md` (les deux sont volontairement
> séparés).

## Principe

Scénarios exécutés **sans interception des API métier** : un vrai backend
FastAPI (uvicorn), une vraie base PostgreSQL **isolée** (conteneur
`sp2i_capex_test_pg`, port 5433) et des données **100 % synthétiques**.
Aucune donnée réelle, aucune connexion de production.

Le schéma n'est **pas** obtenu en lançant tous les fichiers
`09_INFRA/sql/*.sql` par ordre de nom :
- le dépôt prévoit que `Base.metadata.create_all` + `ensure_powerbi_schema`
  complètent une base au démarrage, mais `ensure_powerbi_schema` rejoue des
  vues V5 qui exigent la chaîne de migrations complète et **échoue sur une
  base vierge** ;
- les objets V6 exercés ici sont donc créés par `recipe_v6_schema.sql`, dont
  les vues `vw_project_cost_summary_v6`, `vw_dashboard_direction_v6_scoped`
  et `vw_cost_intelligence_v6_scoped` sont **extraites de `033`** pour rester
  conformes à la définition de production.

## Contenu du dossier

| Fichier | Rôle |
|---|---|
| `recipe_v6_schema.sql` | Schéma V6 synthétique (vues extraites de `033` + faits) |
| `_generate.py`, `_part1.sql`, `_part3.sql` | Génération de `recipe_v6_schema.sql` (reproductibilité) |
| `prepare_recipe_db.py` | Crée la base, applique `create_all`, le schéma V6 et les identités |
| `run_recette.py` | Exécute les scénarios (assertions, rapport JSON) |
| `run_recette_report.json` | Résultat de la dernière exécution |

## Procédure

```powershell
# 1. Base isolee (conteneur deja present : sp2i_capex_test_pg, port 5433)
docker exec sp2i_capex_test_pg psql -U user -d postgres `
  -c "DROP DATABASE IF EXISTS sp2i_capex_recipe;" -c "CREATE DATABASE sp2i_capex_recipe;"

# 2. Schema + seed (depuis 07_API_BACKEND, venv actif)
python tests/recette/prepare_recipe_db.py

# 3. Backend reel (ALLOW_STARTUP_SCHEMA_MUTATIONS=false : on ne rejoue pas
#    ensure_powerbi_schema sur une base isolee)
$env:DATABASE_URL="postgresql://user:password@localhost:5433/sp2i_capex_recipe"
$env:ALLOW_STARTUP_SCHEMA_MUTATIONS="false"
$env:SP2I_JWT_SECRET="recette-local-secret-change-before-production-0123456789"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 4. Scenarios (autre terminal)
python tests/recette/run_recette.py
```

## Scénarios couverts (dernière exécution : 17/17 OK)

1. **Connexion** : admin + analyste OK, mauvais mot de passe 401.
2. **Changement de projet** : PROJET_A `capex_direct` = 3000, PROJET_B = 500,
   aucun mélange inter-projets.
3. **Projet vide** (PROJET_C) : 200, KPI monétaires à 0, aucune erreur.
4. **Filtre niveau** : `niveau=RDC` sur A → `capex_direct` = 1000.
5. **Cohérence KPI / graphiques / détails** : dashboard 3 lots dont la somme
   égale le capex projet (3000) ; KPI `total_project_cost` = 3988.32 cohérent
   avec le tableau ; cost-intelligence renvoie les 4 lignes fines et leur somme
   égale le `capex_direct`.
6. **Ratio indisponible** : PROJET_D filtré (géométrie non résolvable) →
   `surface_m2`, `capex_m2`, `total_project_cost_per_m2` = `null` (le frontend
   affiche « Indisponible pour ce perimetre », jamais 0).
7. **Refus d'accès** : analyste autorisé sur A (200), refusé sur B (404
   « Projet introuvable »), refusé sans projet (403).

Le rapport détaillé est écrit dans `run_recette_report.json`.

## Synchronisation réelle (test backend) — `prepare_sync_db.py`

`test_excel_sync_datetime_serialization` effectue une **vraie synchronisation**
(ServicePipeline → PostgreSQL). Il a besoin des tables/colonnes écrites par la
synchronisation. La base isolée `sp2i_capex_sync_test` est préparée par
`prepare_sync_db.py` : `create_all` ORM + **DDL extrait tel quel de
`cloud_migrations`** (`ensure_powerbi_schema`, sans `ANALYTICS_VIEWS_SQL`).
Suite backend : **31 passed**.

## Parcours navigateur avec API réelle — ✅ 5/5

`08_FRONTEND/tests/e2e/real-api-recipe.spec.js` (config dédiée
`playwright.realapi.config.js`, aucun `page.route()` sur l'API métier).

Commande dédiée (backend recette lancé, ex. `python tests/recette/_run_backend.py`) :

```powershell
$env:VITE_SP2I_USE_V6_FINANCIALS='true'
npx playwright test --config=playwright.realapi.config.js
```

Scénarios : connexion, projet A (CAPEX Direct = 3 000 FCFA), filtre niveau RDC
(1 000 FCFA), projet B (500 FCFA), projet vide C (aucun montant résiduel),
ratio indisponible sur D (niveau S1 → « Indisponible pour ce perimetre »).

Blocage `/analytics/filters` levé : (1) la vue `vw_fact_metre_current`
(dépendance du endpoint) a été ajoutée au schéma de recette
(`recipe_v6_schema.sql`, grain synthétique) ; (2) bug applicatif corrigé dans
`_piece_filter_options` (bind `:projet` non transmis) avec test de régression
dans `tests/test_project_isolation.py`. Voir
`docs/VALIDATION_CHAINE_MIGRATIONS_V6.md`.
