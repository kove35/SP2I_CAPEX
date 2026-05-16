# Services API frontend

Les appels HTTP sont centralises dans :

```text
08_FRONTEND/src/services/
```

## Fichiers

```text
apiClient.js
simulationService.js
decisionService.js
procurementService.js
logisticsService.js
scenarioService.js
```

## Role

`apiClient.js` configure Axios :

```text
baseURL
timeout
normalisation erreurs
```

Les autres services exposent des fonctions metier reutilisables par les pages.

## Pourquoi

Centraliser les appels API evite de disperser les URLs FastAPI dans les
composants React. Les pages restent lisibles et plus faciles a maintenir.
