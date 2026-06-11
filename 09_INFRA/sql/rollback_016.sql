-- SP2I CAPEX - Rollback 016 BPU V5.3
-- Supprime uniquement la table additive creee par 016_dim_bpu_v53.sql.

BEGIN;

DROP TABLE IF EXISTS dim_bpu_v53;

COMMIT;
