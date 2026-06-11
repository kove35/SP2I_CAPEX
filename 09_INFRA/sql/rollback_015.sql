-- SP2I CAPEX - Rollback 015 V5.3 DQE Master
-- Supprime uniquement la vue additive creee par 015_v53_dqe_master_view.sql.

BEGIN;

DROP VIEW IF EXISTS vw_sp2i_generated_dqe_master;

COMMIT;
