# Plomberie Procurement Review + Water Governance

Source unique:

`03_DONNEES_REFERENCE/DQE_PROJECT_SP2I.xlsx`, onglet `DQE_CLEAN`.

Famille traitee: **PLOMBERIE uniquement**.

## Objectif

Creer un pipeline de validation gouvernee plomberie avant toute integration dans `MASTER_REFERENCE_ENTERPRISE`.

Cette phase ne modifie pas:

- ELECTRICITE
- HVAC
- MASTER_REFERENCE_ENTERPRISE
- les routes FastAPI
- le frontend React
- Power BI
- AG Grid

## Livrables

- `DQE_PLOMBERIE_TEST.xlsx`
- `MASTER_REFERENCE_PLOMBERIE.xlsx`
- `PLOMBERIE_SUPPLIER_REGISTRY.xlsx`
- `PLOMBERIE_PROCUREMENT_AUDIT.xlsx`
- `PLOMBERIE_DRIFT_ANALYSIS.xlsx`
- `PLOMBERIE_TCO_ANALYSIS.xlsx`
- `PLOMBERIE_WATER_GOVERNANCE.xlsx`
- `PLOMBERIE_LOW_CONFIDENCE_REFERENCES.xlsx`
- `PLOMBERIE_VALIDATION_STATS.json`

Commande reproductible:

```powershell
.venv\Scripts\python.exe devtools\build_plomberie_governance.py
```

## Extraction plomberie

Les lignes sont detectees via:

- alimentation eau
- evacuation
- PVC
- PER
- cuivre
- multicouche
- sanitaire
- robinetterie
- vannes
- pompes
- surpresseurs
- chauffe-eau
- tuyauterie
- accessoires plomberie
- regards
- siphons
- collecteurs

## Champs ajoutes

- `DIAMETRE`
- `UNITE_DIAMETRE`
- `PRESSION_SERVICE`
- `TYPE_RESEAU`
- `MATERIAU`
- `TYPE_EQUIPEMENT`
- `MARQUE_REFERENCE`

## Validation technique

Le pipeline detecte:

- diametres manquants ou incoherents
- pressions manquantes ou incoherentes
- materiaux non detectes
- incompatibilites materiau/usage
- faux equipements
- faux reseaux

## Water governance

`WATER_RISK_SCORE` utilise:

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

Le score prend en compte:

- pression
- qualite materiau
- corrosion
- maintenance
- risque fuite
- disponibilite locale
- contexte reseau Afrique centrale

## Fourniture vs installation

Classification:

- `FOURNITURE_PLOMBERIE`: importable possible
- `INSTALLATION_PLOMBERIE`: non importable
- `MIXED_PLOMBERIE`: ligne mixte, revue obligatoire

## Decision blockers

`DECISION_BLOCKER` utilise:

- `NONE`
- `REVIEW_REQUIRED`
- `BLOCK_IMPORT`
- `HIGH_RISK`
- `TECHNICAL_VALIDATION_REQUIRED`

## Resultat initial

Lignes plomberie extraites: 121.

References master plomberie: 121.

Fournisseurs candidats: 3.

Confiance:

- `MEDIUM`: 41
- `LOW`: 80
- `HIGH`: 0

Water risk:

- `LOW`: 9
- `MEDIUM`: 39
- `HIGH`: 73

Validation technique:

- `VERIFIED`: 9
- `PARTIAL`: 99
- `REJECTED`: 13

Drift:

- `HIGH`: 82
- `MEDIUM`: 39

Decision blockers:

- `BLOCK_IMPORT`: 77
- `REVIEW_REQUIRED`: 40
- `TECHNICAL_VALIDATION_REQUIRED`: 3
- `HIGH_RISK`: 1

## Decision

Statut: **PLOMBERIE prete pour revue gouvernance, non integrable directement**.

Le volume de lignes mixtes/installation est important. La priorite est de separer fourniture et pose, confirmer les materiaux/diametres, puis valider les benchmarks locaux avant toute integration enterprise.
