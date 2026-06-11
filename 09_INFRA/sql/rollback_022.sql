-- SP2I CAPEX - Rollback 022 V5.3 dimensions rebuild
--
-- Option recommandee si 021 reste la baseline de cutover:
-- reexecuter 09_INFRA/sql/021_v53_read_cutover.sql apres correction/validation.
--
-- Option de retour complet aux vues Power BI historiques:
-- reexecuter 09_INFRA/sql/011_powerbi_neon_integrity_fix.sql
-- ou sql/powerbi/001_powerbi_views.sql selon la baseline cible.
--
-- Ce rollback ne supprime aucune table metier et ne modifie pas fact_metre.

BEGIN;

DO $$
BEGIN
    RAISE NOTICE 'Rollback 022 is procedural: re-run the selected baseline script explicitly.';
    RAISE NOTICE 'Recommended V5.3 baseline: 09_INFRA/sql/021_v53_read_cutover.sql';
    RAISE NOTICE 'Historical baseline: 09_INFRA/sql/011_powerbi_neon_integrity_fix.sql or sql/powerbi/001_powerbi_views.sql';
END $$;

COMMIT;
