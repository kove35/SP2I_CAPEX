# CAPEX Knowledge & Financial Intelligence Engine

## Objectif

Le moteur ajoute une couche enterprise de connaissance CAPEX pour immobilier/BTP en Afrique centrale. Il classifie les equipements, normalise les designations fournisseurs, compare les prix a des ranges realistes FCFA et produit des signaux auditables pour procurement, ROI, Power BI et controle qualite.

## Architecture metier

- `SemanticNormalizationEngine`: nettoyage OCR, synonymes, abreviations, extraction d'attributs comme kVA, kW, mm2, m2, litres et BTU.
- `CAPEXTaxonomyEngine`: classification hierarchique famille, sous-famille, type equipement, classe equipement.
- `EquipmentClassificationEngine`: orchestration taxonomie + reference financiere + score procurement.
- `FinancialReferenceEngine`: application des ranges par region et qualite.
- `AnomalyDetectionEngine`: detection prix, zeros perdus, ROI aberrant, Z-Score, IQR et benchmarks.
- `FinancialSanityEngine`: validation globale ligne par ligne avec explainability et payload Power BI.
- `PriceReferenceRepository`: chargement JSON lecture seule.

## Taxonomie

Structure:

```text
FAMILLE
  -> SOUS_FAMILLE
      -> TYPE_EQUIPEMENT
          -> CLASSE_EQUIPEMENT
```

Les taxonomies sont stockees dans `app/core/capex_taxonomy/*_taxonomy.json` et couvrent electricite, plomberie, HVAC, menuiserie alu, menuiserie bois, revetements, gros oeuvre, VRD, medical, securite, ascenseurs, cuisine professionnelle, mobilier, reseaux IT, energie solaire, hydraulique, facade, charpente, etancheite et amenagements exterieurs.

## References financieres

Les ranges sont stockes dans `app/core/financial_ranges/*_medium.json`.

Chaque reference contient:

- `price_min`
- `price_max`
- `currency`
- `quality`
- `region`
- `importability`
- `logistic_weight`

Les niveaux de qualite sont `LOW_COST`, `MEDIUM`, `PREMIUM`. Les regions supportees par le moteur sont `CONGO_BRAZZAVILLE`, `CENTRAL_AFRICA`, `WEST_AFRICA`, `IMPORT_CHINA`.

## Logique scoring

- `semantic_confidence_score`: qualite de classification semantique.
- `normalization_confidence_score`: qualite du nettoyage et de l'extraction d'attributs.
- `financial_confidence_score`: coherence du prix avec le referentiel.
- `anomaly_score`: severite cumulee des anomalies detectees.
- `procurement_confidence_score`: robustesse du couple classification + reference.

## Logique anomalies

Le moteur detecte:

- prix anormalement bas ou eleves
- zeros perdus
- prix nul ou negatif
- quantite invalide
- ROI aberrant
- outliers Z-Score et IQR
- incoherences benchmark famille/equipement

## Integration Power BI

`FinancialSanityEngine.validate_line()` retourne un bloc `powerbi` pret a exposer:

- famille
- sous-famille
- type equipement
- financial confidence score
- anomaly score
- heatmap bucket

Ce payload alimente les heatmaps d'anomalies, dashboards de qualite procurement, benchmarks categorie et controle ROI.

## Strategie Afrique centrale

Les ranges medium sont calibres en FCFA pour une qualite moyenne professionnelle, tenant compte des contraintes Congo Brazzaville et Afrique centrale: importabilite, poids logistique, disponibilite locale, equipements lourds, medical, HVAC et energie.

## Roadmap evolution

1. Ajouter versionnement des ranges par date et source.
2. Connecter les references a PostgreSQL pour overrides client.
3. Ajouter un feedback loop depuis les achats reels.
4. Exposer des vues BI dediees aux anomalies et benchmarks.
5. Etendre les modeles a la granularite marque, pays fournisseur et incoterm.
