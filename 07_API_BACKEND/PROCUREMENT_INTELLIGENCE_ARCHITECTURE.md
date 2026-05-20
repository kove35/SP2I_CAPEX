# Procurement Intelligence Backend Architecture

## Objectif

Ajouter une couche backend Procurement Intelligence enterprise dans SP2I_CAPEX sans casser l'architecture FastAPI existante. La priorité est de conserver le contrat API actuel, les modèles existants et la compatibilité Power BI, tout en renforçant :

- sourcing coverage intelligent
- confidence scoring
- hidden savings potential
- container optimization
- multi-lot optimization
- decision scoring
- scénarios dynamiques
- KPI enterprise procurement

## Architecture cible

```text
app/routes/simulation.py
    -> ServiceSimulation
        -> DataCleaner
        -> CalculateurCAPEX
        -> ProcurementEnrichmentEngine
        -> LogisticsEngine
        -> DecisionEngineV2
        -> KPIEngine

app/core/
    procurement_enrichment_engine.py
    decision_engine_v2.py
    scenario_engine.py
    kpi_engine.py
```

## Rôle des nouveaux modules

- `ProcurementEnrichmentEngine` : enrichit chaque ligne CAPEX avec des signaux procurement approfondis et auditables.
- `DecisionEngineV2` : prend les résultats financiers existants, ajoute l'importability et la maturité procurement, puis produit une décision scenario-aware.
- `ScenarioEngine` : expose la génération de scénarios avancés pour landed cost et décision procurement.
- `KPIEngine` : calcule des KPI enterprise procurement supplémentaires compatibles Power BI.

## Intégration non invasive

- Les routes `/simulation/simulate` et `/simulation/scenarios` restent inchangées.
- Le contrat `SimulationResponse` conserve ses champs actuels et gagne des champs optionnels non obligatoires.
- `ServiceSimulation` reste la façade publique, mais délègue l'enrichissement procurement et la décision au nouvel ensemble de modules.
- Les calculs historiques et la persistence PostgreSQL utilisent toujours les champs existants, avec des clés d'analyse JSON enrichies.

## Pseudo-code de l'orchestration

```python
class ServiceSimulation:
    def _simuler_lignes(...):
        lignes_normalisees = cleaner.normaliser_lignes(lignes_entree)
        lignes_calculees = calculateur.optimiser_lignes(lignes_normalisees)
        lignes_calculees = [procurement_enrichment_engine.enrich_line(ligne) for ligne in lignes_calculees]
        lignes_calculees = [logistics_engine.enrich_line(ligne) for ligne in lignes_calculees]
        lignes_calculees = [decision_engine_v2.enrich_line(ligne) for ligne in lignes_calculees]
        kpi = calculateur.calculer_kpi(lignes_calculees)
        kpi['procurement'] = kpi_engine.compute_procurement_kpi(lignes_calculees)
        return response
```

## Historique & auditabilité

Chaque ligne garde un `PROCUREMENT_ANALYSIS` détaillé. Le moteur produit des scores facilement traçables :

- `SOURCING_COVERAGE`
- `IMPORT_CONFIDENCE_SCORE`
- `SUPPLIER_MATURITY_SCORE`
- `PROCUREMENT_MATURITY_SCORE`
- `IMPORTABILITY_SCORE`
- `HIDDEN_SAVINGS_POTENTIAL`
- `PROCUREMENT_SCORE`
- `DECISION_SCENARIO`

## Points d'intégration Power BI

1. Enrichir le modèle `fact_simulation` plus tard avec les nouveaux scores JSON si nécessaire.
2. Préserver les colonnes `capex_local`, `capex_import`, `capex_optimise`, `decision_score`, `global_risk_score`, `lead_time_days`, `cashflow_score`.
3. Exposer un champ `kpi.procurement` via l'API pour les tableaux de bord executive et procurement.
4. Ajouter des mesures DAX pour :
   - `POTENTIEL_CACHE`
   - `TAUX_COUVERTURE_SOURCING`
   - `TAUX_IMPORTABILITE`
   - `SCORE_PROCUREMENT`
   - `DEPENDANCE_IMPORT`

## Stratégie de migration sans casse

1. Commencer par déployer les modules internes sans supprimer l'ancien `DecisionEngine`.
2. Valider que `procurement_analysis` et `decision_reason` sont enrichis, sans changer la structure API de base.
3. Ajouter des tests unitaires ciblés sur les nouveaux moteurs.
4. Piloter l'adoption dans Power BI sur de nouvelles colonnes optionnelles avant de migrer les dashboards existants.
