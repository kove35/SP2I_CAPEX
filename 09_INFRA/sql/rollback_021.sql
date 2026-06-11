-- SP2I CAPEX - Rollback 021 V5.3 read cutover
--
-- Actions:
-- 1. Remettre la variable backend:
--    SP2I_FACT_SOURCE=fact_metre
--
-- 2. Reexecuter la migration Power BI historique:
--    sql/powerbi/001_powerbi_views.sql
--
-- 3. Supprimer la source canonique de lecture V5.3.

BEGIN;

DROP VIEW IF EXISTS vw_fact_metre_current;

COMMIT;
