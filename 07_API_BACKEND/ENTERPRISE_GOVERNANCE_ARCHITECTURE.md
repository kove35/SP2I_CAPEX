# Enterprise Governance Architecture

## Objectif

Ce document formalise la couche backend de gouvernance enterprise pour la simulation CAPEX.
L'objectif est d'ajouter :

- un registre centralise de parametres et de scores (`parameter_registry_engine.py`)
- une piste d'audit operationnelle pour chaque ligne de simulation (`audit_trail_engine.py`)
- une couche d'explicabilite structurée pour la prise de decision (`explainability_engine.py`)
- un moteur de persistence de scenarios et d'historisation compatible avec l'existant (`scenario_persistence_engine.py`)

> L'architecture doit rester compatible avec les routes existantes et ne pas casser les contrats frontend ni Power BI.

## Principes

1. Backward compatible : les sorties API conservent les champs actuels et ajoutent uniquement des champs optionnels.
2. Modulable : chaque engine reste autonome et spécialisé.
3. Auditabilité : chaque ligne enrichie transporte un profil de decision, une trace de parametres et un jeu de tags.
4. Explainability : les verdicts métier sont traduits en messages compréhensibles par le pilotage.
5. Persistence : la couche scenario reprend les repository existants et n'ajoute pas de tables pour cette phase.

## Composants

### ParameterRegistryEngine

- centralise les paramètres clés de calcul : taux logistiques, seuils de décision, poids de scoring, règles d'importabilité.
- valide et normalise les entrées.
- stocke une version de registre pour traçabilité.
- expose des méthodes de lecture (`get_logistics_rates`, `get_fob_ratio`, `get_parameter`).

### AuditTrailEngine

- construit un « audit trail » par ligne en assemblant :
  - le contexte métier (famille, lot, désignation)
  - les scores intermédiaires
  - les règles et seuils utilisées
  - les tags d'alerte
- produit un dictionnaire stable utilisable pour l'export Power BI ou l'analyse de dérive.

### ExplainabilityEngine

- transforme les résultats de décision en messages actionnables.
- fournit des sous-blocs : direction, procurement, technique, financier.
- permet d'exposer des recommandations structurées sans modifiante majeure du frontend.

### ScenarioPersistenceEngine

- pilote l'historisation des scénarios via les repositories existants.
- gère la création de scénario, la sauvegarde des runs et la lecture des snapshots.
- permet un rollback de scénario niveau lecture.

## Migration sans casse

1. Ajouter les nouveaux modules sans toucher aux routes existantes.
2. Etendre les schémas de réponse avec des champs optionnels.
3. Intégrer l'audit et l'explicabilité dans `ServiceSimulation` après la décision.
4. Utiliser `ScenarioPersistenceEngine` comme wrapper de persistance sans modifier le schéma de base.

## Roadmap

1. Implémentation des engines.
2. Integration dans `ServiceSimulation`.
3. Tests unitaires et end-to-end du flux existant.
4. Documentation et release note.
5. Phase suivante : écran d'administration des paramètres et stockage de versions en base.
