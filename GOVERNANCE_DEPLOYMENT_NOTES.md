# SP2I_CAPEX - Governance Deployment Notes

Date : 2026-05-21

## Objectif

Preparer un preview deployment du Governance Cockpit Frontend V1 sans promotion production.

## Build local

Commande :

`npm run build`

Repertoire :

`08_FRONTEND`

Resultat :

- Build OK.
- Artefacts generes dans `08_FRONTEND/dist`.

## Preview attendu

Commande Vercel recommandee depuis `08_FRONTEND` :

`vercel`

Ne pas utiliser :

`vercel --prod`

## Routes a tester en preview

- `/app/governance-cockpit`
- `/app/procurement-intelligence`
- `/app`
- `/app/procurement`

## Checklist preview

Governance cockpit :

- KPI strip visible.
- Review queue chargee.
- AG Grid responsive.
- Escalation panel lisible.
- Drift heatmap rendue.
- Confidence matrix lisible.
- Explainability panel metier.
- Audit timeline visible.
- Family status board lisible.

Navigation :

- Sidebar affiche `Gouvernance Enterprise`.
- Route `/app/governance-cockpit` lazy-loaded.
- Route procurement cockpit existante intacte.

Fallback data :

- Le service tente `/governance/cockpit`.
- Si l'API n'existe pas, fallback dataset V1 actif.
- Aucun crash frontend attendu.

## Warnings connus

- Node.js local `20.16.0` : Vite recommande `20.19+` ou `22.12+`.
- Chunk principal superieur a 500 kB.
- React Query expose des warnings `use client` ignores par Vite.

## Decision

Preview deployment autorise.

Production deployment non autorise dans cette phase.
