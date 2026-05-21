# Procurement Governance V2

Source de travail:

`MASTER_REFERENCE_ENTERPRISE.xlsx`

Phase active: **ELECTRICITE** uniquement.

## Objectif

Cette phase ajoute une couche de gouvernance procurement et benchmark au `MASTER_REFERENCE_ENTERPRISE` existant, sans nouveau moteur backend, sans route API, sans modification frontend et sans impact Power BI/AG Grid.

## Livrables

- `MASTER_REFERENCE_GOVERNANCE_V2.xlsx`
- `PROCUREMENT_VALIDATION_AUDIT.xlsx`
- `BENCHMARK_DRIFT_AUDIT.xlsx`
- `TOP_LOW_CONFIDENCE_SUPPLIERS.xlsx`
- `MARKET_DRIFT_ANALYSIS.xlsx`
- `PROCUREMENT_GOVERNANCE_STATS.json`

Commande reproductible:

```powershell
.venv\Scripts\python.exe devtools\build_procurement_governance_v2.py
```

## Colonnes ajoutees

Gouvernance fournisseur:

- `SUPPLIER_VERIFIED`
- `FOB_VERIFIED`
- `LAST_MARKET_CHECK`
- `LOCAL_BENCHMARK_CONFIRMED`
- `PROCUREMENT_VALIDATED_BY`
- `VALIDATION_STATUS`

Gouvernance benchmark:

- `BENCHMARK_SOURCE`
- `BENCHMARK_CONFIDENCE`
- `LAST_BENCHMARK_UPDATE`
- `MARKET_REGION`
- `PRICE_VARIATION_LEVEL`

Confiance et cockpit:

- `PROCUREMENT_REVIEW_REQUIRED`
- `MARKET_DRIFT_SCORE`
- `COCKPIT_CONFIDENCE_BADGE`
- `COCKPIT_WARNING`

## Statuts officiels

Pour la validation procurement:

- `PENDING`
- `PARTIAL`
- `VERIFIED`
- `REJECTED`

Pour la confiance:

- `HIGH`
- `MEDIUM`
- `LOW`

Le niveau `HIGH` est volontairement strict. Il exige:

- fournisseur valide
- FOB valide
- benchmark local confirme
- coherence financiere
- taxonomie stable
- procurement stable

## Resultat phase ELECTRICITE

References traitees: 65.

Validation:

- `PARTIAL`: 65
- `VERIFIED`: 0
- `PENDING`: 0
- `REJECTED`: 0

Confiance:

- `MEDIUM`: 28
- `LOW`: 37
- `HIGH`: 0

Review procurement:

- `PROCUREMENT_REVIEW_REQUIRED = YES`: 65

Drift marche:

- score moyen: 86.52
- references avec derive critique: 57

## Interpretation

Le resultat est volontairement conservateur. La phase 1 a stabilise la taxonomie et la reference. La phase 2 empeche maintenant le cockpit et le procurement de transformer des donnees non verifiees en decisions automatiques.

Les fournisseurs Chine restent majoritairement non verifies (`A_VERIFIER_GOUVERNANCE`), donc:

- aucun `HIGH` n'est attribue
- les ROI doivent rester visuellement degrades
- les decisions import doivent rester en revue procurement
- les benchmarks a forte variation doivent remonter en warning

## Degradation cockpit preparee

Le frontend pourra utiliser directement:

- `COCKPIT_CONFIDENCE_BADGE = RED_CRITICAL`
- `COCKPIT_CONFIDENCE_BADGE = ORANGE_REVIEW`
- `COCKPIT_CONFIDENCE_BADGE = GREEN_VERIFIED`

Sans changer le contrat metier:

- `LOW` -> badge rouge, ROI degrade, review obligatoire
- `MEDIUM` -> badge orange, validation requise
- `HIGH` -> badge vert, reference decisionnelle

## Prochaine etape

Avant de passer `ELECTRICITE` en confiance enterprise:

1. verifier les fournisseurs Chine reels
2. confirmer les FOB par source marche
3. confirmer les prix locaux Congo Brazzaville
4. reduire les variations benchmark extremes
5. passer les references validees de `PARTIAL` a `VERIFIED`

Ensuite seulement, poursuivre la famille **HVAC**.
