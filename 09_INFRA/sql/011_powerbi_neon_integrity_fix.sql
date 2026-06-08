-- SP2I CAPEX - Power BI Neon integrity fix
-- Migration additive et idempotente.
-- Objectif :
-- - creer les vues actives Power BI ;
-- - eviter les segments Lot/Sous-lot/Article sans faits ;
-- - aligner le referentiel article sur les codes reellement presents ;
-- - rendre les KPI surface non bloquants.

BEGIN;

-- 1. Colonnes surface attendues par Power BI.
ALTER TABLE dim_piece
    ADD COLUMN IF NOT EXISTS surface_m2 DOUBLE PRECISION;

ALTER TABLE dim_appartement
    ADD COLUMN IF NOT EXISTS surface_m2 DOUBLE PRECISION;

-- Ne pas inventer de surface : si aucune source n'existe, garder 0 pour eviter BLANK.
UPDATE dim_piece
SET surface_m2 = 0
WHERE surface_m2 IS NULL;

UPDATE dim_appartement
SET surface_m2 = 0
WHERE surface_m2 IS NULL;

-- 2. Normalisation non destructive des articles.
-- Si fact_metre.code_article est absent mais article_id renseigne, le code
-- article Power BI devient l'identifiant article reel de la ligne.
UPDATE fact_metre
SET code_article = article_id
WHERE COALESCE(NULLIF(TRIM(code_article), ''), '') = ''
  AND COALESCE(NULLIF(TRIM(article_id), ''), '') <> '';

-- 3. Dimensions techniques : ajouter les colonnes utiles si le schema est ancien.
ALTER TABLE dim_lot
    ADD COLUMN IF NOT EXISTS description VARCHAR(255) NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE dim_sous_lot_complet
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE dim_article_bpu
    ADD COLUMN IF NOT EXISTS article_id VARCHAR(150) NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS lot_id VARCHAR(150) NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS sous_lot_id VARCHAR(150) NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS designation VARCHAR(500) NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS marque VARCHAR(255) NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS unite VARCHAR(50) NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

-- 4. Enrichir les dimensions depuis les faits reels, sans mapping invente.
INSERT INTO dim_lot (lot, description, is_active)
SELECT DISTINCT
    TRIM(f.lot) AS lot,
    TRIM(f.lot) AS description,
    TRUE AS is_active
FROM fact_metre f
WHERE COALESCE(NULLIF(TRIM(f.lot), ''), '') <> ''
ON CONFLICT (lot) DO UPDATE SET
    description = COALESCE(NULLIF(dim_lot.description, ''), EXCLUDED.description),
    is_active = TRUE,
    updated_at = COALESCE(dim_lot.updated_at, now());

INSERT INTO dim_sous_lot_complet (sous_lot_id, lot_id, description)
SELECT
    source.sous_lot_id,
    MIN(source.lot_id) AS lot_id,
    MIN(source.description) AS description
FROM (
    SELECT
        COALESCE(NULLIF(TRIM(f.sous_lot_id), ''), NULLIF(TRIM(f.sous_lot), '')) AS sous_lot_id,
        COALESCE(NULLIF(TRIM(f.lot), ''), NULLIF(TRIM(f.lot_id::text), ''), 'NON_RENSEIGNE') AS lot_id,
        COALESCE(NULLIF(TRIM(f.sous_lot), ''), NULLIF(TRIM(f.sous_lot_id), ''), 'Non renseigne') AS description
    FROM fact_metre f
    WHERE COALESCE(NULLIF(TRIM(f.sous_lot_id), ''), NULLIF(TRIM(f.sous_lot), '')) IS NOT NULL
) source
GROUP BY source.sous_lot_id
ON CONFLICT (sous_lot_id) DO UPDATE SET
    lot_id = COALESCE(NULLIF(dim_sous_lot_complet.lot_id, ''), EXCLUDED.lot_id),
    description = COALESCE(NULLIF(dim_sous_lot_complet.description, ''), EXCLUDED.description),
    updated_at = now();

INSERT INTO dim_article_bpu (
    code_article,
    article_id,
    lot_id,
    sous_lot_id,
    designation,
    marque,
    unite,
    is_active
)
SELECT
    source.code_article,
    MIN(source.article_id) AS article_id,
    MIN(source.lot_id) AS lot_id,
    MIN(source.sous_lot_id) AS sous_lot_id,
    MIN(source.designation) AS designation,
    MIN(source.marque) AS marque,
    MIN(source.unite) AS unite,
    TRUE AS is_active
FROM (
    SELECT
        COALESCE(NULLIF(TRIM(f.code_article), ''), NULLIF(TRIM(f.article_id), '')) AS code_article,
        COALESCE(NULLIF(TRIM(f.article_id), ''), NULLIF(TRIM(f.code_article), '')) AS article_id,
        COALESCE(NULLIF(TRIM(f.lot), ''), NULLIF(TRIM(f.lot_id::text), ''), '') AS lot_id,
        COALESCE(NULLIF(TRIM(f.sous_lot_id), ''), NULLIF(TRIM(f.sous_lot), ''), '') AS sous_lot_id,
        COALESCE(NULLIF(TRIM(f.designation), ''), 'Article sans designation') AS designation,
        COALESCE(NULLIF(TRIM(f.marque), ''), '') AS marque,
        COALESCE(NULLIF(TRIM(f.unite), ''), '') AS unite
    FROM fact_metre f
    WHERE COALESCE(NULLIF(TRIM(f.code_article), ''), NULLIF(TRIM(f.article_id), '')) IS NOT NULL
) source
GROUP BY source.code_article
ON CONFLICT (code_article) DO UPDATE SET
    article_id = COALESCE(NULLIF(dim_article_bpu.article_id, ''), EXCLUDED.article_id),
    lot_id = COALESCE(NULLIF(dim_article_bpu.lot_id, ''), EXCLUDED.lot_id),
    sous_lot_id = COALESCE(NULLIF(dim_article_bpu.sous_lot_id, ''), EXCLUDED.sous_lot_id),
    designation = COALESCE(NULLIF(dim_article_bpu.designation, ''), EXCLUDED.designation),
    marque = COALESCE(NULLIF(dim_article_bpu.marque, ''), EXCLUDED.marque),
    unite = COALESCE(NULLIF(dim_article_bpu.unite, ''), EXCLUDED.unite),
    is_active = TRUE,
    updated_at = COALESCE(dim_article_bpu.updated_at, now());

-- 5. Vues actives Power BI.
DROP VIEW IF EXISTS vw_dim_article_bpu_active CASCADE;
DROP VIEW IF EXISTS vw_dim_sous_lot_active CASCADE;
DROP VIEW IF EXISTS vw_dim_lot_active CASCADE;

CREATE OR REPLACE VIEW vw_dim_lot_active AS
SELECT d.*
FROM dim_lot d
WHERE EXISTS (
    SELECT 1
    FROM fact_metre f
    WHERE UPPER(TRIM(COALESCE(f.lot, ''))) = UPPER(TRIM(COALESCE(d.lot, '')))
);

CREATE OR REPLACE VIEW vw_dim_sous_lot_active AS
SELECT d.*
FROM dim_sous_lot_complet d
WHERE EXISTS (
    SELECT 1
    FROM fact_metre f
    WHERE UPPER(TRIM(COALESCE(f.sous_lot_id, ''))) = UPPER(TRIM(COALESCE(d.sous_lot_id, '')))
       OR UPPER(TRIM(COALESCE(f.sous_lot, ''))) = UPPER(TRIM(COALESCE(d.sous_lot_id, '')))
);

CREATE OR REPLACE VIEW vw_dim_article_bpu_active AS
SELECT d.*
FROM dim_article_bpu d
WHERE EXISTS (
    SELECT 1
    FROM fact_metre f
    WHERE UPPER(TRIM(COALESCE(f.code_article, ''))) = UPPER(TRIM(COALESCE(d.code_article, '')))
       OR UPPER(TRIM(COALESCE(f.article_id, ''))) = UPPER(TRIM(COALESCE(d.code_article, '')))
       OR UPPER(TRIM(COALESCE(f.article_id, ''))) = UPPER(TRIM(COALESCE(d.article_id, '')))
);

-- 6. Index utiles au refresh Power BI.
CREATE INDEX IF NOT EXISTS ix_fact_metre_lot_active
    ON fact_metre (lot);

CREATE INDEX IF NOT EXISTS ix_fact_metre_sous_lot_active
    ON fact_metre (sous_lot_id);

CREATE INDEX IF NOT EXISTS ix_fact_metre_code_article_active
    ON fact_metre (code_article);

CREATE INDEX IF NOT EXISTS ix_dim_article_bpu_article_id
    ON dim_article_bpu (article_id);

COMMIT;

-- 7. Controle post-migration.
SELECT 'vw_dim_lot_active' AS view_name, COUNT(*) AS rows_count FROM vw_dim_lot_active
UNION ALL SELECT 'vw_dim_sous_lot_active', COUNT(*) FROM vw_dim_sous_lot_active
UNION ALL SELECT 'vw_dim_article_bpu_active', COUNT(*) FROM vw_dim_article_bpu_active;
