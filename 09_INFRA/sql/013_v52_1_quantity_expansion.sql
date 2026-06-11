-- SP2I CAPEX - V5.2.1 Quantity Expansion
-- Migration: 013_v52_1_quantity_expansion.sql
--
-- Objectif:
-- - transformer les equipements generatifs V5.2 en lignes DQE detaillees ;
-- - passer d'environ 216 lignes DQE generatives a 1500-3000 lignes detaillees ;
-- - ne modifier aucun objet historique ;
-- - ne pas ecrire dans fact_metre, fact_simulation, fact_approvals ou procurement_decisions.
--
-- Dependances:
-- - 012_v51_dimensions.sql
-- - 013_v52_generative_engine.sql
--
-- Garanties:
-- - strictement additif ;
-- - idempotent ;
-- - compatible Neon / PostgreSQL 18 / Power BI DirectQuery.

BEGIN;

CREATE TABLE IF NOT EXISTS dim_quantity_expansion_rule (
    rule_id BIGSERIAL PRIMARY KEY,
    equipment_code VARCHAR(120) NOT NULL,
    generated_article_code VARCHAR(180) NOT NULL,
    quantity_formula VARCHAR(120) NOT NULL,
    generated_designation VARCHAR(500) NOT NULL DEFAULT '',
    unit VARCHAR(40) NOT NULL DEFAULT 'U',
    lot_code VARCHAR(120) NOT NULL DEFAULT '',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_dim_quantity_expansion_rule UNIQUE (equipment_code, generated_article_code)
);

COMMENT ON TABLE dim_quantity_expansion_rule IS
    'V5.2.1 - Regles de decomposition d un equipement generatif en lignes DQE elementaires.';

COMMENT ON COLUMN dim_quantity_expansion_rule.quantity_formula IS
    'Formules supportees: BASE, FIXED_n, QTY*n, SURFACE*n, DISTANCE_n.';

CREATE TABLE IF NOT EXISTS fact_generation_expansion (
    expansion_id BIGSERIAL PRIMARY KEY,
    generation_id BIGINT NOT NULL REFERENCES fact_generation_bim(generation_id),
    equipment_code VARCHAR(120) NOT NULL,
    generated_article_code VARCHAR(180) NOT NULL,
    generated_designation VARCHAR(500) NOT NULL,
    quantity NUMERIC(16, 4) NOT NULL DEFAULT 0,
    unit VARCHAR(40) NOT NULL DEFAULT 'U',
    lot_code VARCHAR(120) NOT NULL DEFAULT '',
    source_quantity NUMERIC(14, 4) NOT NULL DEFAULT 0,
    source_surface_m2 NUMERIC(12, 2) NOT NULL DEFAULT 0,
    quantity_formula VARCHAR(120) NOT NULL,
    generation_batch VARCHAR(120) NOT NULL DEFAULT 'BAT_01_V52',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fact_generation_expansion UNIQUE (generation_id, generated_article_code)
);

-- ============================================================================
-- 1. REGLES D EXPANSION
-- ============================================================================

INSERT INTO dim_quantity_expansion_rule (
    equipment_code,
    generated_article_code,
    quantity_formula,
    generated_designation,
    unit,
    lot_code,
    is_active
)
VALUES
    -- ELECTRICITE - SPOTS
    ('SPOT_LED', 'SPOT_LED', 'BASE', 'Spot LED encastre', 'U', 'LOT_ELEC', TRUE),
    ('SPOT_LED', 'CABLE_3G1_5', 'QTY*12', 'Cable 3G1.5 eclairage', 'ML', 'LOT_ELEC', TRUE),
    ('SPOT_LED', 'GAINE_ICTA16', 'QTY*12', 'Gaine ICTA 16 eclairage', 'ML', 'LOT_ELEC', TRUE),
    ('SPOT_LED', 'BOITE_DCL', 'BASE', 'Boite DCL', 'U', 'LOT_ELEC', TRUE),
    ('SPOT_LED', 'CONNECTEUR_WAGO', 'QTY*2', 'Connecteurs Wago eclairage', 'U', 'LOT_ELEC', TRUE),
    ('SPOT_LED', 'DRIVER_LED', 'QTY*0.25', 'Quote-part driver LED', 'U', 'LOT_ELEC', TRUE),
    ('SPOT_LED', 'QUOTE_PART_TABLEAU_ECL', 'QTY*0.05', 'Quote-part tableau eclairage', 'U', 'LOT_ELEC', TRUE),
    ('SPOT_LED', 'DISJONCTEUR_10A', 'QTY*0.05', 'Quote-part disjoncteur 10A', 'U', 'LOT_ELEC', TRUE),
    ('SPOT_LED', 'REPERE_CIRCUIT_ECL', 'BASE', 'Reperage circuit eclairage', 'U', 'LOT_ELEC', TRUE),

    -- ELECTRICITE - PRISES 16A ET PRISES SPECIALISEES
    ('PRISE_16A', 'PRISE_16A', 'BASE', 'Prise 16A 2P+T', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_16A', 'CABLE_3G2_5', 'QTY*14', 'Cable 3G2.5 prises', 'ML', 'LOT_ELEC', TRUE),
    ('PRISE_16A', 'GAINE_ICTA20', 'QTY*14', 'Gaine ICTA 20 prises', 'ML', 'LOT_ELEC', TRUE),
    ('PRISE_16A', 'BOITE_ENCASTREMENT', 'BASE', 'Boite encastrement prise', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_16A', 'CONNECTEUR_PRISE', 'QTY*2', 'Connecteurs prises', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_16A', 'QUOTE_PART_TABLEAU_PRISE', 'QTY*0.08', 'Quote-part tableau prises', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_16A', 'QUOTE_PART_DISJONCTEUR_16A', 'QTY*0.08', 'Quote-part disjoncteur 16A', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_16A', 'REPERE_CIRCUIT_PRISE', 'BASE', 'Reperage circuit prises', 'U', 'LOT_ELEC', TRUE),

    ('PRISE_PLAN_TRAVAIL', 'PRISE_PLAN_TRAVAIL', 'BASE', 'Prise plan de travail', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_PLAN_TRAVAIL', 'CABLE_3G2_5_CUISINE', 'QTY*16', 'Cable 3G2.5 cuisine', 'ML', 'LOT_ELEC', TRUE),
    ('PRISE_PLAN_TRAVAIL', 'GAINE_ICTA20_CUISINE', 'QTY*16', 'Gaine ICTA 20 cuisine', 'ML', 'LOT_ELEC', TRUE),
    ('PRISE_PLAN_TRAVAIL', 'BOITE_ENCASTREMENT_CUISINE', 'BASE', 'Boite encastrement cuisine', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_PLAN_TRAVAIL', 'PROTECTION_20A_CUISINE', 'QTY*0.25', 'Quote-part protection 20A cuisine', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_PLAN_TRAVAIL', 'CONNECTEUR_CUISINE', 'QTY*2', 'Connecteurs cuisine', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_PLAN_TRAVAIL', 'REPERE_CIRCUIT_CUISINE', 'BASE', 'Reperage circuit cuisine', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_PLAN_TRAVAIL', 'QUOTE_PART_TABLEAU_CUISINE', 'QTY*0.10', 'Quote-part tableau cuisine', 'U', 'LOT_ELEC', TRUE),

    ('PRISE_FRIGO', 'PRISE_FRIGO', 'BASE', 'Prise frigo specialisee', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_FRIGO', 'CABLE_FRIGO_3G2_5', 'QTY*16', 'Cable frigo 3G2.5', 'ML', 'LOT_ELEC', TRUE),
    ('PRISE_FRIGO', 'GAINE_FRIGO_ICTA20', 'QTY*16', 'Gaine frigo ICTA20', 'ML', 'LOT_ELEC', TRUE),
    ('PRISE_FRIGO', 'BOITE_FRIGO', 'BASE', 'Boite prise frigo', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_FRIGO', 'PROTECTION_FRIGO_16A', 'BASE', 'Protection frigo 16A', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_FRIGO', 'CONNECTEUR_FRIGO', 'QTY*2', 'Connecteurs frigo', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_FRIGO', 'REPERE_FRIGO', 'BASE', 'Reperage circuit frigo', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_FRIGO', 'QUOTE_PART_TABLEAU_FRIGO', 'QTY*0.10', 'Quote-part tableau frigo', 'U', 'LOT_ELEC', TRUE),

    ('PRISE_MICRO_ONDES', 'PRISE_MICRO_ONDES', 'BASE', 'Prise micro-ondes specialisee', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_MICRO_ONDES', 'CABLE_MICRO_ONDES_3G2_5', 'QTY*15', 'Cable micro-ondes 3G2.5', 'ML', 'LOT_ELEC', TRUE),
    ('PRISE_MICRO_ONDES', 'GAINE_MICRO_ONDES_ICTA20', 'QTY*15', 'Gaine micro-ondes ICTA20', 'ML', 'LOT_ELEC', TRUE),
    ('PRISE_MICRO_ONDES', 'BOITE_MICRO_ONDES', 'BASE', 'Boite prise micro-ondes', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_MICRO_ONDES', 'PROTECTION_MICRO_ONDES_16A', 'BASE', 'Protection micro-ondes 16A', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_MICRO_ONDES', 'CONNECTEUR_MICRO_ONDES', 'QTY*2', 'Connecteurs micro-ondes', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_MICRO_ONDES', 'REPERE_MICRO_ONDES', 'BASE', 'Reperage circuit micro-ondes', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_MICRO_ONDES', 'QUOTE_PART_TABLEAU_MICRO_ONDES', 'QTY*0.10', 'Quote-part tableau micro-ondes', 'U', 'LOT_ELEC', TRUE),

    ('PRISE_HOTTE', 'PRISE_HOTTE', 'BASE', 'Prise hotte specialisee', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_HOTTE', 'CABLE_HOTTE_3G2_5', 'QTY*14', 'Cable hotte 3G2.5', 'ML', 'LOT_ELEC', TRUE),
    ('PRISE_HOTTE', 'GAINE_HOTTE_ICTA20', 'QTY*14', 'Gaine hotte ICTA20', 'ML', 'LOT_ELEC', TRUE),
    ('PRISE_HOTTE', 'BOITE_HOTTE', 'BASE', 'Boite prise hotte', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_HOTTE', 'PROTECTION_HOTTE_16A', 'BASE', 'Protection hotte 16A', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_HOTTE', 'CONNECTEUR_HOTTE', 'QTY*2', 'Connecteurs hotte', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_HOTTE', 'REPERE_HOTTE', 'BASE', 'Reperage circuit hotte', 'U', 'LOT_ELEC', TRUE),
    ('PRISE_HOTTE', 'QUOTE_PART_TABLEAU_HOTTE', 'QTY*0.10', 'Quote-part tableau hotte', 'U', 'LOT_ELEC', TRUE),

    -- CFA
    ('PRISE_RJ45', 'PRISE_RJ45', 'BASE', 'Prise RJ45', 'U', 'LOT_CFA', TRUE),
    ('PRISE_RJ45', 'CABLE_CAT6', 'QTY*18', 'Cable CAT6', 'ML', 'LOT_CFA', TRUE),
    ('PRISE_RJ45', 'GAINE_CFA20', 'QTY*18', 'Gaine CFA 20', 'ML', 'LOT_CFA', TRUE),
    ('PRISE_RJ45', 'BOITE_CFA', 'BASE', 'Boite encastrement CFA', 'U', 'LOT_CFA', TRUE),
    ('PRISE_RJ45', 'PATCH_PANEL', 'QTY*0.10', 'Quote-part patch panel', 'U', 'LOT_CFA', TRUE),
    ('PRISE_RJ45', 'QUOTE_PART_SWITCH', 'QTY*0.05', 'Quote-part switch', 'U', 'LOT_CFA', TRUE),
    ('PRISE_RJ45', 'REPERE_CFA', 'BASE', 'Reperage CFA', 'U', 'LOT_CFA', TRUE),

    ('PRISE_TV', 'PRISE_TV', 'BASE', 'Prise TV', 'U', 'LOT_CFA', TRUE),
    ('PRISE_TV', 'CABLE_COAX', 'QTY*18', 'Cable coaxial TV', 'ML', 'LOT_CFA', TRUE),
    ('PRISE_TV', 'GAINE_CFA_TV', 'QTY*18', 'Gaine CFA TV', 'ML', 'LOT_CFA', TRUE),
    ('PRISE_TV', 'BOITE_TV', 'BASE', 'Boite prise TV', 'U', 'LOT_CFA', TRUE),
    ('PRISE_TV', 'REPARTITEUR_TV', 'QTY*0.10', 'Quote-part repartiteur TV', 'U', 'LOT_CFA', TRUE),
    ('PRISE_TV', 'REPERE_TV', 'BASE', 'Reperage TV', 'U', 'LOT_CFA', TRUE),

    -- SANITAIRE / PLOMBERIE
    ('LAVABO', 'LAVABO', 'BASE', 'Lavabo', 'U', 'LOT_SAN', TRUE),
    ('LAVABO', 'EF_LAVABO', 'QTY*6', 'Alimentation EF lavabo', 'ML', 'LOT_PLOMB', TRUE),
    ('LAVABO', 'EC_LAVABO', 'QTY*6', 'Alimentation EC lavabo', 'ML', 'LOT_PLOMB', TRUE),
    ('LAVABO', 'EU_LAVABO', 'QTY*5', 'Evacuation EU lavabo', 'ML', 'LOT_PLOMB', TRUE),
    ('LAVABO', 'ROBINET_LAVABO', 'BASE', 'Robinet lavabo', 'U', 'LOT_SAN', TRUE),
    ('LAVABO', 'SIPHON_LAVABO', 'BASE', 'Siphon lavabo', 'U', 'LOT_SAN', TRUE),
    ('LAVABO', 'RACCORDS_LAVABO', 'QTY*4', 'Raccords lavabo', 'U', 'LOT_PLOMB', TRUE),
    ('LAVABO', 'FIXATION_LAVABO', 'BASE', 'Fixation lavabo', 'U', 'LOT_SAN', TRUE),
    ('LAVABO', 'JOINT_SANITAIRE_LAVABO', 'QTY*2', 'Joint sanitaire lavabo', 'U', 'LOT_SAN', TRUE),

    ('WC', 'WC', 'BASE', 'Cuvette WC', 'U', 'LOT_SAN', TRUE),
    ('WC', 'EF_WC', 'QTY*5', 'Alimentation EF WC', 'ML', 'LOT_PLOMB', TRUE),
    ('WC', 'EV_WC', 'QTY*5', 'Evacuation EV WC', 'ML', 'LOT_PLOMB', TRUE),
    ('WC', 'ROBINET_ARRET_WC', 'BASE', 'Robinet arret WC', 'U', 'LOT_PLOMB', TRUE),
    ('WC', 'RACCORDS_WC', 'QTY*4', 'Raccords WC', 'U', 'LOT_PLOMB', TRUE),
    ('WC', 'FIXATION_WC', 'BASE', 'Fixation WC', 'U', 'LOT_SAN', TRUE),
    ('WC', 'JOINT_WC', 'QTY*2', 'Joint WC', 'U', 'LOT_SAN', TRUE),

    ('DOUCHE', 'DOUCHE', 'BASE', 'Douche', 'U', 'LOT_SAN', TRUE),
    ('DOUCHE', 'EF_DOUCHE', 'QTY*8', 'Alimentation EF douche', 'ML', 'LOT_PLOMB', TRUE),
    ('DOUCHE', 'EC_DOUCHE', 'QTY*8', 'Alimentation EC douche', 'ML', 'LOT_PLOMB', TRUE),
    ('DOUCHE', 'EV_DOUCHE', 'QTY*6', 'Evacuation douche', 'ML', 'LOT_PLOMB', TRUE),
    ('DOUCHE', 'MITIGEUR_DOUCHE', 'BASE', 'Mitigeur douche', 'U', 'LOT_SAN', TRUE),
    ('DOUCHE', 'SIPHON_DOUCHE', 'BASE', 'Siphon douche', 'U', 'LOT_SAN', TRUE),
    ('DOUCHE', 'RACCORDS_DOUCHE', 'QTY*6', 'Raccords douche', 'U', 'LOT_PLOMB', TRUE),
    ('DOUCHE', 'PAROI_DOUCHE', 'BASE', 'Paroi douche', 'U', 'LOT_SAN', TRUE),
    ('DOUCHE', 'ETANCHEITE_DOUCHE', 'QTY*1', 'Etancheite douche', 'ENS', 'LOT_SAN', TRUE),

    ('EVIER', 'EVIER', 'BASE', 'Evier cuisine', 'U', 'LOT_PLOMB', TRUE),
    ('EVIER', 'EF_EVIER', 'QTY*8', 'Alimentation EF evier', 'ML', 'LOT_PLOMB', TRUE),
    ('EVIER', 'EC_EVIER', 'QTY*8', 'Alimentation EC evier', 'ML', 'LOT_PLOMB', TRUE),
    ('EVIER', 'EU_EVIER', 'QTY*7', 'Evacuation evier', 'ML', 'LOT_PLOMB', TRUE),
    ('EVIER', 'ROBINET_EVIER', 'BASE', 'Robinet evier', 'U', 'LOT_PLOMB', TRUE),
    ('EVIER', 'SIPHON_EVIER', 'BASE', 'Siphon evier', 'U', 'LOT_PLOMB', TRUE),
    ('EVIER', 'RACCORDS_EVIER', 'QTY*6', 'Raccords evier', 'U', 'LOT_PLOMB', TRUE),
    ('EVIER', 'FIXATION_EVIER', 'BASE', 'Fixation evier', 'U', 'LOT_PLOMB', TRUE),
    ('EVIER', 'JOINT_EVIER', 'QTY*2', 'Joint evier', 'U', 'LOT_PLOMB', TRUE),

    -- CVC
    ('SPLIT_12000', 'SPLIT_12000', 'BASE', 'Split 12000 BTU', 'U', 'LOT_CVC', TRUE),
    ('SPLIT_12000', 'CUIVRE_GAZ_12000', 'QTY*10', 'Cuivre gaz split 12000', 'ML', 'LOT_CVC', TRUE),
    ('SPLIT_12000', 'CUIVRE_LIQUIDE_12000', 'QTY*10', 'Cuivre liquide split 12000', 'ML', 'LOT_CVC', TRUE),
    ('SPLIT_12000', 'CONDENSAT_12000', 'QTY*10', 'Evacuation condensats split 12000', 'ML', 'LOT_CVC', TRUE),
    ('SPLIT_12000', 'ALIMENTATION_ELEC_SPLIT_12000', 'QTY*10', 'Alimentation electrique split 12000', 'ML', 'LOT_ELEC', TRUE),
    ('SPLIT_12000', 'SUPPORT_SPLIT_12000', 'BASE', 'Support split 12000', 'U', 'LOT_CVC', TRUE),
    ('SPLIT_12000', 'PERCEMENT_SPLIT_12000', 'BASE', 'Percement split 12000', 'U', 'LOT_CVC', TRUE),
    ('SPLIT_12000', 'MISE_EN_SERVICE_SPLIT_12000', 'BASE', 'Mise en service split 12000', 'U', 'LOT_CVC', TRUE),

    ('SPLIT_18000', 'SPLIT_18000', 'BASE', 'Split 18000 BTU', 'U', 'LOT_CVC', TRUE),
    ('SPLIT_18000', 'CUIVRE_GAZ_18000', 'QTY*12', 'Cuivre gaz split 18000', 'ML', 'LOT_CVC', TRUE),
    ('SPLIT_18000', 'CUIVRE_LIQUIDE_18000', 'QTY*12', 'Cuivre liquide split 18000', 'ML', 'LOT_CVC', TRUE),
    ('SPLIT_18000', 'CONDENSAT_18000', 'QTY*12', 'Evacuation condensats split 18000', 'ML', 'LOT_CVC', TRUE),
    ('SPLIT_18000', 'ALIMENTATION_ELEC_SPLIT_18000', 'QTY*12', 'Alimentation electrique split 18000', 'ML', 'LOT_ELEC', TRUE),
    ('SPLIT_18000', 'SUPPORT_SPLIT_18000', 'BASE', 'Support split 18000', 'U', 'LOT_CVC', TRUE),
    ('SPLIT_18000', 'PERCEMENT_SPLIT_18000', 'BASE', 'Percement split 18000', 'U', 'LOT_CVC', TRUE),
    ('SPLIT_18000', 'MISE_EN_SERVICE_SPLIT_18000', 'BASE', 'Mise en service split 18000', 'U', 'LOT_CVC', TRUE),

    ('EXTRACTEUR', 'EXTRACTEUR', 'BASE', 'Extracteur air', 'U', 'LOT_CVC', TRUE),
    ('EXTRACTEUR', 'GAINE_EXTRACTEUR', 'QTY*6', 'Gaine extracteur', 'ML', 'LOT_CVC', TRUE),
    ('EXTRACTEUR', 'ALIMENTATION_EXTRACTEUR', 'QTY*6', 'Alimentation extracteur', 'ML', 'LOT_ELEC', TRUE),
    ('EXTRACTEUR', 'GRILLE_EXTRACTEUR', 'BASE', 'Grille extracteur', 'U', 'LOT_CVC', TRUE),
    ('EXTRACTEUR', 'CLAPET_EXTRACTEUR', 'BASE', 'Clapet anti-retour extracteur', 'U', 'LOT_CVC', TRUE),

    -- COMPLEMENTS SURFACIQUES ACCROCHES AUX PIECES
    ('SPOT_LED', 'OSSATURE_FP', 'SURFACE*1', 'Ossature faux plafond', 'M2', 'LOT_FP', TRUE),
    ('SPOT_LED', 'SUSPENTES_FP', 'SURFACE*1.2', 'Suspentes faux plafond', 'U', 'LOT_FP', TRUE),
    ('SPOT_LED', 'FOURRURES_FP', 'SURFACE*1.5', 'Fourrures faux plafond', 'ML', 'LOT_FP', TRUE),
    ('SPOT_LED', 'BA13_FP', 'SURFACE*1', 'Plaque BA13 faux plafond', 'M2', 'LOT_FP', TRUE),
    ('SPOT_LED', 'BANDES_FP', 'SURFACE*0.8', 'Bandes a joint faux plafond', 'ML', 'LOT_FP', TRUE),
    ('SPOT_LED', 'ENDUITS_FP', 'SURFACE*0.2', 'Enduits faux plafond', 'KG', 'LOT_FP', TRUE),

    ('PRISE_16A', 'IMPRESSION_MUR', 'SURFACE*2.5', 'Impression murs', 'M2', 'LOT_PNT', TRUE),
    ('PRISE_16A', 'PEINTURE_MUR', 'SURFACE*2.5', 'Peinture murs', 'M2', 'LOT_PNT', TRUE),
    ('SPOT_LED', 'PEINTURE_PLAFOND', 'SURFACE*1', 'Peinture plafond', 'M2', 'LOT_PNT', TRUE),

    ('EVIER', 'CARRELAGE_CUISINE', 'SURFACE*0.6', 'Carrelage cuisine', 'M2', 'LOT_CAR', TRUE),
    ('EVIER', 'COLLE_CARRELAGE_CUISINE', 'SURFACE*2', 'Colle carrelage cuisine', 'KG', 'LOT_CAR', TRUE),
    ('EVIER', 'JOINT_CARRELAGE_CUISINE', 'SURFACE*0.4', 'Joint carrelage cuisine', 'KG', 'LOT_CAR', TRUE),
    ('EVIER', 'PLINTHE_CUISINE', 'SURFACE*0.35', 'Plinthe cuisine', 'ML', 'LOT_CAR', TRUE),

    ('DOUCHE', 'CARRELAGE_SDB', 'SURFACE*1.8', 'Carrelage salle de bain', 'M2', 'LOT_CAR', TRUE),
    ('DOUCHE', 'COLLE_CARRELAGE_SDB', 'SURFACE*3', 'Colle carrelage salle de bain', 'KG', 'LOT_CAR', TRUE),
    ('DOUCHE', 'JOINT_CARRELAGE_SDB', 'SURFACE*0.6', 'Joint carrelage salle de bain', 'KG', 'LOT_CAR', TRUE),
    ('DOUCHE', 'ETANCHEITE_SOL_SDB', 'SURFACE*1', 'Etancheite sol salle de bain', 'M2', 'LOT_CAR', TRUE),

    -- SOLAIRE / FORAGE / VRD prets pour phases suivantes
    ('PANNEAU_550W', 'PANNEAU_550W', 'BASE', 'Panneau solaire 550W', 'U', 'LOT_SOLAIRE', TRUE),
    ('PANNEAU_550W', 'STRUCTURE_SOLAR', 'BASE', 'Structure panneau solaire', 'U', 'LOT_SOLAIRE', TRUE),
    ('PANNEAU_550W', 'CABLAGE_DC_SOLAR', 'QTY*8', 'Cablage DC solaire', 'ML', 'LOT_SOLAIRE', TRUE),
    ('PANNEAU_550W', 'CONNECTEURS_SOLAR', 'QTY*2', 'Connecteurs solaires', 'U', 'LOT_SOLAIRE', TRUE),
    ('PANNEAU_550W', 'QUOTE_PART_ONDULEUR', 'QTY*0.04', 'Quote-part onduleur', 'U', 'LOT_SOLAIRE', TRUE),
    ('PANNEAU_550W', 'QUOTE_PART_BATTERIE', 'QTY*0.06', 'Quote-part batterie', 'U', 'LOT_SOLAIRE', TRUE),

    ('POMPE_IMMERGEE', 'POMPE_IMMERGEE', 'BASE', 'Pompe immergee', 'U', 'LOT_HYDRAULIQUE', TRUE),
    ('POMPE_IMMERGEE', 'CABLE_POMPE', 'QTY*150', 'Cable pompe immergee', 'ML', 'LOT_HYDRAULIQUE', TRUE),
    ('POMPE_IMMERGEE', 'TUYAUTERIE_FORAGE', 'QTY*150', 'Tuyauterie forage', 'ML', 'LOT_HYDRAULIQUE', TRUE),
    ('POMPE_IMMERGEE', 'SURPRESSEUR', 'BASE', 'Surpresseur', 'U', 'LOT_HYDRAULIQUE', TRUE),
    ('POMPE_IMMERGEE', 'CUVE_STOCKAGE', 'BASE', 'Cuve stockage eau', 'U', 'LOT_HYDRAULIQUE', TRUE),
    ('POMPE_IMMERGEE', 'TRAITEMENT_EAU', 'BASE', 'Traitement eau', 'U', 'LOT_HYDRAULIQUE', TRUE)
ON CONFLICT (equipment_code, generated_article_code) DO NOTHING;

-- ============================================================================
-- 2. GENERATION DES QUANTITES DETAILLEES
-- ============================================================================

INSERT INTO fact_generation_expansion (
    generation_id,
    equipment_code,
    generated_article_code,
    generated_designation,
    quantity,
    unit,
    lot_code,
    source_quantity,
    source_surface_m2,
    quantity_formula,
    generation_batch
)
SELECT
    gb.generation_id,
    gb.article_code AS equipment_code,
    rule.generated_article_code,
    rule.generated_designation,
    ROUND(
        GREATEST(
            CASE
                WHEN rule.quantity_formula = 'BASE' THEN gb.quantity_generated
                WHEN rule.quantity_formula LIKE 'FIXED_%' THEN regexp_replace(rule.quantity_formula, '[^0-9.]', '', 'g')::NUMERIC
                WHEN rule.quantity_formula LIKE 'QTY*%' THEN gb.quantity_generated * regexp_replace(rule.quantity_formula, '[^0-9.]', '', 'g')::NUMERIC
                WHEN rule.quantity_formula LIKE 'SURFACE*%' THEN gb.surface_m2 * regexp_replace(rule.quantity_formula, '[^0-9.]', '', 'g')::NUMERIC
                WHEN rule.quantity_formula = 'SURFACE' THEN gb.surface_m2
                WHEN rule.quantity_formula LIKE 'DISTANCE_%' THEN gb.quantity_generated * regexp_replace(rule.quantity_formula, '[^0-9.]', '', 'g')::NUMERIC
                ELSE gb.quantity_generated
            END,
            0
        )::NUMERIC,
        4
    ) AS quantity,
    rule.unit,
    rule.lot_code,
    gb.quantity_generated,
    gb.surface_m2,
    rule.quantity_formula,
    gb.generation_batch
FROM fact_generation_bim gb
JOIN dim_quantity_expansion_rule rule
  ON rule.equipment_code = gb.article_code
 AND rule.is_active
WHERE gb.generation_batch = 'BAT_01_V52'
ON CONFLICT (generation_id, generated_article_code) DO NOTHING;

-- ============================================================================
-- 3. VUES POWER BI V5.2.1
-- ============================================================================

CREATE OR REPLACE VIEW vw_sp2i_generated_quantities AS
SELECT
    fx.generation_batch,
    gb.project_id,
    gb.batiment_id,
    gb.niveau_id,
    gb.appartement_id AS appartement,
    gb.piece_id,
    tp.code AS type_piece,
    fx.equipment_code,
    fx.generated_article_code,
    fx.generated_designation,
    fx.quantity,
    fx.unit,
    fx.lot_code,
    fx.source_quantity,
    fx.source_surface_m2,
    fx.quantity_formula,
    fx.created_at
FROM fact_generation_expansion fx
JOIN fact_generation_bim gb
  ON gb.generation_id = fx.generation_id
LEFT JOIN dim_type_piece tp
  ON tp.id = gb.type_piece_id;

CREATE OR REPLACE VIEW vw_sp2i_generated_network_quantities AS
SELECT
    generation_batch,
    lot_code,
    equipment_code,
    generated_article_code,
    generated_designation,
    unit,
    COUNT(*) AS nb_lignes,
    ROUND(COALESCE(SUM(quantity), 0)::NUMERIC, 4) AS quantite_totale,
    SUM(
        CASE
            WHEN unit = 'ML' THEN CEIL(GREATEST(quantity, 1))
            ELSE GREATEST(CEIL(quantity), 1)
        END
    )::BIGINT AS network_rows_estimated
FROM vw_sp2i_generated_quantities
WHERE lot_code IN (
    'LOT_ELEC',
    'LOT_CFA',
    'LOT_PLOMB',
    'LOT_SAN',
    'LOT_CVC',
    'LOT_INCENDIE',
    'LOT_SECURITE',
    'LOT_SOLAIRE',
    'LOT_HYDRAULIQUE',
    'LOT_VRD'
)
GROUP BY
    generation_batch,
    lot_code,
    equipment_code,
    generated_article_code,
    generated_designation,
    unit;

-- ============================================================================
-- 4. INDEX PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS ix_dim_quantity_expansion_rule_equipment
    ON dim_quantity_expansion_rule (equipment_code)
    WHERE is_active;

CREATE INDEX IF NOT EXISTS ix_dim_quantity_expansion_rule_generated_article
    ON dim_quantity_expansion_rule (generated_article_code);

CREATE INDEX IF NOT EXISTS ix_fact_generation_expansion_batch_lot
    ON fact_generation_expansion (generation_batch, lot_code);

CREATE INDEX IF NOT EXISTS ix_fact_generation_expansion_generation
    ON fact_generation_expansion (generation_id);

CREATE INDEX IF NOT EXISTS ix_fact_generation_expansion_article
    ON fact_generation_expansion (generated_article_code);

COMMIT;

-- ============================================================================
-- 5. VALIDATION RAPIDE
-- ============================================================================

SELECT relation_name, rows_count
FROM (
    VALUES
        ('dim_quantity_expansion_rule', (SELECT COUNT(*) FROM dim_quantity_expansion_rule)),
        ('fact_generation_expansion', (SELECT COUNT(*) FROM fact_generation_expansion)),
        ('vw_sp2i_generated_quantities', (SELECT COUNT(*) FROM vw_sp2i_generated_quantities)),
        ('vw_sp2i_generated_network_quantities', (SELECT COUNT(*) FROM vw_sp2i_generated_network_quantities))
) AS validation(relation_name, rows_count)
ORDER BY relation_name;

SELECT
    generation_batch,
    COUNT(*) AS nb_generation_dqe_detail,
    COUNT(DISTINCT lot_code) AS nb_lots,
    ROUND(COALESCE(SUM(quantity), 0)::NUMERIC, 2) AS quantite_totale
FROM vw_sp2i_generated_quantities
GROUP BY generation_batch
ORDER BY generation_batch;
