-- SP2I CAPEX - Rollback 024 V5.3 fact_metre compatibility fix v2
--
-- Rollback non destructif:
-- - ne modifie aucune table metier ;
-- - ne supprime aucune donnee ;
-- - recree les vues avec la baseline V5.3 precedente.
--
-- Option recommandee:
-- reexecuter 024_v53_fact_metre_compatibility_fix.sql si l'on souhaite
-- revenir a la version de compatibilite precedente sans sous_lot_id.
--
-- Option baseline:
-- reexecuter 018_vw_fact_metre_v53_financial.sql puis
-- 021_v53_read_cutover.sql selon l'etat cible souhaite.

BEGIN;

DO $$
BEGIN
    RAISE NOTICE 'Rollback 024 v2 is procedural and non destructive.';
    RAISE NOTICE 'Recommended: re-run 09_INFRA/sql/024_v53_fact_metre_compatibility_fix.sql.';
    RAISE NOTICE 'Baseline option: re-run 018 then 021 according to the desired cutover state.';
END $$;

ROLLBACK;
