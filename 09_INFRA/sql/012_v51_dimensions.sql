-- SP2I CAPEX - V5.1 Enterprise Production dimensions
-- Migration: 012_v51_dimensions.sql
--
-- Objectif:
-- - preparer la couche BIM/DQE V5.1 sans modifier les tables existantes ;
-- - ajouter uniquement des dimensions additives ;
-- - conserver la compatibilite Power BI, Analytics et Procurement.
--
-- Compatibilite:
-- - PostgreSQL 18
-- - Neon PostgreSQL
-- - Power BI Import/DirectQuery
--
-- Garanties:
-- - aucune table existante supprimee ;
-- - aucune table existante renommee ;
-- - aucun endpoint impacte ;
-- - migration idempotente ;
-- - rollback documente en fin de fichier.

BEGIN;

-- ============================================================================
-- 1. DIM_TYPE_PIECE
-- ============================================================================

CREATE TABLE IF NOT EXISTS dim_type_piece (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(80) NOT NULL UNIQUE,
    designation VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE dim_type_piece IS
    'V5.1 - Referentiel des types de pieces pour generation BIM vers DQE.';

COMMENT ON COLUMN dim_type_piece.code IS
    'Code stable du type de piece: SEJOUR, CUISINE, CH1, SDB1, etc.';

INSERT INTO dim_type_piece (code, designation, is_active)
VALUES
    ('SEJOUR', 'Sejour', TRUE),
    ('CUISINE', 'Cuisine', TRUE),
    ('CH1', 'Chambre 1', TRUE),
    ('CH2', 'Chambre 2', TRUE),
    ('CH3', 'Chambre 3', TRUE),
    ('DRESSING', 'Dressing', TRUE),
    ('SDB1', 'Salle de bain 1', TRUE),
    ('SDB2', 'Salle de bain 2', TRUE),
    ('WC', 'WC', TRUE),
    ('DEGAGEMENT', 'Degagement', TRUE),
    ('BALCON', 'Balcon', TRUE),
    ('ESCALIER', 'Escalier', TRUE)
ON CONFLICT (code) DO NOTHING;

-- ============================================================================
-- 2. DIM_SURFACE_REFERENCE
-- ============================================================================

CREATE TABLE IF NOT EXISTS dim_surface_reference (
    id BIGSERIAL PRIMARY KEY,
    type_piece_id BIGINT NOT NULL REFERENCES dim_type_piece(id),
    surface_reference_m2 NUMERIC(12, 2) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_dim_surface_reference_type_piece UNIQUE (type_piece_id)
);

COMMENT ON TABLE dim_surface_reference IS
    'V5.1 - Surfaces de reference BAT_01 par type de piece.';

INSERT INTO dim_surface_reference (
    type_piece_id,
    surface_reference_m2,
    description
)
SELECT tp.id, seed.surface_reference_m2, seed.description
FROM (
    VALUES
        ('SEJOUR', 70.00::NUMERIC, 'BAT_01 - Surface reference sejour'),
        ('CH1', 29.00::NUMERIC, 'BAT_01 - Surface reference chambre 1'),
        ('CH2', 19.00::NUMERIC, 'BAT_01 - Surface reference chambre 2'),
        ('CH3', 18.00::NUMERIC, 'BAT_01 - Surface reference chambre 3'),
        ('CUISINE', 12.00::NUMERIC, 'BAT_01 - Surface reference cuisine'),
        ('DRESSING', 7.60::NUMERIC, 'BAT_01 - Surface reference dressing'),
        ('SDB1', 9.13::NUMERIC, 'BAT_01 - Surface reference salle de bain 1'),
        ('SDB2', 9.13::NUMERIC, 'BAT_01 - Surface reference salle de bain 2'),
        ('WC', 2.50::NUMERIC, 'BAT_01 - Surface reference WC'),
        ('DEGAGEMENT', 25.00::NUMERIC, 'BAT_01 - Surface reference degagement'),
        ('BALCON', 18.00::NUMERIC, 'BAT_01 - Surface reference balcon')
) AS seed(code, surface_reference_m2, description)
JOIN dim_type_piece tp
  ON tp.code = seed.code
ON CONFLICT (type_piece_id) DO NOTHING;

-- ============================================================================
-- 3. DIM_REGLE_METIER
-- ============================================================================

CREATE TABLE IF NOT EXISTS dim_regle_metier (
    id BIGSERIAL PRIMARY KEY,
    type_piece_id BIGINT NOT NULL REFERENCES dim_type_piece(id),
    article_code VARCHAR(180) NOT NULL,
    formule VARCHAR(255) NOT NULL,
    unite VARCHAR(40) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_dim_regle_metier_rule UNIQUE (type_piece_id, article_code, formule)
);

COMMENT ON TABLE dim_regle_metier IS
    'V5.1 - Regles metier de generation des quantites DQE depuis type de piece et surface.';

COMMENT ON COLUMN dim_regle_metier.formule IS
    'Expression metier V5.1. Exemples: Surface/7, Surface/10, 2, 4.';

INSERT INTO dim_regle_metier (
    type_piece_id,
    article_code,
    formule,
    unite,
    is_active
)
SELECT tp.id, seed.article_code, seed.formule, seed.unite, TRUE
FROM (
    VALUES
        ('SEJOUR', 'SPOT_LED', 'Surface/7', 'U'),
        ('SEJOUR', 'PRISE_2PT', 'Surface/10', 'U'),
        ('SEJOUR', 'RJ45', '2', 'U'),
        ('SEJOUR', 'SPLIT_18000_BTU', '2', 'U'),
        ('CUISINE', 'PRISE_PLAN_TRAVAIL', '4', 'U'),
        ('CUISINE', 'PRISE_FRIGO', '1', 'U'),
        ('SDB1', 'WC', '1', 'U'),
        ('SDB1', 'DOUCHE', '1', 'U'),
        ('SDB2', 'WC', '1', 'U'),
        ('SDB2', 'DOUCHE', '1', 'U')
) AS seed(type_piece_code, article_code, formule, unite)
JOIN dim_type_piece tp
  ON tp.code = seed.type_piece_code
ON CONFLICT (type_piece_id, article_code, formule) DO NOTHING;

-- ============================================================================
-- 4. DIM_UNITE
-- ============================================================================

CREATE TABLE IF NOT EXISTS dim_unite (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(40) NOT NULL UNIQUE,
    designation VARCHAR(255) NOT NULL
);

COMMENT ON TABLE dim_unite IS
    'V5.1 - Referentiel des unites DQE/BPU.';

INSERT INTO dim_unite (code, designation)
VALUES
    ('U', 'Unite'),
    ('ML', 'Metre lineaire'),
    ('M2', 'Metre carre'),
    ('M3', 'Metre cube'),
    ('KG', 'Kilogramme'),
    ('ENS', 'Ensemble'),
    ('FORFAIT', 'Forfait')
ON CONFLICT (code) DO NOTHING;

-- ============================================================================
-- 5. DIM_MARQUE
-- ============================================================================

CREATE TABLE IF NOT EXISTS dim_marque (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(120) NOT NULL UNIQUE,
    designation VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE dim_marque IS
    'V5.1 - Marques de demonstration pour BPU, procurement et cost intelligence.';

INSERT INTO dim_marque (code, designation, is_active)
VALUES
    ('SP2I_REF', 'SP2I Reference', TRUE),
    ('SCHNEIDER', 'Schneider Electric', TRUE),
    ('LEGRAND', 'Legrand', TRUE),
    ('DAIKIN', 'Daikin', TRUE),
    ('GROHE', 'Grohe', TRUE),
    ('ALUCOBOND', 'Alucobond', TRUE),
    ('ROCKWOOL', 'Rockwool', TRUE),
    ('JINKO_SOLAR', 'Jinko Solar', TRUE)
ON CONFLICT (code) DO NOTHING;

-- ============================================================================
-- 6. INDEX
-- ============================================================================

CREATE INDEX IF NOT EXISTS ix_dim_type_piece_code
    ON dim_type_piece (code);

CREATE INDEX IF NOT EXISTS ix_dim_surface_reference_type_piece_id
    ON dim_surface_reference (type_piece_id);

CREATE INDEX IF NOT EXISTS ix_dim_regle_metier_type_piece_id
    ON dim_regle_metier (type_piece_id);

CREATE INDEX IF NOT EXISTS ix_dim_regle_metier_article_code
    ON dim_regle_metier (article_code);

CREATE INDEX IF NOT EXISTS ix_dim_unite_code
    ON dim_unite (code);

CREATE INDEX IF NOT EXISTS ix_dim_marque_code
    ON dim_marque (code);

COMMIT;

-- ============================================================================
-- 7. VALIDATION POST-MIGRATION
-- ============================================================================
-- Ces requetes sont read-only et peuvent etre executees apres la migration.

SELECT 'dim_type_piece' AS relation_name, COUNT(*) AS rows_count
FROM dim_type_piece
UNION ALL
SELECT 'dim_surface_reference', COUNT(*)
FROM dim_surface_reference
UNION ALL
SELECT 'dim_regle_metier', COUNT(*)
FROM dim_regle_metier
UNION ALL
SELECT 'dim_unite', COUNT(*)
FROM dim_unite
UNION ALL
SELECT 'dim_marque', COUNT(*)
FROM dim_marque
ORDER BY relation_name;

SELECT
    tp.code AS type_piece,
    sr.surface_reference_m2,
    sr.description
FROM dim_surface_reference sr
JOIN dim_type_piece tp
  ON tp.id = sr.type_piece_id
ORDER BY tp.code;

SELECT
    tp.code AS type_piece,
    rm.article_code,
    rm.formule,
    rm.unite,
    rm.is_active
FROM dim_regle_metier rm
JOIN dim_type_piece tp
  ON tp.id = rm.type_piece_id
ORDER BY tp.code, rm.article_code;

-- Controle de compatibilite: ces objets historiques doivent toujours exister.
SELECT
    relation_name,
    to_regclass(relation_name) IS NOT NULL AS exists_after_012
FROM (
    VALUES
        ('fact_metre'),
        ('fact_simulation'),
        ('fact_shipment'),
        ('fact_logistics_cost'),
        ('fact_approvals'),
        ('procurement_decisions'),
        ('dim_projet'),
        ('dim_batiment'),
        ('dim_niveau'),
        ('dim_appartement'),
        ('dim_piece'),
        ('dim_zone'),
        ('dim_lot'),
        ('dim_sous_lot'),
        ('dim_sous_lot_complet'),
        ('dim_famille'),
        ('dim_article_bpu'),
        ('dim_article_bpu_extended'),
        ('dim_supplier'),
        ('dim_country'),
        ('dim_scenario'),
        ('vw_capex_summary'),
        ('vw_dim_lot_active'),
        ('vw_dim_sous_lot_active'),
        ('vw_dim_article_bpu_active')
) AS expected(relation_name)
ORDER BY relation_name;

-- ============================================================================
-- 8. RAPPORT D'IMPACT
-- ============================================================================
-- Impact attendu:
-- - tables ajoutees: dim_type_piece, dim_surface_reference, dim_regle_metier,
--   dim_unite, dim_marque ;
-- - aucune table existante modifiee ;
-- - aucune vue existante modifiee ;
-- - aucun endpoint backend modifie ;
-- - aucun objet Power BI existant renomme ;
-- - preparation de la future generation BIM -> DQE via dim_regle_metier.
--
-- Risques:
-- - risque fonctionnel faible, car migration additive ;
-- - risque de collision faible sur noms de tables si elles ont ete creees
--   manuellement hors migration ; CREATE TABLE IF NOT EXISTS protege le run ;
-- - rollback destructif seulement pour les nouvelles tables V5.1.

-- ============================================================================
-- 9. ROLLBACK 012_V51_DIMENSIONS
-- ============================================================================
-- Executer ce bloc uniquement en cas de rollback explicite.
-- Il ne touche aucune table historique.
--
-- BEGIN;
-- DROP TABLE IF EXISTS dim_regle_metier CASCADE;
-- DROP TABLE IF EXISTS dim_surface_reference CASCADE;
-- DROP TABLE IF EXISTS dim_marque CASCADE;
-- DROP TABLE IF EXISTS dim_unite CASCADE;
-- DROP TABLE IF EXISTS dim_type_piece CASCADE;
-- COMMIT;
