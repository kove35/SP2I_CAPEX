# SP2I CAPEX — Workflow Codex

## Démarrage d'une tâche

1. Ouvrir le dépôt `SP2I_CAPEX` comme dossier principal du projet local.
2. Créer un nouveau chat pour un nouveau résultat.
3. Donner un objectif vérifiable, par exemple :
   `Protéger l'inscription et tous les endpoints destructifs, puis exécuter les tests.`
4. Laisser Codex lire `AGENTS.md` avant de modifier le code.

## Format d'une demande efficace

```text
Objectif :
Périmètre autorisé :
Comportement attendu :
Critères de validation :
Éléments à ne pas modifier :
```

## Branches recommandées

- `security/...` pour authentification et autorisations ;
- `data-quality/...` pour DQE, mappings et contrôles ;
- `backend/...` pour FastAPI et PostgreSQL ;
- `frontend/...` pour React ;
- `powerbi/...` pour SQL, modèle et documentation BI ;
- `infra/...` pour CI/CD et déploiement.

Une branche correspond à un résultat livrable. Éviter de mélanger sécurité,
refonte UI et nouvelles fonctions métier dans la même branche.

## Livraison attendue de Codex

Chaque livraison doit préciser :

- résultat obtenu ;
- fichiers modifiés ;
- tests exécutés et résultats ;
- migrations et rollback éventuels ;
- risques ou validations manuelles restantes ;
- prochain petit lot recommandé.

## Définition de terminé

Une tâche est terminée lorsque :

- le comportement attendu est implémenté ;
- les tests ciblés passent ;
- le build concerné passe ;
- les données financières sont réconciliées si elles ont changé ;
- la documentation utile est mise à jour ;
- aucun secret ni fichier confidentiel n'est inclus ;
- le diff ne contient pas de modification hors périmètre.

