# AI Confidence Engine

## Objectif

Tous les resultats IA doivent etre scores et auditables.

## Scores produits

```json
{
  "global_confidence": 0.82,
  "mapping_quality": 0.91,
  "structure_quality": 0.74,
  "data_quality": 0.88,
  "needs_human_validation": true
}
```

## Calcul

Le score global combine :

- qualite mapping
- qualite structure DQE
- qualite donnees
- score feuille DQE

## Regle metier

Si le score est inferieur a 82% ou si des anomalies existent, la validation
humaine est recommandee.

