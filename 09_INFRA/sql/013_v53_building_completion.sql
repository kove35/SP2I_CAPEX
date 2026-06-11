-- SP2I CAPEX - V5.3 Building Completion
-- Migration: 013_v53_building_completion.sql
--
-- Objectif:
-- - completer la couverture BAT_01 au-dessus de V5.2.1 et V5.2.2 ;
-- - ajouter les lots GO, MAC, TOIT, FACADE, MENU_EXT, MENU_INT, ASC,
--   INCENDIE, SECURITE et VRD ;
-- - exposer des vues Power BI additives ;
-- - ne modifier aucun objet historique SP2I.
--
-- Compatibilite:
-- - PostgreSQL 18
-- - Neon PostgreSQL
-- - Power BI DirectQuery
--
-- Garanties:
-- - aucune ecriture dans fact_metre, fact_simulation, fact_approvals ou procurement_decisions ;
-- - aucun endpoint backend/frontend modifie ;
-- - aucun rapport Power BI existant modifie ;
-- - migration additive et idempotente.

BEGIN;

-- ============================================================================
-- 1. DIMENSIONS COMPLEMENTAIRES
-- ============================================================================

CREATE TABLE IF NOT EXISTS dim_go_component (
    component_id BIGSERIAL PRIMARY KEY,
    component_code VARCHAR(120) NOT NULL UNIQUE,
    designation VARCHAR(255) NOT NULL,
    unit VARCHAR(40) NOT NULL,
    scope_rule VARCHAR(255) NOT NULL DEFAULT 'N3 uniquement',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dim_maconnerie_component (
    component_id BIGSERIAL PRIMARY KEY,
    component_code VARCHAR(120) NOT NULL UNIQUE,
    designation VARCHAR(255) NOT NULL,
    unit VARCHAR(40) NOT NULL,
    scope_rule VARCHAR(255) NOT NULL DEFAULT 'Surfaces de murs',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dim_toiture_component (
    component_id BIGSERIAL PRIMARY KEY,
    component_code VARCHAR(120) NOT NULL UNIQUE,
    designation VARCHAR(255) NOT NULL,
    unit VARCHAR(40) NOT NULL,
    scope_rule VARCHAR(255) NOT NULL DEFAULT 'Surface toiture terrasse',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO dim_go_component (component_code, designation, unit, scope_rule)
VALUES
    ('POTEAU_BA_20X20', 'Poteau beton arme 20x20', 'ML', 'N3 uniquement'),
    ('POUTRE_BA_20X40', 'Poutre beton arme 20x40', 'ML', 'N3 uniquement'),
    ('DALLE_BA_15CM', 'Dalle beton arme 15 cm', 'M2', 'N3 uniquement'),
    ('BETON_C25', 'Beton C25/30', 'M3', 'N3 uniquement'),
    ('ACIER_HA8', 'Acier HA8', 'KG', 'N3 uniquement'),
    ('ACIER_HA10', 'Acier HA10', 'KG', 'N3 uniquement'),
    ('ACIER_HA12', 'Acier HA12', 'KG', 'N3 uniquement'),
    ('ACIER_HA14', 'Acier HA14', 'KG', 'N3 uniquement'),
    ('ACIER_HA16', 'Acier HA16', 'KG', 'N3 uniquement'),
    ('COFFRAGE', 'Coffrage beton arme', 'M2', 'N3 uniquement')
ON CONFLICT (component_code) DO NOTHING;

INSERT INTO dim_maconnerie_component (component_code, designation, unit, scope_rule)
VALUES
    ('BLOC_15', 'Bloc creux 15 cm', 'M2', 'Cloisons interieures'),
    ('BLOC_20', 'Bloc creux 20 cm', 'M2', 'Murs exterieurs'),
    ('MORTIER', 'Mortier de pose', 'M3', 'Surfaces de murs'),
    ('CHAINAGE', 'Chainage horizontal et vertical', 'ML', 'Surfaces de murs'),
    ('ENDUIT_INTERIEUR', 'Enduit interieur', 'M2', 'Faces interieures'),
    ('ENDUIT_EXTERIEUR', 'Enduit exterieur', 'M2', 'Faces exterieures')
ON CONFLICT (component_code) DO NOTHING;

INSERT INTO dim_toiture_component (component_code, designation, unit, scope_rule)
VALUES
    ('FORME_PENTE', 'Forme de pente toiture terrasse', 'M2', 'Surface toiture'),
    ('PRIMAIRE', 'Primaire etancheite', 'M2', 'Surface toiture'),
    ('MEMBRANE_BICOUCHE', 'Membrane etancheite bicouche', 'M2', 'Surface toiture'),
    ('RELEVES', 'Releves etancheite', 'ML', 'Acroteres'),
    ('PROTECTION_LOURDE', 'Protection lourde terrasse accessible', 'M2', 'Surface toiture'),
    ('ISOLATION_XPS', 'Isolation XPS toiture terrasse', 'M2', 'Surface toiture'),
    ('NAISSANCE_EP', 'Naissance eaux pluviales', 'U', 'Points EP'),
    ('DESCENTE_EP', 'Descente eaux pluviales', 'ML', 'Facade')
ON CONFLICT (component_code) DO NOTHING;

-- ============================================================================
-- 2. TABLES DE GENERATION PAR LOT
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_generation_go (
    generation_id BIGSERIAL PRIMARY KEY,
    generation_batch VARCHAR(120) NOT NULL DEFAULT 'BAT_01_V53',
    niveau VARCHAR(80) NOT NULL DEFAULT 'N3',
    component_code VARCHAR(120) NOT NULL REFERENCES dim_go_component(component_code),
    designation VARCHAR(255) NOT NULL,
    lot_code VARCHAR(120) NOT NULL DEFAULT 'LOT_GO',
    quantity NUMERIC(16, 4) NOT NULL DEFAULT 0,
    unit VARCHAR(40) NOT NULL,
    dqe_line_count INTEGER NOT NULL DEFAULT 1,
    scope_note VARCHAR(255) NOT NULL DEFAULT 'N3 a construire',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fact_generation_go UNIQUE (generation_batch, niveau, component_code),
    CONSTRAINT ck_fact_generation_go_lines CHECK (dqe_line_count >= 1)
);

CREATE TABLE IF NOT EXISTS fact_generation_maconnerie (
    generation_id BIGSERIAL PRIMARY KEY,
    generation_batch VARCHAR(120) NOT NULL DEFAULT 'BAT_01_V53',
    component_code VARCHAR(120) NOT NULL REFERENCES dim_maconnerie_component(component_code),
    designation VARCHAR(255) NOT NULL,
    lot_code VARCHAR(120) NOT NULL DEFAULT 'LOT_MAC',
    quantity NUMERIC(16, 4) NOT NULL DEFAULT 0,
    unit VARCHAR(40) NOT NULL,
    dqe_line_count INTEGER NOT NULL DEFAULT 1,
    scope_note VARCHAR(255) NOT NULL DEFAULT 'Surfaces de murs BAT_01',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fact_generation_maconnerie UNIQUE (generation_batch, component_code),
    CONSTRAINT ck_fact_generation_maconnerie_lines CHECK (dqe_line_count >= 1)
);

CREATE TABLE IF NOT EXISTS fact_generation_toiture (
    generation_id BIGSERIAL PRIMARY KEY,
    generation_batch VARCHAR(120) NOT NULL DEFAULT 'BAT_01_V53',
    component_code VARCHAR(120) NOT NULL REFERENCES dim_toiture_component(component_code),
    designation VARCHAR(255) NOT NULL,
    lot_code VARCHAR(120) NOT NULL DEFAULT 'LOT_TOIT',
    quantity NUMERIC(16, 4) NOT NULL DEFAULT 0,
    unit VARCHAR(40) NOT NULL,
    dqe_line_count INTEGER NOT NULL DEFAULT 1,
    scope_note VARCHAR(255) NOT NULL DEFAULT 'Toiture terrasse beton accessible',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fact_generation_toiture UNIQUE (generation_batch, component_code),
    CONSTRAINT ck_fact_generation_toiture_lines CHECK (dqe_line_count >= 1)
);

CREATE TABLE IF NOT EXISTS fact_generation_facade (
    generation_id BIGSERIAL PRIMARY KEY,
    generation_batch VARCHAR(120) NOT NULL DEFAULT 'BAT_01_V53',
    component_code VARCHAR(120) NOT NULL,
    designation VARCHAR(255) NOT NULL,
    lot_code VARCHAR(120) NOT NULL DEFAULT 'LOT_FACADE',
    quantity NUMERIC(16, 4) NOT NULL DEFAULT 0,
    unit VARCHAR(40) NOT NULL,
    dqe_line_count INTEGER NOT NULL DEFAULT 1,
    scope_note VARCHAR(255) NOT NULL DEFAULT 'Facades exterieures BAT_01',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fact_generation_facade UNIQUE (generation_batch, component_code),
    CONSTRAINT ck_fact_generation_facade_lines CHECK (dqe_line_count >= 1)
);

CREATE TABLE IF NOT EXISTS fact_generation_menu_ext (
    generation_id BIGSERIAL PRIMARY KEY,
    generation_batch VARCHAR(120) NOT NULL DEFAULT 'BAT_01_V53',
    component_code VARCHAR(120) NOT NULL,
    designation VARCHAR(255) NOT NULL,
    lot_code VARCHAR(120) NOT NULL DEFAULT 'LOT_MENU_EXT',
    quantity NUMERIC(16, 4) NOT NULL DEFAULT 0,
    unit VARCHAR(40) NOT NULL,
    dqe_line_count INTEGER NOT NULL DEFAULT 1,
    scope_note VARCHAR(255) NOT NULL DEFAULT 'Ouvertures exterieures',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fact_generation_menu_ext UNIQUE (generation_batch, component_code),
    CONSTRAINT ck_fact_generation_menu_ext_lines CHECK (dqe_line_count >= 1)
);

CREATE TABLE IF NOT EXISTS fact_generation_menu_int (
    generation_id BIGSERIAL PRIMARY KEY,
    generation_batch VARCHAR(120) NOT NULL DEFAULT 'BAT_01_V53',
    component_code VARCHAR(120) NOT NULL,
    designation VARCHAR(255) NOT NULL,
    lot_code VARCHAR(120) NOT NULL DEFAULT 'LOT_MENU_INT',
    quantity NUMERIC(16, 4) NOT NULL DEFAULT 0,
    unit VARCHAR(40) NOT NULL,
    dqe_line_count INTEGER NOT NULL DEFAULT 1,
    scope_note VARCHAR(255) NOT NULL DEFAULT 'Pieces appartements',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fact_generation_menu_int UNIQUE (generation_batch, component_code),
    CONSTRAINT ck_fact_generation_menu_int_lines CHECK (dqe_line_count >= 1)
);

CREATE TABLE IF NOT EXISTS fact_generation_ascenseur (
    generation_id BIGSERIAL PRIMARY KEY,
    generation_batch VARCHAR(120) NOT NULL DEFAULT 'BAT_01_V53',
    component_code VARCHAR(120) NOT NULL,
    designation VARCHAR(255) NOT NULL,
    lot_code VARCHAR(120) NOT NULL DEFAULT 'LOT_ASC',
    quantity NUMERIC(16, 4) NOT NULL DEFAULT 0,
    unit VARCHAR(40) NOT NULL,
    dqe_line_count INTEGER NOT NULL DEFAULT 1,
    scope_note VARCHAR(255) NOT NULL DEFAULT '1 ascenseur BAT_01',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fact_generation_ascenseur UNIQUE (generation_batch, component_code),
    CONSTRAINT ck_fact_generation_ascenseur_lines CHECK (dqe_line_count >= 1)
);

CREATE TABLE IF NOT EXISTS fact_generation_incendie (
    generation_id BIGSERIAL PRIMARY KEY,
    generation_batch VARCHAR(120) NOT NULL DEFAULT 'BAT_01_V53',
    component_code VARCHAR(120) NOT NULL,
    designation VARCHAR(255) NOT NULL,
    lot_code VARCHAR(120) NOT NULL DEFAULT 'LOT_INCENDIE',
    quantity NUMERIC(16, 4) NOT NULL DEFAULT 0,
    unit VARCHAR(40) NOT NULL,
    dqe_line_count INTEGER NOT NULL DEFAULT 1,
    scope_note VARCHAR(255) NOT NULL DEFAULT 'Par niveau et surface',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fact_generation_incendie UNIQUE (generation_batch, component_code),
    CONSTRAINT ck_fact_generation_incendie_lines CHECK (dqe_line_count >= 1)
);

CREATE TABLE IF NOT EXISTS fact_generation_securite (
    generation_id BIGSERIAL PRIMARY KEY,
    generation_batch VARCHAR(120) NOT NULL DEFAULT 'BAT_01_V53',
    component_code VARCHAR(120) NOT NULL,
    designation VARCHAR(255) NOT NULL,
    lot_code VARCHAR(120) NOT NULL DEFAULT 'LOT_SECURITE',
    quantity NUMERIC(16, 4) NOT NULL DEFAULT 0,
    unit VARCHAR(40) NOT NULL,
    dqe_line_count INTEGER NOT NULL DEFAULT 1,
    scope_note VARCHAR(255) NOT NULL DEFAULT 'Par niveau et acces',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fact_generation_securite UNIQUE (generation_batch, component_code),
    CONSTRAINT ck_fact_generation_securite_lines CHECK (dqe_line_count >= 1)
);

CREATE TABLE IF NOT EXISTS fact_generation_vrd (
    generation_id BIGSERIAL PRIMARY KEY,
    generation_batch VARCHAR(120) NOT NULL DEFAULT 'BAT_01_V53',
    component_code VARCHAR(120) NOT NULL,
    designation VARCHAR(255) NOT NULL,
    lot_code VARCHAR(120) NOT NULL DEFAULT 'LOT_VRD',
    quantity NUMERIC(16, 4) NOT NULL DEFAULT 0,
    unit VARCHAR(40) NOT NULL,
    dqe_line_count INTEGER NOT NULL DEFAULT 1,
    scope_note VARCHAR(255) NOT NULL DEFAULT 'Perimetre et raccordements BAT_01',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fact_generation_vrd UNIQUE (generation_batch, component_code),
    CONSTRAINT ck_fact_generation_vrd_lines CHECK (dqe_line_count >= 1)
);

-- ============================================================================
-- 3. SEEDS BAT_01
-- ============================================================================

INSERT INTO fact_generation_go (component_code, designation, quantity, unit, dqe_line_count)
SELECT component_code, designation, quantity, unit, dqe_line_count
FROM (
    VALUES
        ('POTEAU_BA_20X20', 'Poteau beton arme 20x20 N3', 108::NUMERIC, 'ML', 35),
        ('POUTRE_BA_20X40', 'Poutre beton arme 20x40 N3', 156::NUMERIC, 'ML', 35),
        ('DALLE_BA_15CM', 'Dalle beton arme 15 cm N3', 421.30::NUMERIC, 'M2', 35),
        ('BETON_C25', 'Beton C25/30 N3', 78::NUMERIC, 'M3', 35),
        ('ACIER_HA8', 'Acier HA8 N3', 1600::NUMERIC, 'KG', 35),
        ('ACIER_HA10', 'Acier HA10 N3', 2100::NUMERIC, 'KG', 35),
        ('ACIER_HA12', 'Acier HA12 N3', 2600::NUMERIC, 'KG', 35),
        ('ACIER_HA14', 'Acier HA14 N3', 1800::NUMERIC, 'KG', 35),
        ('ACIER_HA16', 'Acier HA16 N3', 1250::NUMERIC, 'KG', 35),
        ('COFFRAGE', 'Coffrage beton arme N3', 980::NUMERIC, 'M2', 35)
) AS seed(component_code, designation, quantity, unit, dqe_line_count)
ON CONFLICT (generation_batch, niveau, component_code) DO NOTHING;

INSERT INTO fact_generation_maconnerie (component_code, designation, quantity, unit, dqe_line_count)
SELECT component_code, designation, quantity, unit, dqe_line_count
FROM (
    VALUES
        ('BLOC_15', 'Bloc 15 cloisons interieures', 1450::NUMERIC, 'M2', 60),
        ('BLOC_20', 'Bloc 20 murs exterieurs', 980::NUMERIC, 'M2', 60),
        ('MORTIER', 'Mortier de pose maconnerie', 95::NUMERIC, 'M3', 60),
        ('CHAINAGE', 'Chainage maconnerie', 840::NUMERIC, 'ML', 60),
        ('ENDUIT_INTERIEUR', 'Enduit interieur', 2900::NUMERIC, 'M2', 60),
        ('ENDUIT_EXTERIEUR', 'Enduit exterieur', 1350::NUMERIC, 'M2', 60)
) AS seed(component_code, designation, quantity, unit, dqe_line_count)
ON CONFLICT (generation_batch, component_code) DO NOTHING;

INSERT INTO fact_generation_toiture (component_code, designation, quantity, unit, dqe_line_count)
SELECT component_code, designation, quantity, unit, dqe_line_count
FROM (
    VALUES
        ('FORME_PENTE', 'Forme de pente toiture terrasse', 421.30::NUMERIC, 'M2', 35),
        ('PRIMAIRE', 'Primaire etancheite toiture', 421.30::NUMERIC, 'M2', 35),
        ('MEMBRANE_BICOUCHE', 'Membrane bicouche toiture', 421.30::NUMERIC, 'M2', 35),
        ('RELEVES', 'Releves etancheite acroteres', 185::NUMERIC, 'ML', 35),
        ('PROTECTION_LOURDE', 'Protection lourde accessible', 421.30::NUMERIC, 'M2', 35),
        ('ISOLATION_XPS', 'Isolation XPS toiture', 421.30::NUMERIC, 'M2', 35),
        ('NAISSANCE_EP', 'Naissances eaux pluviales', 8::NUMERIC, 'U', 35),
        ('DESCENTE_EP', 'Descentes eaux pluviales', 96::NUMERIC, 'ML', 35)
) AS seed(component_code, designation, quantity, unit, dqe_line_count)
ON CONFLICT (generation_batch, component_code) DO NOTHING;

INSERT INTO fact_generation_facade (component_code, designation, quantity, unit, dqe_line_count)
VALUES
    ('LAINE_ROCHE_100', 'ITE laine de roche 100 mm', 1350::NUMERIC, 'M2', 40),
    ('CHEVILLES', 'Chevilles ITE', 8100::NUMERIC, 'U', 40),
    ('OSSATURE_ALU', 'Ossature aluminium facade', 1350::NUMERIC, 'M2', 40),
    ('ALUCOBOND', 'Panneaux Alucobond', 1350::NUMERIC, 'M2', 40),
    ('COUVERTINES', 'Couvertines aluminium', 185::NUMERIC, 'ML', 40),
    ('BAVETTES', 'Bavettes aluminium', 145::NUMERIC, 'ML', 40),
    ('HABILLAGES', 'Habillages et finitions facade', 1::NUMERIC, 'ENS', 40)
ON CONFLICT (generation_batch, component_code) DO NOTHING;

INSERT INTO fact_generation_menu_ext (component_code, designation, quantity, unit, dqe_line_count)
VALUES
    ('FENETRE_ALU', 'Fenetres aluminium', 54::NUMERIC, 'U', 35),
    ('BAIE_COULISSANTE', 'Baies coulissantes aluminium', 18::NUMERIC, 'U', 35),
    ('PORTE_EXTERIEURE', 'Portes exterieures', 8::NUMERIC, 'U', 35),
    ('VITRAGE', 'Vitrage securit', 520::NUMERIC, 'M2', 35),
    ('QUINCAILLERIE', 'Quincaillerie menuiseries exterieures', 1::NUMERIC, 'ENS', 35)
ON CONFLICT (generation_batch, component_code) DO NOTHING;

INSERT INTO fact_generation_menu_int (component_code, designation, quantity, unit, dqe_line_count)
VALUES
    ('PORTE_CHAMBRE', 'Portes chambres', 18::NUMERIC, 'U', 35),
    ('PORTE_SDB', 'Portes salles de bain', 18::NUMERIC, 'U', 35),
    ('PORTE_TECHNIQUE', 'Portes techniques', 8::NUMERIC, 'U', 35),
    ('DRESSING', 'Amenagements dressing', 6::NUMERIC, 'ENS', 35)
ON CONFLICT (generation_batch, component_code) DO NOTHING;

INSERT INTO fact_generation_ascenseur (component_code, designation, quantity, unit, dqe_line_count)
VALUES
    ('CABINE', 'Cabine ascenseur 8 personnes', 1::NUMERIC, 'U', 30),
    ('PORTE_PALIERE', 'Portes palieres ascenseur', 4::NUMERIC, 'U', 30),
    ('GUIDAGE', 'Guidage ascenseur', 1::NUMERIC, 'ENS', 30),
    ('MOTEUR', 'Moteur ascenseur', 1::NUMERIC, 'U', 30),
    ('ARMOIRE_COMMANDE', 'Armoire de commande ascenseur', 1::NUMERIC, 'U', 30),
    ('TELEALARME', 'Telealarme ascenseur', 1::NUMERIC, 'U', 30),
    ('ESSAIS', 'Essais et mise en service ascenseur', 1::NUMERIC, 'ENS', 30)
ON CONFLICT (generation_batch, component_code) DO NOTHING;

INSERT INTO fact_generation_incendie (component_code, designation, quantity, unit, dqe_line_count)
VALUES
    ('DETECTEUR', 'Detecteurs incendie', 48::NUMERIC, 'U', 35),
    ('BAES', 'Blocs autonomes eclairage securite', 24::NUMERIC, 'U', 35),
    ('EXTINCTEUR', 'Extincteurs', 18::NUMERIC, 'U', 35),
    ('RIA', 'Robinets incendie armes', 4::NUMERIC, 'U', 35),
    ('SIGNALISATION', 'Signalisation incendie', 1::NUMERIC, 'ENS', 35),
    ('CMSI', 'Centralisateur mise en securite incendie', 1::NUMERIC, 'U', 35)
ON CONFLICT (generation_batch, component_code) DO NOTHING;

INSERT INTO fact_generation_securite (component_code, designation, quantity, unit, dqe_line_count)
VALUES
    ('CAMERA_IP', 'Cameras IP', 24::NUMERIC, 'U', 35),
    ('NVR', 'Enregistreur video NVR', 1::NUMERIC, 'U', 35),
    ('CONTROLE_ACCES', 'Controle acces', 8::NUMERIC, 'U', 35),
    ('INTERPHONE', 'Interphonie immeuble', 1::NUMERIC, 'ENS', 35),
    ('DETECTION_INTRUSION', 'Detection intrusion parties communes', 1::NUMERIC, 'ENS', 35)
ON CONFLICT (generation_batch, component_code) DO NOTHING;

INSERT INTO fact_generation_vrd (component_code, designation, quantity, unit, dqe_line_count)
VALUES
    ('REGARD', 'Regards reseaux exterieurs', 18::NUMERIC, 'U', 35),
    ('CANIVEAU', 'Caniveaux exterieurs', 95::NUMERIC, 'ML', 35),
    ('RESEAU_EP', 'Reseau eaux pluviales exterieur', 180::NUMERIC, 'ML', 35),
    ('RESEAU_EU', 'Reseau eaux usees exterieur', 160::NUMERIC, 'ML', 35),
    ('VOIRIE', 'Voirie et acces', 650::NUMERIC, 'M2', 35),
    ('ECLAIRAGE_EXTERIEUR', 'Eclairage exterieur VRD', 18::NUMERIC, 'U', 35)
ON CONFLICT (generation_batch, component_code) DO NOTHING;

-- ============================================================================
-- 4. VUES POWER BI ADDITIVES
-- ============================================================================

CREATE OR REPLACE VIEW vw_sp2i_generated_building AS
SELECT
    source_table,
    generation_batch,
    lot_code,
    component_code,
    designation,
    quantity,
    unit,
    component_index,
    component_code || '_DQE_' || LPAD(component_index::TEXT, 3, '0') AS generated_article_code,
    designation || ' - ligne DQE ' || component_index::TEXT AS generated_designation,
    scope_note,
    created_at
FROM (
    SELECT 'fact_generation_go' AS source_table, generation_batch, lot_code, component_code, designation, quantity, unit, scope_note, created_at, dqe_line_count
    FROM fact_generation_go
    UNION ALL
    SELECT 'fact_generation_maconnerie', generation_batch, lot_code, component_code, designation, quantity, unit, scope_note, created_at, dqe_line_count
    FROM fact_generation_maconnerie
    UNION ALL
    SELECT 'fact_generation_toiture', generation_batch, lot_code, component_code, designation, quantity, unit, scope_note, created_at, dqe_line_count
    FROM fact_generation_toiture
    UNION ALL
    SELECT 'fact_generation_vrd', generation_batch, lot_code, component_code, designation, quantity, unit, scope_note, created_at, dqe_line_count
    FROM fact_generation_vrd
    WHERE is_active
) src
CROSS JOIN LATERAL generate_series(1, src.dqe_line_count) AS gs(component_index);

CREATE OR REPLACE VIEW vw_sp2i_generated_envelope AS
SELECT
    source_table,
    generation_batch,
    lot_code,
    component_code,
    designation,
    quantity,
    unit,
    component_index,
    component_code || '_DQE_' || LPAD(component_index::TEXT, 3, '0') AS generated_article_code,
    designation || ' - ligne DQE ' || component_index::TEXT AS generated_designation,
    scope_note,
    created_at
FROM (
    SELECT 'fact_generation_toiture' AS source_table, generation_batch, lot_code, component_code, designation, quantity, unit, scope_note, created_at, dqe_line_count
    FROM fact_generation_toiture
    UNION ALL
    SELECT 'fact_generation_facade', generation_batch, lot_code, component_code, designation, quantity, unit, scope_note, created_at, dqe_line_count
    FROM fact_generation_facade
    WHERE is_active
    UNION ALL
    SELECT 'fact_generation_menu_ext', generation_batch, lot_code, component_code, designation, quantity, unit, scope_note, created_at, dqe_line_count
    FROM fact_generation_menu_ext
    WHERE is_active
    UNION ALL
    SELECT 'fact_generation_menu_int', generation_batch, lot_code, component_code, designation, quantity, unit, scope_note, created_at, dqe_line_count
    FROM fact_generation_menu_int
    WHERE is_active
) src
CROSS JOIN LATERAL generate_series(1, src.dqe_line_count) AS gs(component_index);

CREATE OR REPLACE VIEW vw_sp2i_generated_special_systems AS
SELECT
    source_table,
    generation_batch,
    lot_code,
    component_code,
    designation,
    quantity,
    unit,
    component_index,
    component_code || '_DQE_' || LPAD(component_index::TEXT, 3, '0') AS generated_article_code,
    designation || ' - ligne DQE ' || component_index::TEXT AS generated_designation,
    scope_note,
    created_at
FROM (
    SELECT 'fact_generation_ascenseur' AS source_table, generation_batch, lot_code, component_code, designation, quantity, unit, scope_note, created_at, dqe_line_count
    FROM fact_generation_ascenseur
    WHERE is_active
    UNION ALL
    SELECT 'fact_generation_incendie', generation_batch, lot_code, component_code, designation, quantity, unit, scope_note, created_at, dqe_line_count
    FROM fact_generation_incendie
    WHERE is_active
    UNION ALL
    SELECT 'fact_generation_securite', generation_batch, lot_code, component_code, designation, quantity, unit, scope_note, created_at, dqe_line_count
    FROM fact_generation_securite
    WHERE is_active
    UNION ALL
    SELECT 'fact_generation_vrd', generation_batch, lot_code, component_code, designation, quantity, unit, scope_note, created_at, dqe_line_count
    FROM fact_generation_vrd
    WHERE is_active
) src
CROSS JOIN LATERAL generate_series(1, src.dqe_line_count) AS gs(component_index);

-- ============================================================================
-- 5. INDEX
-- ============================================================================

CREATE INDEX IF NOT EXISTS ix_fact_generation_go_scope
    ON fact_generation_go (generation_batch, lot_code, component_code);

CREATE INDEX IF NOT EXISTS ix_fact_generation_maconnerie_scope
    ON fact_generation_maconnerie (generation_batch, lot_code, component_code);

CREATE INDEX IF NOT EXISTS ix_fact_generation_toiture_scope
    ON fact_generation_toiture (generation_batch, lot_code, component_code);

CREATE INDEX IF NOT EXISTS ix_fact_generation_facade_scope
    ON fact_generation_facade (generation_batch, lot_code, component_code)
    WHERE is_active;

CREATE INDEX IF NOT EXISTS ix_fact_generation_menu_ext_scope
    ON fact_generation_menu_ext (generation_batch, lot_code, component_code)
    WHERE is_active;

CREATE INDEX IF NOT EXISTS ix_fact_generation_menu_int_scope
    ON fact_generation_menu_int (generation_batch, lot_code, component_code)
    WHERE is_active;

CREATE INDEX IF NOT EXISTS ix_fact_generation_ascenseur_scope
    ON fact_generation_ascenseur (generation_batch, lot_code, component_code)
    WHERE is_active;

CREATE INDEX IF NOT EXISTS ix_fact_generation_incendie_scope
    ON fact_generation_incendie (generation_batch, lot_code, component_code)
    WHERE is_active;

CREATE INDEX IF NOT EXISTS ix_fact_generation_securite_scope
    ON fact_generation_securite (generation_batch, lot_code, component_code)
    WHERE is_active;

CREATE INDEX IF NOT EXISTS ix_fact_generation_vrd_scope
    ON fact_generation_vrd (generation_batch, lot_code, component_code)
    WHERE is_active;

COMMIT;

-- ============================================================================
-- 6. VALIDATION POST-MIGRATION
-- ============================================================================
-- Ces requetes sont read-only et peuvent etre executees apres la migration.

WITH v53_lines AS (
    SELECT lot_code FROM vw_sp2i_generated_building
    UNION ALL
    SELECT lot_code FROM vw_sp2i_generated_envelope
    WHERE lot_code NOT IN ('LOT_TOIT')
    UNION ALL
    SELECT lot_code FROM vw_sp2i_generated_special_systems
    WHERE lot_code NOT IN ('LOT_VRD')
)
SELECT
    COUNT(*) AS nb_lignes_v53,
    2002 + COUNT(*) AS nb_lignes_total_theorique,
    CASE
        WHEN 2002 + COUNT(*) BETWEEN 3200 AND 4500 THEN 'OK'
        ELSE 'CHECK_VOLUME'
    END AS volume_status
FROM v53_lines;

WITH v53_lines AS (
    SELECT lot_code FROM vw_sp2i_generated_building
    UNION ALL
    SELECT lot_code FROM vw_sp2i_generated_envelope
    WHERE lot_code NOT IN ('LOT_TOIT')
    UNION ALL
    SELECT lot_code FROM vw_sp2i_generated_special_systems
    WHERE lot_code NOT IN ('LOT_VRD')
)
SELECT lot_code, COUNT(*) AS nb_lignes_dqe
FROM v53_lines
GROUP BY lot_code
ORDER BY lot_code;
