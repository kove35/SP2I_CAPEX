# Documentation SP2I

Ce fichier sert de point d'entree pour la documentation du projet.

SP2I contient beaucoup de briques : frontend React, backend FastAPI, PostgreSQL,
Power BI, moteur IA DQE, simulation CAPEX, procurement, logistique et analytics.
L'objectif de cet index est d'indiquer quel document lire selon le besoin.

---

## Lecture rapide

Pour comprendre le projet en 20 minutes :

1. `../README.md`
2. `frontend_architecture.md`
3. `frontend_backend_flow.md`
4. `api_services.md`
5. `analytics_engine_v1.md`
6. `cloud_readiness_audit.md`

---

## Architecture globale

| Document | Role |
|---|---|
| `architecture_simulation.md` | Explique le moteur CAPEX stabilise |
| `architecture_scenarios.md` | Explique l'historisation des scenarios |
| `frontend_architecture.md` | Architecture React/Vercel actuelle |
| `frontend_backend_flow.md` | Flux React -> FastAPI -> PostgreSQL |
| `cloud_readiness_audit.md` | Etat cloud Render/Vercel/PostgreSQL |
| `deployment_render_streamlit.md` | Deploiement Render et facade Streamlit optionnelle |

---

## Frontend cockpit

| Document | Role |
|---|---|
| `frontend_architecture.md` | Structure React moderne |
| `frontend_evolution_roadmap.md` | Roadmap cockpit deja executee et prochains sprints |
| `navigation_strategy.md` | Strategie de navigation enterprise |
| `navigation_architecture.md` | Sidebar, topbar, menus et contexte |
| `cockpit_architecture.md` | Architecture cockpit decisionnel |
| `dashboard_density_strategy.md` | Densite dashboards et priorites KPI |
| `no-scroll_strategy.md` | Strategie anti-scroll vertical |
| `design_system.md` | Principes visuels |

---

## API et integration

| Document | Role |
|---|---|
| `api_services.md` | Services API frontend et mapping endpoints |
| `frontend_backend_flow.md` | Flux fonctionnel complet |
| `cloud_test_pipeline.md` | Tests cloud de bout en bout |
| `powerbi_integration.md` | Integration Power BI |
| `powerbi_navigation_strategy.md` | Navigation React/Power BI unifiee |
| `powerbi_service_integration.md` | Power BI Service |

---

## Analytics et BI

| Document | Role |
|---|---|
| `analytics_engine_v1.md` | SP2I Analytics Engine V1 |
| `powerbi_scenarios.md` | Scenarios Power BI |
| `dashboard_density_strategy.md` | Organisation des dashboards |

---

## IA Excel et DQE

| Document | Role |
|---|---|
| `ai_excel_engine.md` | Architecture IA d'analyse Excel |
| `ai_mapping_strategy.md` | Strategie de mapping colonnes/familles |
| `ai_confidence_engine.md` | Scores de confiance |
| `ai_validation_flow.md` | Validation humaine assistee |
| `human_validation_strategy.md` | Role de l'utilisateur dans la validation |

---

## Moteurs metier

| Document | Role |
|---|---|
| `decision_engine.md` | DecisionEngine explicable |
| `scoring_logic.md` | Logique de scoring |
| `risk_engine.md` | Moteur de risque |
| `risk_model.md` | Modele risque |
| `procurement_engine.md` | Procurement analytics |
| `procurement_analytics.md` | Analyse achats |
| `lead_time_model.md` | Modele delais |
| `import_strategy.md` | Strategie import |
| `africa_china_import.md` | Contexte Afrique/Chine |

---

## Logistique

| Document | Role |
|---|---|
| `container_engine.md` | Planification containers |
| `shipment_engine.md` | Suivi shipment |
| `freight_model.md` | Cout fret, douane, livraison |
| `site_logistics.md` | Logistique chantier |
| `africa_import_logistics.md` | Logistique import Afrique |

---

## Tests et qualite

| Document | Role |
|---|---|
| `tests_simulation.md` | Strategie de tests simulation |
| `cloud_test_pipeline.md` | Workflow de test cloud |
| `frontend_ux_audit.md` | Audit UX/UI |

---

## Regle de maintenance documentaire

Quand une brique change, mettre a jour au minimum :

1. `README.md`
2. le document specifique de la brique modifiee
3. `README_DOCUMENTATION.md` si un nouveau document est ajoute

La documentation doit decrire l'etat reel du projet, pas seulement la cible
theorique.
