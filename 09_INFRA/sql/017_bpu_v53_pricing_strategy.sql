-- SP2I CAPEX - Pricing strategy BPU V5.3
-- Migration: 017_bpu_v53_pricing_strategy.sql
--
-- Objectif:
-- - creer une strategie de valorisation provisoire par lot ;
-- - calculer une vue prix pour les 2524 articles de dim_bpu_v53 ;
-- - permettre les calculs CAPEX local, import, optimise et economies ;
-- - ne pas modifier fact_metre, fact_simulation, fact_approvals ou procurement_decisions.
--
-- Hypothese import Chine rendu Pointe-Noire:
-- - fret: 12%
-- - assurance + transit + livraison: 10%
-- - douane: 20%
-- - coefficient global rendu import: 1.42
--
-- Les prix restent enrichissables: si dim_bpu_v53 contient deja un prix non nul,
-- la vue le conserve avant de recourir a la strategie par lot.

BEGIN;

CREATE TABLE IF NOT EXISTS dim_pricing_strategy_v53 (
    lot_code VARCHAR(100) PRIMARY KEY,
    prix_base_local_fcfa NUMERIC(18, 2) NOT NULL,
    coefficient_import NUMERIC(8, 4) NOT NULL DEFAULT 0.6500,
    coefficient_transport NUMERIC(8, 4) NOT NULL DEFAULT 0.1200,
    coefficient_douane NUMERIC(8, 4) NOT NULL DEFAULT 0.2000,
    coefficient_logistique NUMERIC(8, 4) NOT NULL DEFAULT 0.1000,
    prix_base_import_fcfa NUMERIC(18, 2) NOT NULL,
    niveau_confiance VARCHAR(50) NOT NULL DEFAULT 'HYPOTHESE_V53',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_dim_pricing_strategy_v53_base_positive CHECK (
        prix_base_local_fcfa > 0
        AND prix_base_import_fcfa > 0
    ),
    CONSTRAINT ck_dim_pricing_strategy_v53_coefficients_non_negatifs CHECK (
        coefficient_import >= 0
        AND coefficient_transport >= 0
        AND coefficient_douane >= 0
        AND coefficient_logistique >= 0
    )
);

INSERT INTO dim_pricing_strategy_v53 (
    lot_code,
    prix_base_local_fcfa,
    coefficient_import,
    coefficient_transport,
    coefficient_douane,
    coefficient_logistique,
    prix_base_import_fcfa,
    niveau_confiance
)
VALUES
    ('LOT_ASC',       1850000, 0.6200, 0.1200, 0.2000, 0.1000, ROUND(1850000 * 0.6200, 2), 'HYPOTHESE_V53'),
    ('LOT_CAR',         45000, 0.6200, 0.1200, 0.2000, 0.1000, ROUND(  45000 * 0.6200, 2), 'HYPOTHESE_V53'),
    ('LOT_CFA',         28000, 0.6500, 0.1200, 0.2000, 0.1000, ROUND(  28000 * 0.6500, 2), 'HYPOTHESE_V53'),
    ('LOT_CVC',        420000, 0.6000, 0.1200, 0.2000, 0.1000, ROUND( 420000 * 0.6000, 2), 'HYPOTHESE_V53'),
    ('LOT_ELEC',        35000, 0.6500, 0.1200, 0.2000, 0.1000, ROUND(  35000 * 0.6500, 2), 'HYPOTHESE_V53'),
    ('LOT_FACADE',      90000, 0.6800, 0.1200, 0.2000, 0.1000, ROUND(  90000 * 0.6800, 2), 'HYPOTHESE_V53'),
    ('LOT_FP',          30000, 0.7000, 0.1200, 0.2000, 0.1000, ROUND(  30000 * 0.7000, 2), 'HYPOTHESE_V53'),
    ('LOT_GO',         125000, 0.7200, 0.1200, 0.2000, 0.1000, ROUND( 125000 * 0.7200, 2), 'HYPOTHESE_V53'),
    ('LOT_INCENDIE',    85000, 0.6400, 0.1200, 0.2000, 0.1000, ROUND(  85000 * 0.6400, 2), 'HYPOTHESE_V53'),
    ('LOT_MAC',         65000, 0.7000, 0.1200, 0.2000, 0.1000, ROUND(  65000 * 0.7000, 2), 'HYPOTHESE_V53'),
    ('LOT_MENU_EXT',   180000, 0.6600, 0.1200, 0.2000, 0.1000, ROUND( 180000 * 0.6600, 2), 'HYPOTHESE_V53'),
    ('LOT_MENU_INT',    95000, 0.6700, 0.1200, 0.2000, 0.1000, ROUND(  95000 * 0.6700, 2), 'HYPOTHESE_V53'),
    ('LOT_PLOMB',       42000, 0.6500, 0.1200, 0.2000, 0.1000, ROUND(  42000 * 0.6500, 2), 'HYPOTHESE_V53'),
    ('LOT_PNT',         22000, 0.7600, 0.1200, 0.2000, 0.1000, ROUND(  22000 * 0.7600, 2), 'HYPOTHESE_V53'),
    ('LOT_SAN',        145000, 0.6200, 0.1200, 0.2000, 0.1000, ROUND( 145000 * 0.6200, 2), 'HYPOTHESE_V53'),
    ('LOT_SECURITE',    75000, 0.6300, 0.1200, 0.2000, 0.1000, ROUND(  75000 * 0.6300, 2), 'HYPOTHESE_V53'),
    ('LOT_TOIT',        70000, 0.6900, 0.1200, 0.2000, 0.1000, ROUND(  70000 * 0.6900, 2), 'HYPOTHESE_V53'),
    ('LOT_VRD',         55000, 0.7400, 0.1200, 0.2000, 0.1000, ROUND(  55000 * 0.7400, 2), 'HYPOTHESE_V53')
ON CONFLICT (lot_code) DO UPDATE SET
    prix_base_local_fcfa = EXCLUDED.prix_base_local_fcfa,
    coefficient_import = EXCLUDED.coefficient_import,
    coefficient_transport = EXCLUDED.coefficient_transport,
    coefficient_douane = EXCLUDED.coefficient_douane,
    coefficient_logistique = EXCLUDED.coefficient_logistique,
    prix_base_import_fcfa = EXCLUDED.prix_base_import_fcfa,
    niveau_confiance = EXCLUDED.niveau_confiance;

CREATE OR REPLACE VIEW vw_bpu_v53_priced AS
WITH priced AS (
    SELECT
        b.article_code,
        b.designation,
        b.lot_code,
        b.sous_lot_code,
        b.unite,
        b.fournisseur_local,
        b.fournisseur_import,
        b.pays_import,
        b.source_prix,
        b.date_reference,
        b.is_active,
        s.prix_base_local_fcfa,
        s.prix_base_import_fcfa,
        s.coefficient_import,
        s.coefficient_transport,
        s.coefficient_douane,
        s.coefficient_logistique,
        (1 + s.coefficient_transport + s.coefficient_douane + s.coefficient_logistique) AS coefficient_global_import,
        COALESCE(NULLIF(b.niveau_confiance, 'A_ENRICHIR'), s.niveau_confiance) AS niveau_confiance,
        COALESCE(NULLIF(b.prix_local_fcfa, 0), s.prix_base_local_fcfa) AS prix_local_calcule,
        COALESCE(
            NULLIF(b.prix_import_fcfa, 0),
            s.prix_base_import_fcfa
                * (1 + s.coefficient_transport + s.coefficient_douane + s.coefficient_logistique)
        ) AS prix_import_calcule
    FROM dim_bpu_v53 b
    LEFT JOIN dim_pricing_strategy_v53 s
      ON s.lot_code = b.lot_code
)
SELECT
    article_code,
    designation,
    lot_code,
    sous_lot_code,
    unite,
    ROUND(prix_local_calcule, 2) AS prix_local_fcfa,
    ROUND(prix_import_calcule, 2) AS prix_import_fcfa,
    ROUND(LEAST(prix_local_calcule, prix_import_calcule), 2) AS prix_optimise_fcfa,
    ROUND(GREATEST(prix_local_calcule - LEAST(prix_local_calcule, prix_import_calcule), 0), 2) AS economie_unitaire_fcfa,
    CASE
        WHEN prix_import_calcule < prix_local_calcule THEN 'IMPORT'
        ELSE 'LOCAL'
    END AS decision_import,
    fournisseur_local,
    fournisseur_import,
    pays_import,
    source_prix,
    date_reference,
    niveau_confiance,
    coefficient_import,
    coefficient_transport,
    coefficient_douane,
    coefficient_logistique,
    coefficient_global_import,
    prix_base_local_fcfa,
    prix_base_import_fcfa,
    is_active
FROM priced;

COMMENT ON TABLE dim_pricing_strategy_v53 IS
'Strategie provisoire de valorisation par lot pour BPU V5.3. Coefficients import: fret 12%, douane 20%, logistique 10%, coefficient rendu 1.42.';

COMMENT ON VIEW vw_bpu_v53_priced IS
'Vue de prix BPU V5.3 calculee depuis dim_bpu_v53 et dim_pricing_strategy_v53. Les prix stockes non nuls priment sur les hypotheses par lot.';

COMMIT;
