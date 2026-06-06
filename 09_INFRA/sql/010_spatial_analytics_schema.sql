-- SP2I CAPEX - Spatial analytics dimensions
-- Idempotent schema for building and zone analytics without IFC/Revit dependency.

CREATE TABLE IF NOT EXISTS dim_batiment (
    batiment_id BIGSERIAL PRIMARY KEY,
    batiment VARCHAR(150) NOT NULL UNIQUE,
    type_batiment VARCHAR(100) DEFAULT 'RESIDENTIEL'
);

ALTER TABLE dim_batiment
    ADD COLUMN IF NOT EXISTS batiment_code VARCHAR(150),
    ADD COLUMN IF NOT EXISTS nom VARCHAR(255),
    ADD COLUMN IF NOT EXISTS nb_niveaux INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS nb_appartements INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS surface_totale_m2 DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS description VARCHAR(255) DEFAULT '',
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

CREATE TABLE IF NOT EXISTS dim_zone (
    zone_id BIGSERIAL PRIMARY KEY,
    zone_code VARCHAR(180) NOT NULL UNIQUE,
    type_zone VARCHAR(100) DEFAULT ''
);

ALTER TABLE dim_zone
    ADD COLUMN IF NOT EXISTS zone_nom VARCHAR(180),
    ADD COLUMN IF NOT EXISTS batiment VARCHAR(150) DEFAULT '',
    ADD COLUMN IF NOT EXISTS niveau VARCHAR(100) DEFAULT '',
    ADD COLUMN IF NOT EXISTS appart VARCHAR(150) DEFAULT '',
    ADD COLUMN IF NOT EXISTS piece VARCHAR(150) DEFAULT '',
    ADD COLUMN IF NOT EXISTS description VARCHAR(255) DEFAULT '',
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

INSERT INTO dim_batiment (
    batiment,
    batiment_code,
    nom,
    nb_niveaux,
    nb_appartements,
    surface_totale_m2,
    type_batiment,
    description,
    is_active
)
VALUES (
    'BATIMENT_01',
    'BATIMENT_01',
    'Batiment 01',
    3,
    6,
    1263.90,
    'RESIDENTIEL',
    'Batiment residentiel initial SP2I',
    TRUE
)
ON CONFLICT (batiment) DO UPDATE SET
    batiment_code = EXCLUDED.batiment_code,
    nom = EXCLUDED.nom,
    nb_niveaux = EXCLUDED.nb_niveaux,
    nb_appartements = EXCLUDED.nb_appartements,
    surface_totale_m2 = EXCLUDED.surface_totale_m2,
    type_batiment = EXCLUDED.type_batiment,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active,
    updated_at = now();

UPDATE dim_batiment
SET
    batiment_code = COALESCE(NULLIF(batiment_code, ''), batiment),
    nom = COALESCE(NULLIF(nom, ''), batiment),
    updated_at = now();

INSERT INTO dim_zone (zone_code, zone_nom, type_zone, description, is_active)
VALUES
    ('ZONE_JOUR', 'Jour', 'JOUR', 'Pieces de vie: sejour, salon, cuisine', TRUE),
    ('ZONE_NUIT', 'Nuit', 'NUIT', 'Chambres et dressing', TRUE),
    ('ZONE_SANITAIRE', 'Sanitaire', 'SANITAIRE', 'SDE, SDB et WC', TRUE),
    ('ZONE_CIRCULATION', 'Circulation', 'CIRCULATION', 'Couloirs, escaliers et circulations', TRUE),
    ('ZONE_EXTERIEURE', 'Exterieure', 'EXTERIEUR', 'Balcons, terrasses et surfaces exterieures', TRUE),
    ('ZONE_TECHNIQUE', 'Technique', 'TECHNIQUE', 'Locaux techniques et pieces non classees', TRUE)
ON CONFLICT (zone_code) DO UPDATE SET
    zone_nom = EXCLUDED.zone_nom,
    type_zone = EXCLUDED.type_zone,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active,
    updated_at = now();

CREATE INDEX IF NOT EXISTS ix_dim_batiment_code
    ON dim_batiment (batiment_code);

CREATE INDEX IF NOT EXISTS ix_dim_zone_code
    ON dim_zone (zone_code);

CREATE INDEX IF NOT EXISTS ix_dim_zone_type
    ON dim_zone (type_zone);

-- Install/update the reporting views with:
-- psql "$DATABASE_URL" -f sql/powerbi/001_powerbi_views.sql
