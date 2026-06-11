-- SP2I CAPEX - BPU V5.3 18 lots
-- Migration: 016_dim_bpu_v53.sql
--
-- Objectif:
-- - creer le referentiel prix cible dim_bpu_v53 ;
-- - initialiser 1 ligne par article genere depuis vw_sp2i_generated_dqe_master ;
-- - laisser les prix a 0 avant enrichissement Pointe-Noire / Chine ;
-- - ne pas modifier fact_metre, fact_simulation, fact_approvals ou procurement_decisions.
--
-- Preconditions:
-- - 015_v53_dqe_master_view.sql appliquee ;
-- - vw_sp2i_generated_dqe_master disponible avec 4734 lignes, 2524 articles uniques et 18 lots.

BEGIN;

CREATE TABLE IF NOT EXISTS dim_bpu_v53 (
    article_code VARCHAR(255) PRIMARY KEY,
    designation TEXT NOT NULL DEFAULT '',
    lot_code VARCHAR(100) NOT NULL,
    sous_lot_code VARCHAR(150) NOT NULL DEFAULT '',
    unite VARCHAR(50) NOT NULL DEFAULT '',
    prix_local_fcfa NUMERIC(18, 2) NOT NULL DEFAULT 0,
    prix_import_fcfa NUMERIC(18, 2) NOT NULL DEFAULT 0,
    prix_optimise_fcfa NUMERIC(18, 2) NOT NULL DEFAULT 0,
    fournisseur_local VARCHAR(255) NOT NULL DEFAULT '',
    fournisseur_import VARCHAR(255) NOT NULL DEFAULT '',
    pays_import VARCHAR(100) NOT NULL DEFAULT '',
    source_prix VARCHAR(255) NOT NULL DEFAULT 'A_ENRICHIR_POINTE_NOIRE_CHINE',
    date_reference DATE,
    niveau_confiance VARCHAR(50) NOT NULL DEFAULT 'A_ENRICHIR',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_dim_bpu_v53_prix_non_negatifs CHECK (
        prix_local_fcfa >= 0
        AND prix_import_fcfa >= 0
        AND prix_optimise_fcfa >= 0
    )
);

CREATE INDEX IF NOT EXISTS ix_dim_bpu_v53_lot_code
    ON dim_bpu_v53 (lot_code);

CREATE INDEX IF NOT EXISTS ix_dim_bpu_v53_is_active
    ON dim_bpu_v53 (is_active);

INSERT INTO dim_bpu_v53 (
    article_code,
    designation,
    lot_code,
    sous_lot_code,
    unite,
    prix_local_fcfa,
    prix_import_fcfa,
    prix_optimise_fcfa,
    fournisseur_local,
    fournisseur_import,
    pays_import,
    source_prix,
    date_reference,
    niveau_confiance,
    is_active
)
SELECT
    source.article_code,
    MIN(source.designation) AS designation,
    MIN(source.lot_code) AS lot_code,
    MIN(source.sous_lot_code) AS sous_lot_code,
    MIN(source.unite) AS unite,
    0::numeric(18, 2) AS prix_local_fcfa,
    0::numeric(18, 2) AS prix_import_fcfa,
    0::numeric(18, 2) AS prix_optimise_fcfa,
    ''::varchar AS fournisseur_local,
    ''::varchar AS fournisseur_import,
    ''::varchar AS pays_import,
    'A_ENRICHIR_POINTE_NOIRE_CHINE'::varchar AS source_prix,
    NULL::date AS date_reference,
    'A_ENRICHIR'::varchar AS niveau_confiance,
    TRUE AS is_active
FROM (
    SELECT
        TRIM(generated_article_code)::varchar(255) AS article_code,
        COALESCE(NULLIF(TRIM(generated_designation), ''), TRIM(generated_article_code)) AS designation,
        TRIM(lot_code)::varchar(100) AS lot_code,
        COALESCE(NULLIF(TRIM(component_code), ''), '')::varchar(150) AS sous_lot_code,
        COALESCE(NULLIF(TRIM(unit), ''), '')::varchar(50) AS unite
    FROM vw_sp2i_generated_dqe_master
    WHERE NULLIF(TRIM(generated_article_code), '') IS NOT NULL
) source
GROUP BY source.article_code
ON CONFLICT (article_code) DO UPDATE SET
    designation = COALESCE(NULLIF(dim_bpu_v53.designation, ''), EXCLUDED.designation),
    lot_code = COALESCE(NULLIF(dim_bpu_v53.lot_code, ''), EXCLUDED.lot_code),
    sous_lot_code = COALESCE(NULLIF(dim_bpu_v53.sous_lot_code, ''), EXCLUDED.sous_lot_code),
    unite = COALESCE(NULLIF(dim_bpu_v53.unite, ''), EXCLUDED.unite),
    is_active = TRUE,
    updated_at = now();

COMMENT ON TABLE dim_bpu_v53 IS
'Referentiel BPU V5.3 18 lots, initialise depuis vw_sp2i_generated_dqe_master. Les prix restent a 0 avant enrichissement Pointe-Noire / Chine.';

COMMENT ON COLUMN dim_bpu_v53.article_code IS 'Code article genere V5.3, cle primaire du referentiel BPU.';
COMMENT ON COLUMN dim_bpu_v53.prix_local_fcfa IS 'Prix local FCFA a enrichir depuis le referentiel Pointe-Noire.';
COMMENT ON COLUMN dim_bpu_v53.prix_import_fcfa IS 'Prix import FCFA a enrichir depuis le referentiel Chine/import.';
COMMENT ON COLUMN dim_bpu_v53.prix_optimise_fcfa IS 'Prix optimise FCFA calcule ou renseigne apres enrichissement.';

COMMIT;
