# SP2I_CAPEX - Workflow projet

## 1. Introduction

Le workflow projet SP2I guide l'utilisateur depuis la creation d'un projet jusqu'au pilotage decisionnel. Il sert a rendre le parcours CAPEX explicite, progressif et auditable, tout en evitant les raccourcis dangereux entre les etapes.

Le principe central est simple : chaque module depend d'un signal metier reel. Une etape prete ne rend pas automatiquement l'etape suivante prete.

## 2. Vue globale

Flux cible du projet :

```text
Creer projet
-> Configurer projet
-> Importer DQE
-> Certifier DQE
-> Synchroniser budget
-> Lancer scenario
-> Preparer approvisionnement
-> Preparer execution
-> Piloter projet
```

Ce workflow est visible dans le Project Hub, le workspace projet, les modules metier et l'onglet Pilotage.

## 3. Etats principaux

### Setup

Le setup determine si le projet contient les informations minimales necessaires :

- nom projet
- client ou organisation
- ville
- pays
- devise
- responsable projet

Si ces champs sont incomplets, le workflow reste en configuration requise.

### DQE

Le DQE represente la source budgetaire du projet. Il peut etre absent, importe, analyse, certifie, certifie avec points a verifier, synchronise ou rejete.

### Budget

Le budget devient exploitable lorsque les donnees DQE certifiees sont synchronisees avec la base projet. Un DQE certifie ne signifie pas automatiquement que le budget est synchronise.

### Scenario

Le scenario represente une simulation CAPEX exploitable. Il est determine a partir des executions de simulation persistantes et de leurs lignes reelles.

### Procurement

L'approvisionnement represente la transformation du scenario en arbitrages achat : import, local, hybride, validation humaine et dossier achat.

### Execution

L'execution represente la preparation chantier : actions, livraisons, ETA, risques logistiques, lots critiques et suivi operationnel.

## 4. Regles de blocage

- Un projet non configure bloque le reste du workflow.
- Un DQE absent bloque le budget et les scenarios.
- Un DQE certifie ne veut pas dire budget synchronise.
- Un budget synchronise ne veut pas dire scenario disponible.
- Un scenario disponible ne veut pas dire approvisionnement pret.
- Un approvisionnement pret ne veut pas dire execution prete.
- L'execution devient prete uniquement si des signaux chantier ou logistiques existent.

Ces regles evitent les faux KPI, faux arbitrages, faux dashboards et decisions prematurees.

## 5. Sources de verite

Sources actuellement utilisees :

- Setup : modele `Project`.
- DQE : version active DQE et signaux governance.
- Budget : synchronisation FACT / statut de sync.
- Scenario : `simulation_run`, `dim_scenario`, `fact_simulation`.
- Procurement : decisions achat dans `fact_simulation` (`decision_import`, `decision_type`, `decision_score`, `procurement_reason`).
- Execution : champs logistiques de `fact_simulation` (`delivery_risk`, `lead_time_total`, `storage_cost`, `shipment_strategy`, `container_strategy`, `criticality_score`).

Le systeme reste volontairement conservateur lorsque la source dediee n'existe pas encore.

## 6. Routes API

Routes projet :

- `PATCH /projects/{project_id}/setup` : sauvegarde la configuration projet.
- `GET /projects/{project_id}/workflow` : retourne l'etat complet du workflow projet.

Routes DQE :

- routes existantes d'import, analyse, validation et synchronisation DQE.

Routes simulation :

- routes existantes de lancement de simulation et lecture scenario.

Routes procurement et decision :

- routes existantes sous `/procurement/*`.
- routes existantes sous `/decision/*`.
- Elles lisent principalement les lignes persistantes dans `fact_simulation`.

Routes logistiques :

- routes existantes sous `/logistics/*`.
- Elles exposent les signaux container, shipment, freight et site delivery depuis `fact_simulation`.

## 7. Reponse workflow

Structure logique de `GET /projects/{project_id}/workflow` :

```json
{
  "status": "SCENARIO_READY",
  "label": "Scenario disponible",
  "completion": 67,
  "steps": [
    {
      "id": "configuration",
      "label": "Configuration",
      "status": "Termine",
      "state": "done",
      "action": "Modifier",
      "route": "/app/projects"
    }
  ],
  "primary_action": {
    "label": "Preparer l'approvisionnement",
    "route": "/app/procurement"
  },
  "dqe": {},
  "budget": {},
  "scenario": {},
  "procurement": {},
  "execution": {}
}
```

Objets metier :

- `dqe` : statut DQE, version, certification, trust score, lignes exploitables.
- `budget` : statut sync, montant total, nombre de lignes, source.
- `scenario` : statut, scenario id, run id, nombre de lignes simulees.
- `procurement` : statut, nombre de decisions, lignes import/local/hybride, export disponible.
- `execution` : statut, actions chantier, lots critiques, livraisons et ETA a surveiller.

## 8. Frontend

Composants et pages connectes au workflow :

- `ProjectHub`
- `ProjectSetupWizard`
- `ProjectWorkflowStepper`
- `ProjectQuickActions`
- `WorkflowGuardEmptyState`
- `CockpitPage`
- `AnalyticsPage`
- `DqePage`
- `SimulationPage`
- `ProcurementPage`
- `SiteExecutionPage`

Le frontend utilise le workflow pour afficher :

- la prochaine action recommandee,
- les etats vides guides,
- les CTA contextuels,
- les alertes projet,
- la synthese decisionnelle Pilotage.

## 9. Fallback demo/local

Le workflow fonctionne en deux modes :

- Backend disponible : les donnees proviennent des endpoints projet et workflow.
- Backend indisponible ou token demo : le frontend utilise `localStorage` et les projets demo.

Les tests Playwright utilisent ce fallback pour rester stables sans backend obligatoire.

Le fallback conserve les memes principes metier :

- budget synchronise ne veut pas dire scenario pret,
- scenario pret ne veut pas dire approvisionnement pret,
- approvisionnement pret ne veut pas dire execution prete.

## 10. Tests Playwright

Les tests e2e couvrent notamment :

- configuration projet,
- persistance apres refresh,
- DQE absent,
- budget non synchronise,
- budget synchronise sans scenario,
- scenario pret sans approvisionnement,
- approvisionnement absent,
- approvisionnement pret sans actions chantier,
- execution prete,
- execution a risque,
- Pilotage decisionnel,
- responsive minimal.

Dernier etat connu : `20 passed`.

## 11. Limites actuelles

Limites connues :

- Pas encore de table chantier dediee.
- Pas encore de table validation achat dediee.
- Certains signaux procurement viennent de `fact_simulation`.
- Certains signaux execution viennent des champs logistiques de `fact_simulation`.
- Le scenario actif est detecte a partir des executions disponibles, mais pas encore versionne comme entite fonctionnelle complete.
- Le DQE versionne persistant reste a renforcer cote backend.
- Node `20.16.0` doit etre aligne avec la version recommandee par Vite (`20.19+` ou `22.12+`).

## 12. Roadmap

Evolutions recommandees :

- Creer une table de validation achat.
- Creer une table actions chantier.
- Rendre le scenario actif explicitement versionne.
- Renforcer la persistance des versions DQE.
- Ajouter un audit trail workflow.
- Historiser `primary_action`.
- Ajouter une table de statuts workflow par projet.
- Relier les scenarios a `dqe_version_id`.
- Relier les arbitrages achat a un scenario valide.
- Relier les actions chantier aux arbitrages achat valides.

## 13. Resume metier

Le workflow projet SP2I transforme l'application en plateforme CAPEX guidee :

```text
Projet configure
-> donnees certifiees
-> budget fiable
-> scenario simule
-> arbitrages achat prepares
-> execution chantier preparee
-> pilotage direction fiable
```

Chaque etape garde son propre statut, sa source de verite et sa prochaine action.
