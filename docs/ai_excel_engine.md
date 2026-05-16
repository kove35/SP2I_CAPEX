# Moteur IA Excel SP2I

## Vision

Le moteur IA Excel transforme SP2I d'un parser Excel classique vers un moteur
hybride d'analyse documentaire metier. Il ne remplace pas les regles metier :
il les complete quand les fichiers sont ambigus, heterogenes ou mal structures.

Flux cible :

```text
Excel Upload
-> Excel Analyzer
-> Heuristics Engine
-> AI Interpretation Layer
-> Normalization Engine
-> Human Validation
-> Simulation Engine
-> PostgreSQL
-> Power BI
```

## Principe fondamental

L'IA assiste, mais ne devient jamais source de verite.

Elle peut :

- classifier un fichier
- proposer un mapping
- detecter des lignes DQE
- identifier des anomalies
- expliquer ses choix
- scorer sa confiance

Elle ne peut pas :

- calculer le CAPEX critique
- arbitrer seule une decision
- synchroniser PostgreSQL sans validation humaine
- remplacer les controles metier

## Modules crees

```text
app/core/ai/
    ai_excel_orchestrator.py
    ai_excel_classifier.py
    ai_column_mapper.py
    ai_dqe_parser.py
    ai_family_mapper.py
    ai_anomaly_detector.py
    ai_preview_generator.py
    ai_confidence_engine.py
    ai_prompt_templates.py
    ai_file_store.py
```

## Orchestrateur

`AIExcelOrchestrator` applique l'ordre suivant :

1. regles deterministes
2. heuristiques metier
3. fuzzy matching
4. fallback IA future si la confiance reste faible

Cette architecture garde le systeme explicable et testable.

## Sortie enrichie

La reponse `/api/upload/excel` contient maintenant :

```json
{
  "file_id": "...",
  "ai_preview": {},
  "ai_confidence": {},
  "ai_anomalies": [],
  "ai_classified_rows": [],
  "ai_suggestions": {}
}
```

`file_id` sert aux endpoints de consultation et validation humaine.

