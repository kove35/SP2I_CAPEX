# Alignement terminologique KPI SP2I

## Sources et périmètres
- **DQE actif** : version importée et certifiée, source de vérité métier pour le référentiel.
- **FACT_METRE** : base synchronisée exploitable en base projet, utilisée comme mesure de cohérence opérationnelle.
- **Scénario actif** : périmètre simulé courant, issu des hypothèses CAPEX et des arbitrages.

## Mapping UI
- Les KPI de source DQE affichent explicitement "DQE actif".
- Les KPI issus de la base synchronisée affichent "Lignes analysées" ou "FACT_METRE".
- Les KPI de simulation affichent "Lignes scénario" pour éviter l’ambiguïté avec le DQE source.
- La carte de traçabilité doit exposer les écarts ligne / CAPEX et le statut de cohérence.
