# Services API frontend

## Objectif

Les appels HTTP du frontend sont centralises dans :

```text
08_FRONTEND/src/services/
```

Les composants React ne doivent pas connaitre les URLs FastAPI en dur. Ils
appellent des fonctions metier simples, par exemple :

```text
uploadExcelFile(file)
getCapexSummary()
getScenarioHistory()
simulateCapex(payload)
getContainerPlan(simulationId)
```

---

## Fichiers principaux

| Fichier | Role |
|---|---|
| `apiClient.js` | Client Axios commun, base URL, erreurs |
| `dashboardService.js` | Donnees cockpit, CAPEX, fact_metre, monitoring |
| `excelUploadService.js` | Upload Excel DQE et synchronisation |
| `simulationService.js` | Simulation CAPEX |
| `scenarioService.js` | Scenarios et comparaison |
| `decisionService.js` | DecisionEngine |
| `procurementService.js` | Procurement analytics |
| `logisticsService.js` | Logistics analytics |

---

## `apiClient.js`

Responsabilites :

- choisir l'URL backend ;
- configurer Axios ;
- appliquer un timeout adapte aux uploads volumineux ;
- normaliser les erreurs ;
- journaliser temporairement les reponses utiles.

URL backend :

```text
local      -> http://localhost:8000
production -> https://sp2i-backend.onrender.com
override   -> VITE_API_URL
```

Erreur reseau :

```text
Connexion interrompue sur /endpoint.
```

Erreur HTTP backend :

```text
detail/message/error renvoye par FastAPI
```

---

## Services DQE

Endpoints utilises :

| Fonction frontend | Endpoint |
|---|---|
| `uploadExcelFile` | `POST /api/upload/excel` |
| `syncExcelFile` | `POST /api/upload/excel/sync` |
| `uploadDqe` | `POST /dqe/upload` |
| `extractDqe` | `POST /dqe/extract` |

Mapping important pour l'upload IA :

```text
data.ai_preview.quality_score
data.ai_preview.lots_detected
data.ai_preview.recognized_columns
data.ai_preview.estimated_capex_detected
data.lignes_normalisees_preview
data.ai_anomalies
data.analyses
data.ai_suggestions
```

Validation succes :

```javascript
if (data.status !== "SUCCESS") {
  throw new Error(data.message || "Erreur analyse DQE");
}
```

---

## Services cockpit

`dashboardService.js` appelle :

| Fonction | Endpoint | Usage |
|---|---|---|
| `getCapexSummary` | `/capex/summary` | KPI CAPEX rapides |
| `getFactMetre` | `/fact_metre` | Table analytique |
| `getMonitoringStatus` | `/monitoring/status` | Etat API |
| `getScenarioHistory` | `/simulation/scenarios` | Scenarios recents |

Ces endpoints historiques restent utiles pour la compatibilite. Les nouveaux
dashboards doivent progressivement basculer vers `/analytics/*`.

---

## Services Analytics Engine

Endpoints cibles :

```text
/analytics/dashboard
/analytics/kpis
/analytics/capex
/analytics/risk
/analytics/procurement
/analytics/logistics
/analytics/scenarios
/analytics/heatmap
/analytics/drilldown
/analytics/timeline
/analytics/system-health
/analytics/query-performance
/analytics/cache-status
```

Tous retournent :

```json
{
  "status": "SUCCESS",
  "filters": {},
  "pagination": {},
  "kpis": {},
  "charts": {},
  "table": [],
  "metadata": {}
}
```

---

## Services metier

| Domaine | Endpoints |
|---|---|
| Simulation | `/simulation/simulate`, `/simulation/scenarios`, `/simulation/compare` |
| Decision | `/decision/rules`, `/decision/explain/{id}`, `/decision/risk-analysis/{id}` |
| Procurement | `/procurement/risk-analysis/{id}`, `/procurement/lead-time/{id}`, `/procurement/cashflow/{id}` |
| Logistics | `/logistics/container-plan/{id}`, `/logistics/shipment-analysis/{id}`, `/logistics/freight-cost/{id}` |

---

## Bonnes pratiques

1. Ne pas faire de `axios.get()` directement dans une page.
2. Ne pas coder l'URL Render dans un composant.
3. Ne pas supposer que `success=true` existe : le backend utilise souvent `status`.
4. Toujours gerer `status !== "SUCCESS"` proprement.
5. Conserver les fallbacks UI quand la base PostgreSQL est vide.
6. Utiliser React Query pour les donnees dashboard.
7. Utiliser Zustand pour les filtres globaux, pas des states disperses.
8. Garder les logs `API RESPONSE` le temps de stabiliser la production, puis les reduire.
