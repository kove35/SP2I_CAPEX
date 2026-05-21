# Supplier Governance Phase 3

Source:

`MASTER_REFERENCE_GOVERNANCE_V2.xlsx`

Famille traitee: **ELECTRICITE** uniquement.

## Objectif

La phase 3 ajoute la validation fournisseur progressive au-dessus du master gouverne V2. Elle ne cree pas de moteur backend, ne modifie pas les routes FastAPI, ne modifie pas le frontend, et ne change pas Power BI ou AG Grid.

Le principe reste volontairement prudent:

**aucune reference ne devient HIGH sans validation reelle fournisseur + FOB + benchmark local + stabilite procurement.**

## Livrables

- `SUPPLIER_REFERENCE_REGISTRY.xlsx`
- `VERIFIED_PROCUREMENT_REFERENCES.xlsx`
- `FOB_VALIDATION_AUDIT.xlsx`
- `LOCAL_MARKET_VALIDATION.xlsx`
- `TOP_CRITICAL_DRIFT_REFERENCES.xlsx`
- `PROCUREMENT_CONFIDENCE_EVOLUTION.xlsx`
- `SUPPLIER_GOVERNANCE_STATS.json`

Commande reproductible:

```powershell
.venv\Scripts\python.exe devtools\build_supplier_governance_phase3.py
```

## Referentiel fournisseurs

`SUPPLIER_REFERENCE_REGISTRY.xlsx` contient les champs:

- `SUPPLIER_ID`
- `SUPPLIER_NAME`
- `COUNTRY`
- `CITY`
- `PRODUCT_FAMILIES`
- `MOQ`
- `FOB_RANGE_MIN`
- `FOB_RANGE_MAX`
- `INCOTERM`
- `LEAD_TIME_DAYS`
- `SUPPLIER_CONFIDENCE`
- `VERIFIED`
- `LAST_MARKET_CHECK`
- `LAST_VALIDATION_DATE`
- `VALIDATED_BY`
- `NOTES`

Les fournisseurs initiaux sont des candidats de gouvernance. Ils sont volontairement `VERIFIED = FALSE` tant qu'une validation humaine n'a pas confirme leur existence, leur documentation commerciale, leurs FOB, MOQ et delais.

## Validation FOB

`FOB_VALIDATION_STATUS` utilise:

- `UNVERIFIED`
- `PARTIAL`
- `VERIFIED`
- `REJECTED`

Un FOB reste `PARTIAL` si le range semble plausible mais que le fournisseur n'est pas verifie humainement.

## Validation marche local

`LOCAL_MARKET_VALIDATION_STATUS` utilise:

- `VERIFIED`
- `PARTIAL`
- `REJECTED`

Les benchmarks sont rejetes ou degrades si la variation prix ou la derive marche est trop forte.

## Drift governance

`DRIFT_ALERT_LEVEL` utilise:

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

Les facteurs surveilles sont:

- inflation
- variation USD
- variation fret maritime
- variation cuivre
- variation energie
- variation sourcing Chine

Dans cette phase, le drift est mesure par volatilite prix + confiance + risque de reference. Cela prepare le monitoring marche sans automatiser une decision commerciale.

## Badges cockpit prepares

`COCKPIT_CONFIDENCE_BADGE`:

- `GREEN` pour `HIGH`
- `ORANGE` pour `MEDIUM`
- `RED` pour `LOW`

Le frontend n'est pas modifie. Ces champs preparent la degradation visuelle future.

## Resultat phase 3

References traitees: 65.

Fournisseurs:

- fournisseurs candidats: 3
- fournisseurs verifies: 0

Confiance apres validation:

- `HIGH`: 0
- `MEDIUM`: 5
- `LOW`: 60

FOB:

- `PARTIAL`: 17
- `UNVERIFIED`: 48

Marche local:

- `VERIFIED`: 4
- `PARTIAL`: 14
- `REJECTED`: 47

Drift:

- `CRITICAL`: 47
- `HIGH`: 13
- `MEDIUM`: 4
- `LOW`: 1

## Conclusion

La phase 3 verrouille la credibilite procurement: le systeme refuse de monter artificiellement les references en `HIGH`.

Statut: **GO gouvernance stricte**, avec validation humaine requise avant decision procurement automatique.

Prochaine action: verifier reellement les fournisseurs et FOB des references ELECTRICITE a plus fort impact, puis reduire progressivement les `LOW`.
