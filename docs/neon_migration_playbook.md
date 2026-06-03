# SP2I CAPEX - Migration PostgreSQL locale vers Neon

## Objectif

Copier la base locale `sp2i_capex` vers Neon `neondb`, puis faire de Neon la source unique pour FastAPI, React et Power BI.

Architecture cible :

```text
Local PostgreSQL -> Neon PostgreSQL -> Render FastAPI -> Vercel React
Power BI -> Neon PostgreSQL
```

## Variables

PowerShell :

```powershell
$env:PGPASSWORD="password"
$LOCAL_URL="postgresql://user:password@localhost:5432/sp2i_capex"
$NEON_URL="postgresql://USER:PASSWORD@HOST.neon.tech/neondb?sslmode=require"
$DUMP_FILE="sp2i_capex_neon.dump"
```

Ne pas commiter la vraie valeur de `$NEON_URL`.

## Dump local

Format custom recommandé :

```powershell
pg_dump --format=custom --verbose --no-owner --no-acl --dbname $LOCAL_URL --file $DUMP_FILE
```

## Restore Neon

Pour une base Neon vide :

```powershell
pg_restore --verbose --no-owner --no-acl --dbname $NEON_URL $DUMP_FILE
```

Pour remplacer intégralement une base Neon de recette déjà remplie :

```powershell
pg_restore --verbose --clean --if-exists --no-owner --no-acl --dbname $NEON_URL $DUMP_FILE
```

## Vues Power BI

Le backend exécute `ensure_powerbi_schema(engine)` au démarrage et recrée les vues Analytics depuis `app/analytics/sql/views.py`.

Si un contrôle manuel est nécessaire, exécuter le SQL de `ANALYTICS_VIEWS_SQL` sur Neon ou redémarrer Render après avoir configuré `DATABASE_URL`.

Vues attendues :

```sql
SELECT * FROM vw_capex_summary;
SELECT * FROM vw_project_kpis;
SELECT * FROM vw_dashboard_direction;
SELECT * FROM vw_dashboard_import;
SELECT * FROM vw_dashboard_chantier LIMIT 20;
```

## Contrôles post-migration

```sql
SELECT COUNT(*) FROM fact_metre;
-- attendu: 290

SELECT SUM(capex_local) FROM fact_metre;
-- attendu: 113928000

SELECT * FROM vw_capex_summary;
-- attendu: capex_brut proche de 113928000, nb_lignes = 290
```

Contrôle API après déploiement Render :

```powershell
curl https://sp2i-backend.onrender.com/analytics/debug/database
curl https://sp2i-backend.onrender.com/analytics/dashboard
```

Attendu :

```json
{
  "database_name": "neondb",
  "fact_metre_count": 290,
  "capex_local_total": 113928000,
  "is_neon": true
}
```

## Configuration Render

Dans Render, définir manuellement :

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST.neon.tech/neondb?sslmode=require
DB_POOL_SIZE=2
DB_MAX_OVERFLOW=3
DB_POOL_RECYCLE=1800
DB_CONNECT_TIMEOUT=10
```

`render.yaml` ne provisionne plus de PostgreSQL Render et attend `DATABASE_URL` comme secret.

## Rollback

1. Remettre `DATABASE_URL` Render vers l'ancienne base PostgreSQL Render.
2. Redéployer le backend Render.
3. Vérifier :

```powershell
curl https://sp2i-backend.onrender.com/analytics/debug/database
curl https://sp2i-backend.onrender.com/analytics/dashboard
```

4. Conserver le dump local `sp2i_capex_neon.dump` jusqu'à validation finale.

Rollback data Neon si le restore est incomplet :

```powershell
pg_restore --verbose --clean --if-exists --no-owner --no-acl --dbname $NEON_URL $DUMP_FILE
```

