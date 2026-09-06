# Reprise — Recette locale V6 (SP2I CAPEX)

> Document court de reprise. Actualise-le à chaque clôture de tâche.

| Élément | Valeur |
|---|---|
| Branche | `codex/production-recipe-fixes` |
| HEAD | dernier commit du lot — sujet `chore(recette): lancement reproductible local + document de reprise` (voir `git log`) |
| Worktree | `C:\Users\Geoffrey\Documents\DEVELOPPEMENT\SP2I_CAPEX_RECIPE_FIXES` |
| Modifications non commitées | aucune (worktree propre) |
| Services actifs | backend `127.0.0.1:8000` (recipe DB), frontend Vite V6 `127.0.0.1:5173` |
| PostgreSQL isolé | `sp2i_capex_test_pg` (port 5433), bases `sp2i_capex_recipe` (+ `sp2i_capex_sync_test`) |
| Lancement reproductible | `.\start_recette.ps1` (vérifie PG, démarre backend/frontend, URL + logs) |
| Tests exécutés (clôture) | Build Vite ✅ ; spec navigateur API réelle ✅ 1 passed (A nom réel sans « Mpemba », rechargement, RDC=1000, B=500, C vide « 0 FCFA » + « Non évalué », D/S1 indisponible sans sparkline) |
| Blocages | aucun |
| Prochaine action | recette manuelle navigateur (URL ci-dessous) ; optionnel : rejouer la suite mockée 27/27 |

## URL et accès

- URL : `http://localhost:5173/`
- Compte synthétique : `admin@recette.local` / `Admin123!` (ADMIN — projets A/B/C/D). Aucune donnée de production.
- Logs : `07_API_BACKEND/recette_backend.log` / `.err.log`, `08_FRONTEND/recette_frontend.log` / `.err.log`.
