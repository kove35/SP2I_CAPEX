# HVAC Procurement Review + Energy Governance

Source:

`MASTER_REFERENCE_HVAC.xlsx`

Famille traitee: **HVAC uniquement**.

## Objectif

Cette phase ajoute la revue procurement HVAC, la validation technique HVAC, la gouvernance energie, la separation fourniture/installation, le drift HVAC et une preparation TCO.

Elle ne modifie pas:

- les routes FastAPI
- le frontend React
- Power BI
- AG Grid
- `MASTER_REFERENCE_ENTERPRISE`
- la famille `ELECTRICITE`

## Livrables

- `HVAC_SUPPLIER_REGISTRY.xlsx`
- `HVAC_ENERGY_GOVERNANCE.xlsx`
- `HVAC_TCO_ANALYSIS.xlsx`
- `HVAC_FOB_VALIDATION.xlsx`
- `HVAC_PROCUREMENT_REVIEW.xlsx`
- `HVAC_DRIFT_GOVERNANCE.xlsx`
- `HVAC_LOW_CONFIDENCE_REFERENCES.xlsx`
- `HVAC_GOVERNANCE_V2_STATS.json`

Commande reproductible:

```powershell
.venv\Scripts\python.exe devtools\build_hvac_governance_v2.py
```

## Fournisseurs HVAC

`HVAC_SUPPLIER_REGISTRY.xlsx` contient:

- `SUPPLIER_ID`
- `SUPPLIER_NAME`
- `BRAND`
- `COUNTRY`
- `PRODUCT_TYPES`
- `MOQ`
- `FOB_MIN`
- `FOB_MAX`
- `LEAD_TIME_DAYS`
- `SUPPLIER_CONFIDENCE`
- `VERIFIED`
- `LAST_MARKET_CHECK`
- `VALIDATION_STATUS`

Les fournisseurs restent des candidats non verifies. Aucun `HIGH` ne peut etre produit tant que `VERIFIED = FALSE`.

## Validation technique

La validation HVAC controle:

- BTU
- CV / HP
- KW
- COP estime
- inverter
- VRV / VRF
- puissance reelle estimee
- ratio puissance/prix

Statuts:

- `VERIFIED`
- `PARTIAL`
- `REJECTED`

## Energy governance

`ENERGY_RISK_SCORE` utilise:

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

Le score prend en compte:

- puissance estimee
- COP estime
- technologie inverter
- type HVAC
- consommation annuelle estimee

## Fourniture vs installation

Classification:

- `FOURNITURE_HVAC`: importable possible
- `INSTALLATION_HVAC`: non importable
- `MIXED_HVAC`: fourniture + installation, revue obligatoire

Les lignes mixtes ne doivent pas produire de decision import automatique.

## Drift HVAC

`HVAC_DRIFT_ALERT_LEVEL` utilise:

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

Facteurs surveilles:

- cuivre
- fret maritime
- energie
- gaz refrigerant
- saison
- inflation import

## TCO HVAC

`HVAC_TCO_ANALYSIS.xlsx` prepare:

- cout achat
- cout energie 10 ans
- cout maintenance 10 ans
- cout installation
- `TOTAL_COST_OF_OWNERSHIP`

Cette couche n'est pas encore exposee au cockpit.

## Resultat HVAC V2

References HVAC: 8.

Fournisseurs candidats: 3.

Fournisseurs verifies: 0.

Confiance:

- `MEDIUM`: 4
- `LOW`: 4
- `HIGH`: 0

Risque energie:

- `HIGH`: 5
- `LOW`: 3

Validation technique:

- `VERIFIED`: 1
- `PARTIAL`: 7

FOB:

- `PARTIAL`: 5
- `REJECTED`: 3

Drift:

- `CRITICAL`: 4
- `HIGH`: 1
- `MEDIUM`: 3

## Decision

Statut: **HVAC gouvernance renforcee, integration master toujours bloquee**.

Prochaine action:

1. verifier fournisseurs HVAC reels
2. confirmer FOB par famille HVAC
3. valider puissances et COP
4. separer les lignes mixtes fourniture/installation
5. reduire drift cuivre/fret/energie avant integration
