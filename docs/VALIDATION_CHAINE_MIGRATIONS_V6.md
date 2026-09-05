# Validation de la chaîne complète de migrations (V6)

> Document **distinct** de la recette fonctionnelle :
> `07_API_BACKEND/tests/recette/README.md` (backend réel + base isolée + schéma
> synthétique). Ne pas confondre les deux périmètres.

## Pourquoi une validation séparée ?

La recette isolee valide la **logique de calcul** des correctifs V6 sur un
schéma minimal fidèle (vues extraites de `033`, faits synthétiques). Elle ne
prouve pas que la **chaîne de migrations** `09_INFRA/sql/001..033` s'applique
proprement sur une base neuve, ni que les vues V6 de production se comportent
comme leurs copies de test.

Preuves de la nécessité d'une séparation :
- `033_v6_financial_reconciliation.sql` **refuse de s'appliquer** si
  `vw_fact_metre_financial_canonical`, `vw_fact_metre_current`,
  `vw_bpu_v53_priced_v2` ou `dim_projet` n'existent pas (garde `DO $$`).
- `ensure_powerbi_schema` (vues V5) **échoue sur une base vierge** : il rejoue
  des vues qui supposent la chaîne de migrations appliquée.
- Le test `test_excel_sync_datetime_serialization` (fixture `admin_auth`
  corrigée) atteint maintenant le code applicatif et échoue uniquement sur le
  schéma : `relation "dim_lot" does not exist` → HTTP 422. Il passera au vert
  seulement sur une base ayant reçu la chaîne complète.

## Périmètre de la validation « chaîne de migrations »

Non exécutée dans ce lot (nécessite un environnement dédié). La procédure
prévue par le dépôt — **à ne pas exécuter aveuglément par ordre de nom** :

1. Déterminer l'ordre de dépendances réel (les fichiers `0NN` ne sont pas
   purement séquentiels : `018` précède `031` qui précède `033`, et des
   correctifs `022_fixed`, `024_v2` existent).
2. Appliquer sur une base neuve **isolée** :
   - `001` → `018` (schéma Power BI / fact_metre enrichi) ;
   - `020`/`021`/`022_fixed`/`023`/`024_v2`/`025` (bascules V5.3) ;
   - `031` (production readiness V6) puis `033` (reconciliation financière
     V6). Vérifier que les gardes `DO $$` de `033` passent.
3. Rejouer chaque `validation_queries_NNN.sql` associé.
4. Recréer la recette (`prepare_recipe_db.py` **sans** le SQL synthétique)
   puis relancer :
   - `tests/integration/test_v6_spatial_kpi.py` sur le schéma **de
     production** (et non la copie minimale) ;
   - `tests/recette/run_recette.py` ;
   - `tests/test_sync_datetime_serialization.py` (doit passer au vert une
     fois `dim_lot` / `fact_simulation` présents).

## État au 05/09/2026

| Catégorie | Résultat |
|---|---|
| Tests unitaires backend (pytest, base isolée `sp2i_capex_sync_test`) | ✅ **31 passed** (inclut `test_excel_sync_datetime_serialization`, synchronisation réelle, après application du DDL de `cloud_migrations` via `prepare_sync_db.py`) |
| Intégration PostgreSQL (vue V6, données synthétiques) | ✅ `ALL_V6_SPATIAL_KPI_CHECKS_PASSED` |
| Recette API réelle (backend uvicorn + PostgreSQL isolé) | ✅ **17/17** scénarios (`tests/recette/run_recette.py`) |
| Tests navigateur avec API simulée (`page.route`) | ✅ **27/27** (`workflow-project.spec.js`) |
| Tests navigateur avec API réelle | ⚠️ **partiel / à établir** : connexion OK + sélection projet A + KPI « CAPEX Direct = 3 000 FCFA » confirmés ; **filtre niveau et ratio indisponible bloqués** car `/analytics/filters?projet=1` répond **HTTP 500** sur le schéma minimal de recette (menu « Niveau » sans options) — cause exacte et preuves dans `08_FRONTEND/tests/e2e/real-api-recipe.spec.js` |
| Chaîne complète de migrations `001..033` sur base neuve | ⏳ **non validée** (procédure ci-dessus, environnement dédié requis) |
