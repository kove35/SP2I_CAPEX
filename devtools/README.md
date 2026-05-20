# DEVTOOLS SP2I_CAPEX

Infrastructure de diagnostics backend robuste pour Windows, PowerShell, Continue et Codex.

Regle absolue: ne jamais lancer de Python multi-lignes avec `python.exe -c "..."`.
Toujours creer un fichier `.py` dans `devtools/`, puis l'executer avec le Python du venv.

## Commandes PowerShell

```powershell
.venv\Scripts\python.exe devtools\validate_imports.py
.venv\Scripts\python.exe devtools\debug_repositories.py
.venv\Scripts\python.exe devtools\validate_routes.py
.venv\Scripts\python.exe devtools\smoke_test_simulation.py
.venv\Scripts\python.exe devtools\check_project_health.py
.venv\Scripts\python.exe devtools\diagnostics_report.py
.venv\Scripts\python.exe devtools\debug_procurement.py
.venv\Scripts\python.exe devtools\debug_kpi_engine.py
.venv\Scripts\python.exe devtools\debug_scenarios.py
.venv\Scripts\python.exe devtools\validate_powerbi_payloads.py
```

## Role des scripts

- `validate_imports.py`: compile les fichiers Python, importe les modules backend, detecte les circular imports statiques et les packages sans `__init__.py`.
- `debug_repositories.py`: valide `app.repositories`, liste les repositories et expose les imports casses avec traceback.
- `validate_routes.py`: charge l'application FastAPI, liste les endpoints, detecte les collisions route/methode et valide les schemas Pydantic.
- `smoke_test_simulation.py`: execute un smoke test lecture seule des moteurs Procurement, DecisionEngineV2, KPI, Explainability, AuditTrail et ScenarioPersistence.
- `check_project_health.py`: calcule un score global imports, routes, KPI, scenarios, procurement, explainability, auditability et Power BI readiness.
- `diagnostics_report.py`: produit un rapport global architecture, routes, engines, dependances, warnings et recommandations.
- `debug_procurement.py`: diagnostic rapide du `ProcurementEnrichmentEngine`.
- `debug_kpi_engine.py`: diagnostic rapide du `KPIEngine`.
- `debug_scenarios.py`: detection des engines scenario et validation du contrat `ScenarioPersistenceEngine`.
- `validate_powerbi_payloads.py`: verifie les routes et modules utiles a l'exposition BI sans exposer les secrets.
- `_common.py`: helpers internes partages par les scripts devtools.

## Workflow debugging recommande

1. Lancer les imports:
   ```powershell
   .venv\Scripts\python.exe devtools\validate_imports.py
   ```
2. Lancer les routes:
   ```powershell
   .venv\Scripts\python.exe devtools\validate_routes.py
   ```
3. Lancer le smoke metier:
   ```powershell
   .venv\Scripts\python.exe devtools\smoke_test_simulation.py
   ```
4. Lancer le rapport global:
   ```powershell
   .venv\Scripts\python.exe devtools\diagnostics_report.py
   ```

## Workflow validation backend

```powershell
.venv\Scripts\python.exe devtools\validate_imports.py
.venv\Scripts\python.exe devtools\debug_repositories.py
.venv\Scripts\python.exe devtools\validate_routes.py
.venv\Scripts\python.exe devtools\check_project_health.py
```

## Workflow smoke tests

```powershell
.venv\Scripts\python.exe devtools\smoke_test_simulation.py
.venv\Scripts\python.exe devtools\debug_procurement.py
.venv\Scripts\python.exe devtools\debug_kpi_engine.py
.venv\Scripts\python.exe devtools\debug_scenarios.py
.venv\Scripts\python.exe devtools\validate_powerbi_payloads.py
```

## Bonnes pratiques Continue/Codex

- Demander la creation ou la modification d'un script dans `devtools/` pour tout diagnostic Python non trivial.
- Executer uniquement des fichiers Python dedies depuis PowerShell.
- Garder les scripts lecture seule par defaut.
- Afficher les tracebacks complets et un resume final.
- Preferer des payloads de smoke test en memoire pour eviter toute ecriture DB.

## Erreurs PowerShell a eviter

```powershell
python.exe -c "import app.main
print(app.main.app)"
```

```powershell
.venv\Scripts\python.exe -c "from app.core.kpi_engine import KPIEngine
print(KPIEngine().compute_procurement_kpi([]))"
```

Ces commandes cassent facilement avec les quotes, les retours ligne, l'encodage et Continue/Codex.
La forme stable est:

```powershell
.venv\Scripts\python.exe devtools\<script>.py
```

