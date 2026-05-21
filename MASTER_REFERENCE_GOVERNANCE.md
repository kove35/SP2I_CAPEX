# MASTER_REFERENCE Enterprise Governance

Source unique actuelle:

`03_DONNEES_REFERENCE/DQE_PROJECT_SP2I.xlsx`, onglet `DQE_CLEAN`.

## Statut

Phase active: **ELECTRICITE**.

Le referentiel est volontairement progressif. Les familles suivantes seront traitees dans l'ordre:

1. `ELECTRICITE`
2. `HVAC`
3. `PLOMBERIE`
4. `MENUISERIE`
5. `MEDICAL`

Cette version ne traite donc pas toutes les familles simultanement. Elle construit une base enterprise auditable et extensible, sans modifier les routes API, le cockpit, Power BI ou AG Grid.

## Livrables

- `MASTER_REFERENCE_ENTERPRISE.xlsx`
- `MASTER_REFERENCE_QUALITY_AUDIT.xlsx`
- `BENCHMARK_AFRIQUE_CENTRALE.xlsx`
- `TOP_LOW_CONFIDENCE_REFERENCES.xlsx`
- `MASTER_REFERENCE_ENTERPRISE_STATS.json`

Commande reproductible:

```powershell
.venv\Scripts\python.exe devtools\build_master_reference_enterprise.py
```

## Structure MASTER_REFERENCE

Colonnes produites:

- `REFERENCE_ID`
- `DESIGNATION_NORMALISEE`
- `RAW_DESIGNATION`
- `FAMILLE`
- `SOUS_FAMILLE`
- `TYPE_EQUIPEMENT`
- `UNITE`
- `PRICE_MIN_FCFA`
- `PRICE_MAX_FCFA`
- `PU_CHINE_FOB_FCFA`
- `IMPORTABILITY`
- `RISK_LEVEL`
- `MOQ`
- `INCOTERM`
- `FOURNISSEUR_CHINE`
- `BENCHMARK_REGION`
- `QUALITY_LEVEL`
- `CONFIDENCE_LEVEL`
- `LAST_VALIDATION_DATE`
- `SOURCE_REFERENCE`

## Benchmarks Afrique centrale

Les benchmarks sont produits pour:

- `CONGO_BRAZZAVILLE`
- `CAMEROUN`
- `GABON`
- `CENTRAL_AFRICA`

Qualite: `MEDIUM` uniquement.

Les facteurs regionaux sont appliques en lecture seule sur les references consolidees:

- Congo Brazzaville: 1.08
- Cameroun: 1.03
- Gabon: 1.12
- Afrique centrale: 1.00

## Confidence scoring

`CONFIDENCE_LEVEL` est calcule a partir de:

- score de classification
- statut prix vs benchmark
- nombre d'occurrences source
- coherence importabilite

Regles:

- `HIGH`: prix OK, classification forte, reference observee plusieurs fois
- `MEDIUM`: reference plausible mais validation sourcing/benchmark incomplete
- `LOW`: prix suspect, faible evidence source ou risque financier

## Visual degradation cockpit

La degradation visuelle doit se baser sur les champs existants du referentiel:

- `CONFIDENCE_LEVEL = LOW`: badge rouge, warning benchmark
- `CONFIDENCE_LEVEL = MEDIUM`: badge orange, validation requise
- `RISK_LEVEL = HIGH`: warning procurement et ROI degrade
- `IMPORTABILITY = LOW`: recommendation import bloquee ou fortement degradee
- `PRICE_STATUS` dans `MASTER_REFERENCE_QUALITY_AUDIT.xlsx`: signal de sanity financiere

Cette phase ne modifie pas le frontend. Elle fournit les donnees gouvernees qui permettront au cockpit de degrader les decisions sans changer de contrat API.

## Procurement governance

Les champs governance procurement sont initialises:

- `PU_CHINE_FOB_FCFA`
- `MOQ`
- `INCOTERM`
- `FOURNISSEUR_CHINE`
- `IMPORTABILITY`
- `RISK_LEVEL`

Les fournisseurs Chine restent marques `A_VERIFIER_GOUVERNANCE` tant que le sourcing n'est pas valide par famille/reference. Cela evite les faux fournisseurs, faux FOB et faux ROI import.

## Resultat phase ELECTRICITE

Statistiques generees:

- references master: 65
- lignes qualite: 68
- benchmarks regionaux: 260
- references a faible confiance ou risque non bas: 65

Distribution confiance:

- `HIGH`: 0
- `MEDIUM`: 28
- `LOW`: 37

Distribution risque:

- `LOW`: 7
- `MEDIUM`: 21
- `HIGH`: 37

## Decision

La couche MASTER_REFERENCE est exploitable comme socle de gouvernance, mais pas encore comme base de decision automatique sans degradation visuelle.

Decision: **GO conditionnel gouverne**.

Prochaine action recommandee: valider les references ELECTRICITE en `LOW`, puis passer a `HVAC`.
