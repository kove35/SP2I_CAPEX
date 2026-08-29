# État pré-déploiement SP2I

Date du contrôle : 29 août 2026 (UTC).

## Réalisé

- Branche de préparation : `codex/work-project-setup`.
- Déploiement automatique Render : désactivé sur le service réel.
- Snapshot Neon manuel créé sur la branche `production` à
  `2026-08-29 07:06:43 UTC`, sans expiration.
- Variables de sécurité enregistrées sur le service Render réel avec
  `Save only`, sans déclencher de déploiement : `ENVIRONMENT=production`,
  origine CORS exacte, URL frontend, secret JWT aléatoire, mutations de schéma
  au démarrage désactivées et métriques SQL par requête désactivées.
- Chemin de contrôle de santé Render configuré sur `/health`.
- Table Neon de démonstration accidentelle `public.playing_with_neon` supprimée ;
  la vérification `to_regclass(...) IS NULL` a retourné `true`.
- Manifeste `render.yaml` durci : production, CORS exact, secret JWT externe,
  mutations de schéma au démarrage désactivées et déploiement manuel.
- Isolation analytics ajoutée : projet obligatoire pour les non-admins,
  contrôle propriétaire/membre et filtre SQL exact sur le projet.
- Endpoints BI globaux et diagnostics non filtrables réservés aux admins.
- Vérificateur de schéma en lecture seule ajouté :

  ```bash
  PYTHONPATH=07_API_BACKEND python -m app.scripts.predeploy_check
  ```

- Compilation Python et build frontend exécutés localement.

## Blocages constatés

1. Le projet Neon accessible ne contient, dans `neondb/public`, aucune table
   SP2I. La `DATABASE_URL` Render pointe donc vers un autre périmètre ou une base
   non accessible depuis ce compte. Les migrations et la création/validation de
   l'administrateur ne peuvent pas être exécutées de façon sûre depuis Neon.
2. Le plan Render gratuit ne fournit ni Shell ni One-Off Jobs. Le contrôle de
   schéma ne peut pas être lancé sur la base réellement utilisée depuis Render.
3. Les journaux Render du 26 août 2026 montrent une erreur SQLAlchemy pendant
   les mutations de schéma au démarrage, tout en laissant Uvicorn démarrer.
4. Les 79 fichiers de données suivis par le dépôt public ne sont pas encore
   qualifiés par le propriétaire des données.
5. Les tests Python concernés ne peuvent pas être exécutés localement : les
   dépendances ne sont pas présentes et leur installation réseau a été refusée.

## Verdict

**NO-GO** tant que la base réellement référencée par `DATABASE_URL` n'est pas
identifiée et validée, qu'un administrateur actif n'est pas confirmé et que les
fichiers DQE publics ne sont pas qualifiés. Les variables Render sont prêtes,
mais aucun déploiement ne doit être déclenché avant la levée de ces blocages.
