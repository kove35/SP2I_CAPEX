# SP2I_CAPEX - Governance Release Checklist

Date : 2026-05-21
Milestone cible : `v0.9.0-governance-foundation`

## Scope release

- Governance multi-familles
- Procurement review workbench
- Governance cockpit datasets
- Governance cockpit frontend V1
- Routes React et sidebar
- Hooks, services et stores governance
- Documentation governance
- Devtools governance

## Worktree audit

Actions realisees :

- `git status --short` execute.
- `.gitignore` complete pour proteger :
  - `~$*.xlsx`
  - `*.tmp`
  - `*.bak`
  - `.DS_Store`
  - `Thumbs.db`
  - `.continue/`
- Fichiers lock Excel non stages via ignore.
- Livrables governance conserves.

Point d'attention :

- `03_DONNEES_REFERENCE/SP2I_CAPEX_DEMO.xlsx` est supprime dans le worktree. Cette suppression est visible avant commit et doit etre incluse seulement si elle correspond a l'etat projet attendu.

## Fichiers governance verifies

Frontend :

- `GovernanceCockpit.jsx`
- `GovernanceKpiStrip.jsx`
- `GovernanceReviewQueue.jsx`
- `GovernanceEscalationPanel.jsx`
- `GovernanceDriftHeatmap.jsx`
- `GovernanceConfidenceMatrix.jsx`
- `GovernanceExplainabilityPanel.jsx`
- `GovernanceAuditTimeline.jsx`
- `GovernanceFamilyStatusBoard.jsx`

Hooks/services/stores :

- `governanceCockpitService.js`
- `useGovernanceCockpit.js`
- `governanceCockpitStore.js`

Datasets :

- `GOVERNANCE_COCKPIT_DATASET.xlsx`
- `GOVERNANCE_WORKFLOW_TIMELINE.xlsx`
- `GOVERNANCE_ESCALATION_MATRIX.xlsx`
- `GOVERNANCE_EXPLAINABILITY_DATA.xlsx`
- `GOVERNANCE_AUDIT_TIMELINE.xlsx`

Docs :

- `COCKPIT_GOVERNANCE_ARCHITECTURE.md`
- `COCKPIT_GOVERNANCE_COMPONENTS.md`
- `PROCUREMENT_WORKBENCH.md`
- `MULTI_FAMILY_GOVERNANCE.md`

## Validations techniques

Backend :

- `.venv\Scripts\python.exe devtools\validate_imports.py`
- Resultat : OK, 4/4 checks.

Frontend :

- `npm run build`
- Resultat : OK.

Warnings non bloquants :

- Node.js `20.16.0` inferieur a la recommandation Vite 7 (`20.19+` ou `22.12+`).
- Directives `use client` React Query ignorees au bundle.
- Chunk principal superieur a 500 kB.

## QA locale

Route testee :

- `/app/governance-cockpit`

Resultat :

- Vite local a servi la route sur `http://127.0.0.1:5176/app/governance-cockpit`.
- HTTP `200 OK`.

## Readiness release

Statut :

- Backend imports : OK.
- Frontend build : OK.
- Route governance : OK.
- Worktree protege contre les locks Excel : OK.
- Commit/tag/push : a effectuer apres staging final.
- Preview Vercel : a effectuer apres push ou via CLI preview.
