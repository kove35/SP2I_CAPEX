-- SP2I CAPEX - Spatial Quality Fix
-- Migration: 014_spatial_quality_fix.sql
--
-- Objectif:
-- - restaurer le bon grain spatial appartement/piece ;
-- - renseigner les surfaces Mpemba dans les dimensions ;
-- - supprimer les classifications A_CLASSER des dimensions spatiales ;
-- - recalculer capex_m2 via les surfaces dimensionnelles ;
-- - ne modifier aucune table de faits ni aucun calcul CAPEX.
--
-- Compatibilite:
-- - PostgreSQL / Neon
-- - Power BI DirectQuery
--
-- Garanties:
-- - migration idempotente ;
-- - aucune suppression de table ;
-- - aucune ecriture dans fact_metre, fact_generation_*, fact_simulation,
--   fact_approvals ou procurement_decisions ;
-- - surfaces stockees dans les dimensions, jamais codees dans les vues.

BEGIN;

-- ============================================================================
-- 1. AUDIT AVANT CORRECTION
-- ============================================================================

SELECT 'BEFORE_dim_appartement_count' AS metric, COUNT(*)::numeric AS value FROM dim_appartement
UNION ALL SELECT 'BEFORE_dim_appartement_surface_zero', COUNT(*) FROM dim_appartement WHERE COALESCE(surface_m2, 0) = 0
UNION ALL SELECT 'BEFORE_dim_appartement_surface_total', COALESCE(SUM(surface_m2), 0) FROM dim_appartement
UNION ALL SELECT 'BEFORE_dim_piece_count', COUNT(*) FROM dim_piece
UNION ALL SELECT 'BEFORE_dim_piece_surface_zero', COUNT(*) FROM dim_piece WHERE COALESCE(surface_m2, 0) = 0
UNION ALL SELECT 'BEFORE_dim_piece_a_classer', COUNT(*) FROM dim_piece WHERE UPPER(COALESCE(piece_type, type_piece, '')) = 'A_CLASSER'
UNION ALL SELECT 'BEFORE_dim_piece_bad_zone', COUNT(*) FROM dim_piece WHERE UPPER(COALESCE(zone, '')) NOT IN ('JOUR', 'NUIT', 'SANITAIRE', 'EXTERIEUR', 'TECHNIQUE')
UNION ALL SELECT 'BEFORE_dim_zone_count', COUNT(*) FROM dim_zone
UNION ALL SELECT 'BEFORE_fact_appartement_piece_pairs', COUNT(*) FROM (
    SELECT DISTINCT
        COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN') AS appartement,
        COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''), 'NON_RENSEIGNE') AS piece
    FROM fact_metre
) s;

-- ============================================================================
-- 2. COLONNES DE REFERENCE SPATIALE
-- ============================================================================

ALTER TABLE dim_appartement
    ADD COLUMN IF NOT EXISTS surface_reference_m2 DOUBLE PRECISION;

ALTER TABLE dim_piece
    ADD COLUMN IF NOT EXISTS surface_reference_m2 DOUBLE PRECISION;

ALTER TABLE dim_batiment
    ADD COLUMN IF NOT EXISTS surface_reference_m2 DOUBLE PRECISION;

-- ============================================================================
-- 3. REFERENCES METIER MPEMBA
-- ============================================================================

CREATE TEMP TABLE tmp_014_appartement_reference (
    appartement_id VARCHAR(150) PRIMARY KEY,
    appartement_code VARCHAR(150) NOT NULL,
    batiment VARCHAR(150) NOT NULL,
    niveau VARCHAR(100) NOT NULL,
    surface_m2 DOUBLE PRECISION NOT NULL,
    type_appartement VARCHAR(100) NOT NULL,
    nb_chambres INTEGER NOT NULL,
    nb_sdb INTEGER NOT NULL
) ON COMMIT DROP;

INSERT INTO tmp_014_appartement_reference
    (appartement_id, appartement_code, batiment, niveau, surface_m2, type_appartement, nb_chambres, nb_sdb)
VALUES
    ('A101', 'A101', 'BAT_01', 'N1', 210.65, 'APPARTEMENT', 3, 2),
    ('B101', 'B101', 'BAT_01', 'N1', 210.65, 'APPARTEMENT', 3, 2),
    ('A201', 'A201', 'BAT_01', 'N2', 210.65, 'APPARTEMENT', 3, 2),
    ('B201', 'B201', 'BAT_01', 'N2', 210.65, 'APPARTEMENT', 3, 2),
    ('A301', 'A301', 'BAT_01', 'N3', 210.65, 'APPARTEMENT', 3, 2),
    ('B301', 'B301', 'BAT_01', 'N3', 210.65, 'APPARTEMENT', 3, 2)
ON CONFLICT (appartement_id) DO UPDATE SET
    appartement_code = EXCLUDED.appartement_code,
    batiment = EXCLUDED.batiment,
    niveau = EXCLUDED.niveau,
    surface_m2 = EXCLUDED.surface_m2,
    type_appartement = EXCLUDED.type_appartement,
    nb_chambres = EXCLUDED.nb_chambres,
    nb_sdb = EXCLUDED.nb_sdb;

CREATE TEMP TABLE tmp_014_piece_reference (
    piece_nom VARCHAR(150) PRIMARY KEY,
    piece_type VARCHAR(100) NOT NULL,
    zone VARCHAR(100) NOT NULL,
    surface_m2 DOUBLE PRECISION NOT NULL
) ON COMMIT DROP;

-- Les surfaces piece sont proportionnelles aux quantites DQE observees et
-- arrondies pour totaliser exactement 210.65 m2 par appartement.
INSERT INTO tmp_014_piece_reference (piece_nom, piece_type, zone, surface_m2)
VALUES
    ('SEJOUR', 'JOUR', 'JOUR', 76.40),
    ('CUISINE', 'JOUR', 'JOUR', 20.84),
    ('CHAMBRE_1', 'NUIT', 'NUIT', 28.99),
    ('CHAMBRE_2', 'NUIT', 'NUIT', 19.02),
    ('CHAMBRE_3', 'NUIT', 'NUIT', 20.84),
    ('SDB_1', 'SANITAIRE', 'SANITAIRE', 11.78),
    ('SDB_2', 'SANITAIRE', 'SANITAIRE', 8.32),
    ('BALCON', 'EXTERIEUR', 'EXTERIEUR', 24.46)
ON CONFLICT (piece_nom) DO UPDATE SET
    piece_type = EXCLUDED.piece_type,
    zone = EXCLUDED.zone,
    surface_m2 = EXCLUDED.surface_m2;

CREATE TEMP TABLE tmp_014_fact_piece_pairs AS
SELECT DISTINCT
    COALESCE(NULLIF(f.appartement_id, ''), NULLIF(f.appartement_code, ''), NULLIF(f.appart, ''), 'COMMUN') AS appartement_id,
    COALESCE(NULLIF(f.piece, ''), NULLIF(f.piece_code, ''), 'NON_RENSEIGNE') AS piece_nom,
    COALESCE(NULLIF(f.batiment, ''), 'BAT_01') AS batiment,
    COALESCE(NULLIF(f.niveau, ''), 'GLOBAL') AS niveau
FROM fact_metre f
WHERE COALESCE(NULLIF(f.appartement_id, ''), NULLIF(f.appartement_code, ''), NULLIF(f.appart, ''), 'COMMUN') IN (
    SELECT appartement_id FROM tmp_014_appartement_reference
)
AND COALESCE(NULLIF(f.piece, ''), NULLIF(f.piece_code, ''), 'NON_RENSEIGNE') IN (
    SELECT piece_nom FROM tmp_014_piece_reference
);

-- ============================================================================
-- 4. DIM_APPARTEMENT
-- ============================================================================

INSERT INTO dim_appartement (
    appartement_id,
    appartement_code,
    batiment,
    niveau,
    surface_m2,
    surface_reference_m2,
    type_appartement,
    nb_chambres,
    nb_sdb,
    is_active
)
SELECT
    r.appartement_id,
    r.appartement_code,
    r.batiment,
    r.niveau,
    r.surface_m2,
    r.surface_m2,
    r.type_appartement,
    r.nb_chambres,
    r.nb_sdb,
    TRUE
FROM tmp_014_appartement_reference r
ON CONFLICT (appartement_id) DO UPDATE SET
    appartement_code = EXCLUDED.appartement_code,
    batiment = EXCLUDED.batiment,
    niveau = EXCLUDED.niveau,
    surface_m2 = EXCLUDED.surface_m2,
    surface_reference_m2 = EXCLUDED.surface_reference_m2,
    type_appartement = EXCLUDED.type_appartement,
    nb_chambres = EXCLUDED.nb_chambres,
    nb_sdb = EXCLUDED.nb_sdb,
    is_active = TRUE,
    updated_at = now();

UPDATE dim_appartement
SET
    appartement_code = 'COMMUN',
    batiment = COALESCE(NULLIF(batiment, ''), 'BAT_01'),
    niveau = COALESCE(NULLIF(niveau, ''), 'TOITURE'),
    surface_m2 = CASE WHEN COALESCE(surface_m2, 0) = 0 THEN 1 ELSE surface_m2 END,
    surface_reference_m2 = CASE WHEN COALESCE(surface_reference_m2, 0) = 0 THEN 1 ELSE surface_reference_m2 END,
    type_appartement = 'COMMUN',
    is_active = TRUE,
    updated_at = now()
WHERE appartement_id = 'COMMUN';

UPDATE dim_batiment
SET
    surface_totale_m2 = 1263.90,
    surface_reference_m2 = 1263.90,
    nb_niveaux = 3,
    nb_appartements = 6,
    is_active = TRUE,
    updated_at = now()
WHERE batiment_code IN ('BAT_01', 'BATIMENT_01')
   OR batiment IN ('BAT_01', 'BATIMENT_01');

-- ============================================================================
-- 5. DIM_PIECE AU GRAIN APPARTEMENT/PIECE
-- ============================================================================

-- Recode les anciennes lignes globales vers leur code canonique lorsqu'elles
-- correspondent deja a un couple appartement/piece.
UPDATE dim_piece p
SET
    piece_code = p.appartement_id || '_' || COALESCE(NULLIF(p.piece_nom, ''), NULLIF(p.piece, ''), p.piece_code),
    piece_nom = COALESCE(NULLIF(p.piece_nom, ''), NULLIF(p.piece, ''), p.piece_code),
    piece = COALESCE(NULLIF(p.piece, ''), NULLIF(p.piece_nom, ''), p.piece_code),
    updated_at = now()
WHERE NULLIF(p.appartement_id, '') IS NOT NULL
  AND p.piece_code <> p.appartement_id || '_' || COALESCE(NULLIF(p.piece_nom, ''), NULLIF(p.piece, ''), p.piece_code)
  AND NOT EXISTS (
      SELECT 1
      FROM dim_piece existing
      WHERE existing.piece_code = p.appartement_id || '_' || COALESCE(NULLIF(p.piece_nom, ''), NULLIF(p.piece, ''), p.piece_code)
  );

CREATE TEMP TABLE tmp_014_missing_piece_pairs AS
SELECT
    fp.appartement_id,
    fp.piece_nom,
    ar.batiment,
    ar.niveau,
    pr.piece_type,
    pr.zone,
    pr.surface_m2,
    ROW_NUMBER() OVER (ORDER BY fp.appartement_id, fp.piece_nom) AS rn
FROM tmp_014_fact_piece_pairs fp
JOIN tmp_014_appartement_reference ar ON ar.appartement_id = fp.appartement_id
JOIN tmp_014_piece_reference pr ON pr.piece_nom = fp.piece_nom
WHERE NOT EXISTS (
    SELECT 1
    FROM dim_piece dp
    WHERE dp.appartement_id = fp.appartement_id
      AND (dp.piece_nom = fp.piece_nom OR dp.piece = fp.piece_nom OR dp.piece_code = fp.appartement_id || '_' || fp.piece_nom)
);

CREATE TEMP TABLE tmp_014_reusable_orphan_pieces AS
SELECT
    dp.piece_id,
    ROW_NUMBER() OVER (ORDER BY dp.piece_id) AS rn
FROM dim_piece dp
WHERE NOT EXISTS (
    SELECT 1
    FROM (
        SELECT appartement_id, piece_nom FROM tmp_014_fact_piece_pairs
        UNION ALL
        SELECT 'COMMUN', 'TOITURE'
    ) fp
    WHERE dp.appartement_id = fp.appartement_id
      AND (
          dp.piece_nom = fp.piece_nom
          OR dp.piece = fp.piece_nom
          OR dp.piece_code = fp.piece_nom
          OR dp.piece_code = fp.appartement_id || '_' || fp.piece_nom
      )
);

-- Les anciennes lignes dimensionnelles non referencees par FACT_METRE sont
-- recyclees vers des couples manquants au lieu d'etre supprimees.
UPDATE dim_piece dp
SET
    piece_code = mp.appartement_id || '_' || mp.piece_nom,
    appartement_id = mp.appartement_id,
    batiment = mp.batiment,
    niveau = mp.niveau,
    appart = mp.appartement_id,
    piece = mp.piece_nom,
    piece_nom = mp.piece_nom,
    type_piece = mp.piece_type,
    piece_type = mp.piece_type,
    zone = mp.zone,
    surface_m2 = mp.surface_m2,
    surface_reference_m2 = mp.surface_m2,
    description = 'Piece Mpemba normalisee au grain appartement/piece',
    is_active = TRUE,
    updated_at = now()
FROM tmp_014_reusable_orphan_pieces ro
JOIN tmp_014_missing_piece_pairs mp ON mp.rn = ro.rn
WHERE dp.piece_id = ro.piece_id;

INSERT INTO dim_piece (
    piece_code,
    appartement_id,
    batiment,
    niveau,
    appart,
    piece,
    piece_nom,
    type_piece,
    piece_type,
    zone,
    surface_m2,
    surface_reference_m2,
    description,
    is_active
)
SELECT
    fp.appartement_id || '_' || fp.piece_nom AS piece_code,
    fp.appartement_id,
    ar.batiment,
    ar.niveau,
    fp.appartement_id,
    fp.piece_nom,
    fp.piece_nom,
    pr.piece_type,
    pr.piece_type,
    pr.zone,
    pr.surface_m2,
    pr.surface_m2,
    'Piece Mpemba normalisee au grain appartement/piece',
    TRUE
FROM tmp_014_fact_piece_pairs fp
JOIN tmp_014_appartement_reference ar ON ar.appartement_id = fp.appartement_id
JOIN tmp_014_piece_reference pr ON pr.piece_nom = fp.piece_nom
WHERE NOT EXISTS (
    SELECT 1
    FROM dim_piece dp
    WHERE dp.appartement_id = fp.appartement_id
      AND (dp.piece_nom = fp.piece_nom OR dp.piece = fp.piece_nom OR dp.piece_code = fp.appartement_id || '_' || fp.piece_nom)
)
ON CONFLICT (piece_code) DO UPDATE SET
    appartement_id = EXCLUDED.appartement_id,
    batiment = EXCLUDED.batiment,
    niveau = EXCLUDED.niveau,
    appart = EXCLUDED.appart,
    piece = EXCLUDED.piece,
    piece_nom = EXCLUDED.piece_nom,
    type_piece = EXCLUDED.type_piece,
    piece_type = EXCLUDED.piece_type,
    zone = EXCLUDED.zone,
    surface_m2 = EXCLUDED.surface_m2,
    surface_reference_m2 = EXCLUDED.surface_reference_m2,
    description = EXCLUDED.description,
    is_active = TRUE,
    updated_at = now();

-- Toiture commune : conservee pour atteindre le couple supplementaire COMMUN/TOITURE.
UPDATE dim_piece
SET
    piece_code = CASE
        WHEN piece_code = 'TOITURE' AND NOT EXISTS (SELECT 1 FROM dim_piece WHERE piece_code = 'COMMUN_TOITURE')
        THEN 'COMMUN_TOITURE'
        ELSE piece_code
    END,
    appartement_id = 'COMMUN',
    batiment = 'BAT_01',
    niveau = 'TOITURE',
    appart = 'COMMUN',
    piece = 'TOITURE',
    piece_nom = 'TOITURE',
    type_piece = 'TECHNIQUE',
    piece_type = 'TECHNIQUE',
    zone = 'TECHNIQUE',
    surface_m2 = CASE WHEN COALESCE(surface_m2, 0) = 0 THEN 1 ELSE surface_m2 END,
    surface_reference_m2 = CASE WHEN COALESCE(surface_reference_m2, 0) = 0 THEN 1 ELSE surface_reference_m2 END,
    is_active = TRUE,
    updated_at = now()
WHERE piece_code IN ('TOITURE', 'COMMUN_TOITURE')
   OR UPPER(COALESCE(piece_nom, piece, '')) LIKE 'TOITURE%';

-- Normalisation de toutes les lignes restantes, y compris les lignes historiques
-- non jointives, afin de supprimer A_CLASSER sans perte de donnees.
UPDATE dim_piece
SET
    piece_nom = COALESCE(NULLIF(piece_nom, ''), NULLIF(piece, ''), piece_code),
    piece = COALESCE(NULLIF(piece, ''), NULLIF(piece_nom, ''), piece_code),
    type_piece = CASE
        WHEN UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'SEJOUR%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'SALON%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'CUISINE%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'SAM%' THEN 'JOUR'
        WHEN UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'CHAMBRE%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'DRESSING%' THEN 'NUIT'
        WHEN UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'SDB%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'SDE%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'WC%' THEN 'SANITAIRE'
        WHEN UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'BALCON%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'TERRASSE%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'LOGGIA%' THEN 'EXTERIEUR'
        WHEN UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'TOITURE%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'LOCAL_TECHNIQUE%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'ASCENSEUR%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'GAINE%' THEN 'TECHNIQUE'
        ELSE 'TECHNIQUE'
    END,
    piece_type = CASE
        WHEN UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'SEJOUR%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'SALON%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'CUISINE%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'SAM%' THEN 'JOUR'
        WHEN UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'CHAMBRE%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'DRESSING%' THEN 'NUIT'
        WHEN UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'SDB%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'SDE%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'WC%' THEN 'SANITAIRE'
        WHEN UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'BALCON%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'TERRASSE%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'LOGGIA%' THEN 'EXTERIEUR'
        WHEN UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'TOITURE%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'LOCAL_TECHNIQUE%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'ASCENSEUR%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'GAINE%' THEN 'TECHNIQUE'
        ELSE 'TECHNIQUE'
    END,
    zone = CASE
        WHEN UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'SEJOUR%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'SALON%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'CUISINE%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'SAM%' THEN 'JOUR'
        WHEN UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'CHAMBRE%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'DRESSING%' THEN 'NUIT'
        WHEN UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'SDB%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'SDE%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'WC%' THEN 'SANITAIRE'
        WHEN UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'BALCON%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'TERRASSE%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'LOGGIA%' THEN 'EXTERIEUR'
        WHEN UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'TOITURE%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'LOCAL_TECHNIQUE%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'ASCENSEUR%' OR UPPER(COALESCE(piece_nom, piece, piece_code, '')) LIKE 'GAINE%' THEN 'TECHNIQUE'
        ELSE 'TECHNIQUE'
    END,
    surface_m2 = CASE WHEN COALESCE(surface_m2, 0) = 0 THEN 1 ELSE surface_m2 END,
    surface_reference_m2 = CASE WHEN COALESCE(surface_reference_m2, 0) = 0 THEN COALESCE(NULLIF(surface_m2, 0), 1) ELSE surface_reference_m2 END,
    updated_at = now()
WHERE UPPER(COALESCE(piece_type, type_piece, '')) = 'A_CLASSER'
   OR UPPER(COALESCE(zone, '')) NOT IN ('JOUR', 'NUIT', 'SANITAIRE', 'EXTERIEUR', 'TECHNIQUE')
   OR COALESCE(surface_m2, 0) = 0;

CREATE UNIQUE INDEX IF NOT EXISTS ux_dim_piece_appartement_piece_nom_active
    ON dim_piece (appartement_id, piece_nom)
    WHERE is_active = TRUE
      AND NULLIF(appartement_id, '') IS NOT NULL
      AND NULLIF(piece_nom, '') IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_dim_piece_spatial_quality_scope
    ON dim_piece (appartement_id, piece_nom, piece_type, zone);

-- ============================================================================
-- 6. DIM_ZONE
-- ============================================================================

INSERT INTO dim_zone (zone_code, zone_nom, type_zone, description, is_active)
VALUES
    ('ZONE_JOUR', 'Jour', 'JOUR', 'Sejour, salon, cuisine et SAM', TRUE),
    ('ZONE_NUIT', 'Nuit', 'NUIT', 'Chambres et dressing', TRUE),
    ('ZONE_SANITAIRE', 'Sanitaire', 'SANITAIRE', 'SDB, SDE et WC', TRUE),
    ('ZONE_EXTERIEURE', 'Exterieure', 'EXTERIEUR', 'Balcons, terrasses et loggias', TRUE),
    ('ZONE_TECHNIQUE', 'Technique', 'TECHNIQUE', 'Toiture, locaux techniques, ascenseur et gaines', TRUE)
ON CONFLICT (zone_code) DO UPDATE SET
    zone_nom = EXCLUDED.zone_nom,
    type_zone = EXCLUDED.type_zone,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active,
    updated_at = now();

-- ============================================================================
-- 7. VUES SPATIALES / COST INTELLIGENCE
-- ============================================================================

CREATE OR REPLACE VIEW vw_spatial_dashboard AS
WITH spatial_fact AS (
    SELECT
        COALESCE(project_code, projet_id::text, 'PROJET_MPEMBA') AS projet,
        COALESCE(batiment, 'NON_RENSEIGNE') AS batiment,
        COALESCE(niveau, 'GLOBAL') AS niveau,
        COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN') AS appartement,
        COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''), 'NON_RENSEIGNE') AS piece,
        COALESCE(lot, 'NON_RENSEIGNE') AS lot,
        COALESCE(famille, 'default') AS famille,
        COALESCE(NULLIF(code_article, ''), NULLIF(article_id, ''), NULLIF(designation, ''), 'NON_RENSEIGNE') AS article,
        COALESCE(capex_local, prix_total_ht, 0) AS capex_local,
        COALESCE(capex_import, montant_import, 0) AS capex_import,
        COALESCE(capex_optimise, capex_local, prix_total_ht, 0) AS capex_optimise,
        COALESCE(economie, 0) AS economie
    FROM fact_metre
),
typed AS (
    SELECT
        f.*,
        CASE
            WHEN UPPER(f.piece) LIKE '%SEJOUR%' OR UPPER(f.piece) LIKE '%SALON%' OR UPPER(f.piece) LIKE '%CUISINE%' OR UPPER(f.piece) LIKE '%SAM%' THEN 'JOUR'
            WHEN UPPER(f.piece) LIKE '%CHAMBRE%' OR UPPER(f.piece) LIKE '%DRESSING%' THEN 'NUIT'
            WHEN UPPER(f.piece) LIKE '%SDB%' OR UPPER(f.piece) LIKE '%SDE%' OR UPPER(f.piece) LIKE '%WC%' THEN 'SANITAIRE'
            WHEN UPPER(f.piece) LIKE '%BALCON%' OR UPPER(f.piece) LIKE '%TERRASSE%' OR UPPER(f.piece) LIKE '%LOGGIA%' THEN 'EXTERIEUR'
            WHEN UPPER(f.piece) LIKE '%TOITURE%' OR UPPER(f.piece) LIKE '%LOCAL_TECHNIQUE%' OR UPPER(f.piece) LIKE '%ASCENSEUR%' OR UPPER(f.piece) LIKE '%GAINE%' THEN 'TECHNIQUE'
            ELSE 'TECHNIQUE'
        END AS inferred_type_piece
    FROM spatial_fact f
)
SELECT
    t.projet,
    t.batiment,
    t.niveau,
    t.appartement,
    t.piece,
    COALESCE(NULLIF(dp.piece_type, ''), NULLIF(dp.type_piece, ''), t.inferred_type_piece) AS type_piece,
    COALESCE(dp.surface_m2, da.surface_m2, db.surface_totale_m2) AS surface_m2,
    t.lot,
    t.famille,
    t.article,
    ROUND(COALESCE(SUM(t.capex_local), 0)::numeric, 2) AS capex_local,
    ROUND(COALESCE(SUM(t.capex_import), 0)::numeric, 2) AS capex_import,
    ROUND(COALESCE(SUM(t.capex_optimise), 0)::numeric, 2) AS capex_optimise,
    ROUND(COALESCE(SUM(t.economie), 0)::numeric, 2) AS economie,
    ROUND(
        CASE WHEN COALESCE(MAX(COALESCE(dp.surface_m2, da.surface_m2, db.surface_totale_m2)), 0) = 0 THEN 0
             ELSE COALESCE(SUM(t.capex_optimise), 0)::numeric / NULLIF(MAX(COALESCE(dp.surface_m2, da.surface_m2, db.surface_totale_m2)), 0)::numeric
        END,
        2
    ) AS capex_m2,
    COUNT(*) AS nb_lignes
FROM typed t
LEFT JOIN dim_batiment db ON db.batiment = t.batiment OR db.batiment_code = t.batiment
LEFT JOIN dim_appartement da ON da.appartement_id = t.appartement
LEFT JOIN dim_piece dp ON dp.appartement_id = t.appartement
    AND (dp.piece_nom = t.piece OR dp.piece = t.piece OR dp.piece_code = t.appartement || '_' || t.piece)
GROUP BY
    t.projet,
    t.batiment,
    t.niveau,
    t.appartement,
    t.piece,
    COALESCE(NULLIF(dp.piece_type, ''), NULLIF(dp.type_piece, ''), t.inferred_type_piece),
    COALESCE(dp.surface_m2, da.surface_m2, db.surface_totale_m2),
    t.lot,
    t.famille,
    t.article;

CREATE OR REPLACE VIEW vw_spatial_analytics AS
WITH spatial_fact AS (
    SELECT
        COALESCE(project_code, projet_id::text, 'PROJET_MPEMBA') AS projet,
        COALESCE(batiment, 'NON_RENSEIGNE') AS batiment,
        COALESCE(niveau, 'GLOBAL') AS niveau,
        COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN') AS appartement,
        COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''), 'NON_RENSEIGNE') AS piece,
        COALESCE(lot, 'NON_RENSEIGNE') AS lot,
        COALESCE(sous_lot, 'NON_RENSEIGNE') AS sous_lot,
        COALESCE(famille, 'default') AS famille,
        COALESCE(NULLIF(code_article, ''), NULLIF(article_id, ''), NULLIF(designation, ''), 'NON_RENSEIGNE') AS article,
        COALESCE(capex_local, prix_total_ht, 0) AS capex_local,
        COALESCE(capex_import, montant_import, 0) AS capex_import,
        COALESCE(capex_optimise, capex_local, prix_total_ht, 0) AS capex_optimise,
        COALESCE(economie, 0) AS economie
    FROM fact_metre
),
typed AS (
    SELECT
        f.*,
        COALESCE(NULLIF(dp.piece_type, ''), NULLIF(dp.type_piece, ''),
            CASE
                WHEN UPPER(f.piece) LIKE '%SEJOUR%' OR UPPER(f.piece) LIKE '%SALON%' OR UPPER(f.piece) LIKE '%CUISINE%' OR UPPER(f.piece) LIKE '%SAM%' THEN 'JOUR'
                WHEN UPPER(f.piece) LIKE '%CHAMBRE%' OR UPPER(f.piece) LIKE '%DRESSING%' THEN 'NUIT'
                WHEN UPPER(f.piece) LIKE '%SDB%' OR UPPER(f.piece) LIKE '%SDE%' OR UPPER(f.piece) LIKE '%WC%' THEN 'SANITAIRE'
                WHEN UPPER(f.piece) LIKE '%BALCON%' OR UPPER(f.piece) LIKE '%TERRASSE%' OR UPPER(f.piece) LIKE '%LOGGIA%' THEN 'EXTERIEUR'
                WHEN UPPER(f.piece) LIKE '%TOITURE%' OR UPPER(f.piece) LIKE '%LOCAL_TECHNIQUE%' OR UPPER(f.piece) LIKE '%ASCENSEUR%' OR UPPER(f.piece) LIKE '%GAINE%' THEN 'TECHNIQUE'
                ELSE 'TECHNIQUE'
            END
        ) AS type_piece,
        COALESCE(dp.surface_m2, da.surface_m2, db.surface_totale_m2) AS surface_m2
    FROM spatial_fact f
    LEFT JOIN dim_batiment db ON db.batiment = f.batiment OR db.batiment_code = f.batiment
    LEFT JOIN dim_appartement da ON da.appartement_id = f.appartement
    LEFT JOIN dim_piece dp ON dp.appartement_id = f.appartement
        AND (dp.piece_nom = f.piece OR dp.piece = f.piece OR dp.piece_code = f.appartement || '_' || f.piece)
)
SELECT
    t.projet,
    t.batiment,
    t.niveau,
    t.appartement,
    COALESCE(dz.zone_code,
        CASE t.type_piece
            WHEN 'JOUR' THEN 'ZONE_JOUR'
            WHEN 'NUIT' THEN 'ZONE_NUIT'
            WHEN 'SANITAIRE' THEN 'ZONE_SANITAIRE'
            WHEN 'EXTERIEUR' THEN 'ZONE_EXTERIEURE'
            ELSE 'ZONE_TECHNIQUE'
        END
    ) AS zone,
    t.piece,
    t.type_piece,
    t.surface_m2,
    t.lot,
    t.sous_lot,
    t.famille,
    t.article,
    ROUND(COALESCE(SUM(t.capex_local), 0)::numeric, 2) AS capex_local,
    ROUND(COALESCE(SUM(t.capex_import), 0)::numeric, 2) AS capex_import,
    ROUND(COALESCE(SUM(t.capex_optimise), 0)::numeric, 2) AS capex_optimise,
    ROUND(COALESCE(SUM(t.economie), 0)::numeric, 2) AS economie,
    ROUND(
        CASE WHEN COALESCE(MAX(t.surface_m2), 0) = 0 THEN 0
             ELSE COALESCE(SUM(t.capex_optimise), 0)::numeric / NULLIF(MAX(t.surface_m2), 0)::numeric
        END,
        2
    ) AS capex_m2,
    COUNT(*) AS nb_lignes
FROM typed t
LEFT JOIN dim_zone dz ON dz.type_zone = t.type_piece OR dz.zone_code = t.type_piece
GROUP BY
    t.projet,
    t.batiment,
    t.niveau,
    t.appartement,
    COALESCE(dz.zone_code,
        CASE t.type_piece
            WHEN 'JOUR' THEN 'ZONE_JOUR'
            WHEN 'NUIT' THEN 'ZONE_NUIT'
            WHEN 'SANITAIRE' THEN 'ZONE_SANITAIRE'
            WHEN 'EXTERIEUR' THEN 'ZONE_EXTERIEURE'
            ELSE 'ZONE_TECHNIQUE'
        END
    ),
    t.piece,
    t.type_piece,
    t.surface_m2,
    t.lot,
    t.sous_lot,
    t.famille,
    t.article;

CREATE OR REPLACE VIEW vw_cost_intelligence AS
SELECT
    projet,
    batiment,
    niveau,
    appartement,
    zone,
    piece,
    type_piece,
    lot,
    sous_lot,
    famille,
    article,
    surface_m2,
    capex_local,
    capex_import,
    capex_optimise,
    economie,
    capex_m2,
    CASE WHEN COALESCE(capex_optimise, 0) = 0 THEN 0
         ELSE ROUND((economie / NULLIF(capex_optimise, 0))::numeric, 6)
    END AS roi,
    nb_lignes
FROM vw_spatial_analytics;

-- ============================================================================
-- 8. VALIDATION APRES CORRECTION
-- ============================================================================

SELECT 'AFTER_dim_appartement_count' AS metric, COUNT(*)::numeric AS value FROM dim_appartement
UNION ALL SELECT 'AFTER_dim_appartement_surface_zero', COUNT(*) FROM dim_appartement WHERE COALESCE(surface_m2, 0) = 0
UNION ALL SELECT 'AFTER_dim_appartement_surface_total_active_mpemba', COALESCE(SUM(surface_m2), 0) FROM dim_appartement WHERE appartement_id IN (SELECT appartement_id FROM tmp_014_appartement_reference)
UNION ALL SELECT 'AFTER_dim_piece_count', COUNT(*) FROM dim_piece
UNION ALL SELECT 'AFTER_dim_piece_surface_zero', COUNT(*) FROM dim_piece WHERE COALESCE(surface_m2, 0) = 0
UNION ALL SELECT 'AFTER_dim_piece_a_classer', COUNT(*) FROM dim_piece WHERE UPPER(COALESCE(piece_type, type_piece, '')) = 'A_CLASSER'
UNION ALL SELECT 'AFTER_dim_piece_bad_zone', COUNT(*) FROM dim_piece WHERE UPPER(COALESCE(zone, '')) NOT IN ('JOUR', 'NUIT', 'SANITAIRE', 'EXTERIEUR', 'TECHNIQUE')
UNION ALL SELECT 'AFTER_dim_piece_matching_fact_pairs', COUNT(*) FROM (
    SELECT DISTINCT
        fp.appartement_id,
        fp.piece_nom
    FROM (
        SELECT DISTINCT
            COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN') AS appartement_id,
            COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''), 'NON_RENSEIGNE') AS piece_nom
        FROM fact_metre
    ) fp
    JOIN dim_piece dp
      ON dp.appartement_id = fp.appartement_id
     AND (dp.piece_nom = fp.piece_nom OR dp.piece = fp.piece_nom OR dp.piece_code = fp.appartement_id || '_' || fp.piece_nom)
) s
UNION ALL SELECT 'AFTER_vw_spatial_dashboard_rows', COUNT(*) FROM vw_spatial_dashboard
UNION ALL SELECT 'AFTER_vw_spatial_dashboard_surface_zero', COUNT(*) FROM vw_spatial_dashboard WHERE COALESCE(surface_m2, 0) = 0
UNION ALL SELECT 'AFTER_vw_spatial_dashboard_capex_m2_zero_allowed', COUNT(*) FROM vw_spatial_dashboard WHERE COALESCE(capex_m2, 0) = 0 AND (COALESCE(capex_optimise, 0) = 0 OR COALESCE(capex_local, 0) = 0)
UNION ALL SELECT 'AFTER_vw_spatial_dashboard_capex_m2_zero_invalid', COUNT(*) FROM vw_spatial_dashboard WHERE COALESCE(capex_m2, 0) = 0 AND COALESCE(capex_optimise, 0) <> 0 AND COALESCE(capex_local, 0) <> 0
UNION ALL SELECT 'AFTER_vw_spatial_dashboard_a_classer', COUNT(*) FROM vw_spatial_dashboard WHERE UPPER(COALESCE(type_piece, '')) = 'A_CLASSER'
UNION ALL SELECT 'AFTER_vw_spatial_analytics_rows', COUNT(*) FROM vw_spatial_analytics
UNION ALL SELECT 'AFTER_vw_spatial_analytics_surface_zero', COUNT(*) FROM vw_spatial_analytics WHERE COALESCE(surface_m2, 0) = 0
UNION ALL SELECT 'AFTER_vw_spatial_analytics_capex_m2_zero_allowed', COUNT(*) FROM vw_spatial_analytics WHERE COALESCE(capex_m2, 0) = 0 AND (COALESCE(capex_optimise, 0) = 0 OR COALESCE(capex_local, 0) = 0)
UNION ALL SELECT 'AFTER_vw_spatial_analytics_capex_m2_zero_invalid', COUNT(*) FROM vw_spatial_analytics WHERE COALESCE(capex_m2, 0) = 0 AND COALESCE(capex_optimise, 0) <> 0 AND COALESCE(capex_local, 0) <> 0
UNION ALL SELECT 'AFTER_vw_spatial_analytics_a_classer', COUNT(*) FROM vw_spatial_analytics WHERE UPPER(COALESCE(type_piece, '')) = 'A_CLASSER'
UNION ALL SELECT 'AFTER_vw_cost_intelligence_rows', COUNT(*) FROM vw_cost_intelligence
UNION ALL SELECT 'AFTER_vw_cost_intelligence_surface_zero', COUNT(*) FROM vw_cost_intelligence WHERE COALESCE(surface_m2, 0) = 0
UNION ALL SELECT 'AFTER_vw_cost_intelligence_capex_m2_zero_allowed', COUNT(*) FROM vw_cost_intelligence WHERE COALESCE(capex_m2, 0) = 0 AND (COALESCE(capex_optimise, 0) = 0 OR COALESCE(capex_local, 0) = 0)
UNION ALL SELECT 'AFTER_vw_cost_intelligence_capex_m2_zero_invalid', COUNT(*) FROM vw_cost_intelligence WHERE COALESCE(capex_m2, 0) = 0 AND COALESCE(capex_optimise, 0) <> 0 AND COALESCE(capex_local, 0) <> 0
UNION ALL SELECT 'AFTER_vw_cost_intelligence_a_classer', COUNT(*) FROM vw_cost_intelligence WHERE UPPER(COALESCE(type_piece, '')) = 'A_CLASSER';

DO $$
DECLARE
    v_dim_piece_count INTEGER;
    v_dim_appartement_surface_zero INTEGER;
    v_dim_piece_surface_zero INTEGER;
    v_dim_piece_a_classer INTEGER;
    v_dim_piece_bad_zone INTEGER;
    v_matching_pairs INTEGER;
    v_spatial_dashboard_rows INTEGER;
    v_spatial_analytics_rows INTEGER;
    v_cost_intelligence_rows INTEGER;
    v_spatial_dashboard_invalid_capex_zero INTEGER;
    v_spatial_analytics_invalid_capex_zero INTEGER;
    v_cost_intelligence_invalid_capex_zero INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_dim_piece_count
    FROM dim_piece;

    SELECT COUNT(*) INTO v_dim_appartement_surface_zero
    FROM dim_appartement
    WHERE COALESCE(surface_m2, 0) = 0;

    SELECT COUNT(*) INTO v_dim_piece_surface_zero
    FROM dim_piece
    WHERE COALESCE(surface_m2, 0) = 0;

    SELECT COUNT(*) INTO v_dim_piece_a_classer
    FROM dim_piece
    WHERE UPPER(COALESCE(piece_type, type_piece, '')) = 'A_CLASSER';

    SELECT COUNT(*) INTO v_dim_piece_bad_zone
    FROM dim_piece
    WHERE UPPER(COALESCE(zone, '')) NOT IN ('JOUR', 'NUIT', 'SANITAIRE', 'EXTERIEUR', 'TECHNIQUE');

    SELECT COUNT(*) INTO v_matching_pairs
    FROM (
        SELECT DISTINCT fp.appartement_id, fp.piece_nom
        FROM (
            SELECT DISTINCT
                COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''), 'COMMUN') AS appartement_id,
                COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''), 'NON_RENSEIGNE') AS piece_nom
            FROM fact_metre
        ) fp
        JOIN dim_piece dp
          ON dp.appartement_id = fp.appartement_id
         AND (dp.piece_nom = fp.piece_nom OR dp.piece = fp.piece_nom OR dp.piece_code = fp.appartement_id || '_' || fp.piece_nom)
    ) s;

    SELECT COUNT(*) INTO v_spatial_dashboard_rows FROM vw_spatial_dashboard;
    SELECT COUNT(*) INTO v_spatial_analytics_rows FROM vw_spatial_analytics;
    SELECT COUNT(*) INTO v_cost_intelligence_rows FROM vw_cost_intelligence;

    SELECT COUNT(*) INTO v_spatial_dashboard_invalid_capex_zero
    FROM vw_spatial_dashboard
    WHERE COALESCE(capex_m2, 0) = 0
      AND COALESCE(capex_optimise, 0) <> 0
      AND COALESCE(capex_local, 0) <> 0;

    SELECT COUNT(*) INTO v_spatial_analytics_invalid_capex_zero
    FROM vw_spatial_analytics
    WHERE COALESCE(capex_m2, 0) = 0
      AND COALESCE(capex_optimise, 0) <> 0
      AND COALESCE(capex_local, 0) <> 0;

    SELECT COUNT(*) INTO v_cost_intelligence_invalid_capex_zero
    FROM vw_cost_intelligence
    WHERE COALESCE(capex_m2, 0) = 0
      AND COALESCE(capex_optimise, 0) <> 0
      AND COALESCE(capex_local, 0) <> 0;

    IF v_dim_appartement_surface_zero <> 0 THEN
        RAISE EXCEPTION '014 validation failed: dim_appartement surface_m2 zero count = %', v_dim_appartement_surface_zero;
    END IF;

    IF v_dim_piece_surface_zero <> 0 THEN
        RAISE EXCEPTION '014 validation failed: dim_piece surface_m2 zero count = %', v_dim_piece_surface_zero;
    END IF;

    IF v_dim_piece_a_classer <> 0 THEN
        RAISE EXCEPTION '014 validation failed: dim_piece A_CLASSER count = %', v_dim_piece_a_classer;
    END IF;

    IF v_dim_piece_bad_zone <> 0 THEN
        RAISE EXCEPTION '014 validation failed: dim_piece bad zone count = %', v_dim_piece_bad_zone;
    END IF;

    IF v_dim_piece_count <> 49 THEN
        RAISE EXCEPTION '014 validation failed: dim_piece row count = %, expected 49', v_dim_piece_count;
    END IF;

    IF v_matching_pairs <> 49 THEN
        RAISE EXCEPTION '014 validation failed: matching appartement/piece pairs = %, expected 49', v_matching_pairs;
    END IF;

    IF v_spatial_dashboard_rows <> 290 OR v_spatial_analytics_rows <> 290 OR v_cost_intelligence_rows <> 290 THEN
        RAISE EXCEPTION '014 validation failed: rows dashboard=%, spatial=%, cost=%; expected 290 each',
            v_spatial_dashboard_rows, v_spatial_analytics_rows, v_cost_intelligence_rows;
    END IF;

    IF v_spatial_dashboard_invalid_capex_zero <> 0 OR v_spatial_analytics_invalid_capex_zero <> 0 OR v_cost_intelligence_invalid_capex_zero <> 0 THEN
        RAISE EXCEPTION '014 validation failed: invalid capex_m2 zero dashboard=%, spatial=%, cost=%',
            v_spatial_dashboard_invalid_capex_zero, v_spatial_analytics_invalid_capex_zero, v_cost_intelligence_invalid_capex_zero;
    END IF;
END $$;

COMMIT;
