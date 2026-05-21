# HVAC Governance Test

Source unique:

`03_DONNEES_REFERENCE/DQE_PROJECT_SP2I.xlsx`, onglet `DQE_CLEAN`.

Famille testee: **HVAC uniquement**.

## Objectif

Ce pipeline valide la famille HVAC avant integration progressive dans `MASTER_REFERENCE_ENTERPRISE`.

Il ne modifie pas:

- les routes FastAPI
- le frontend React
- Power BI
- AG Grid
- le master ELECTRICITE
- l'architecture backend

## Livrables

- `DQE_HVAC_TEST.xlsx`
- `MASTER_REFERENCE_HVAC.xlsx`
- `HVAC_BENCHMARKS.xlsx`
- `HVAC_PROCUREMENT_AUDIT.xlsx`
- `HVAC_DRIFT_ANALYSIS.xlsx`
- `HVAC_CONFIDENCE_AUDIT.xlsx`
- `HVAC_VALIDATION_STATS.json`

Commande reproductible:

```powershell
.venv\Scripts\python.exe devtools\build_hvac_validation.py
```

## Extraction HVAC

Les lignes HVAC sont detectees via:

- split mural
- cassette
- gainable
- VRV / VRF
- ventilation
- extraction
- climatisation
- cuivre frigorifique
- conduits / gaines
- isolation thermique
- thermostats
- CTA
- BTU

## Champs HVAC ajoutes

`DQE_HVAC_TEST.xlsx` ajoute:

- `PUISSANCE`
- `UNITE_PUISSANCE`
- `TYPE_HVAC`
- `TECHNOLOGIE`
- `MARQUE_REFERENCE`

## Benchmarks

Regions produites:

- Congo Brazzaville
- Cameroun
- Gabon
- Afrique centrale

Qualite: `MEDIUM` uniquement.

Les types HVAC couverts:

- `SPLIT_MURAL`
- `CASSETTE`
- `GAINABLE`
- `VRV_VRF`
- `VENTILATION`
- `EXTRACTION`
- `CUIVRE_FRIGORIFIQUE`
- `CONDUITS`
- `ISOLATION_THERMIQUE`
- `THERMOSTATS`
- `HVAC_GENERAL`

## Procurement

La validation procurement HVAC reste stricte:

- fournisseur Chine marque `A_VERIFIER_GOUVERNANCE_HVAC`
- `SUPPLIER_VERIFIED = FALSE`
- `PROCUREMENT_REVIEW_REQUIRED = YES`
- pas de `HIGH` sans fournisseur, FOB, benchmark et drift valides

## Resultat du test

Lignes HVAC extraites: 8.

References master HVAC: 8.

Benchmarks regionaux: 32.

Confidence:

- `MEDIUM`: 3
- `LOW`: 5
- `HIGH`: 0

Drift:

- `CRITICAL`: 3
- `HIGH`: 2
- `MEDIUM`: 3

Review procurement:

- 8 references sur 8 demandent une revue procurement.

## Decision

Statut: **HVAC pret pour revue gouvernance**, pas encore pret pour integration directe au master enterprise.

Prochaine action:

1. verifier les fournisseurs HVAC reels
2. confirmer FOB par type HVAC
3. confirmer benchmark local Congo/Cameroun/Gabon
4. reduire les lignes `LOW`
5. integrer uniquement les references `MEDIUM` stabilisees ou `HIGH` validees
