# État pré-déploiement SP2I

Date du contrôle : 29 août 2026 (UTC).

## Réalisé

- Branche de préparation : `codex/work-project-setup`.
- Déploiement automatique Render : désactivé sur le service réel.
- Espace Neon de production SP2I identifié : projet `SP2I_CAPEX`, base
  `neondb`, branche `production`, 46,78 MB et 290 lignes dans `fact_metre`.
- Snapshot Neon manuel créé sur cette branche à
  `2026-08-29 08:25:03 UTC`, sans expiration.
- Variables de sécurité enregistrées sur le service Render réel avec
  `Save only`, sans déclencher de déploiement : `ENVIRONMENT=production`,
  origine CORS exacte, URL frontend, secret JWT aléatoire, mutations de schéma
  au démarrage désactivées et métriques SQL par requête désactivées.
- `DATABASE_URL` Render remplacée par la connexion poolée de la base Neon SP2I
  auditée, avec `Save only` et sans déclencher de déploiement.
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
- Schéma de production audité en lecture seule : les cinq tables requises et
  les colonnes d'isolation sont présentes ; aucune ligne de `fact_metre` n'est
  orpheline de `dim_projet`.
- Compatibilité corrigée entre le nom réel `dim_projet.projet_code` et le
  contrôle d'accès/vérificateur pré-déploiement (`2d7aa77`).

## Blocages constatés

1. La base contient deux projets dimensionnels mais aucun compte utilisateur,
   aucun projet applicatif et aucune adhésion. Il faut créer le premier
   administrateur puis rattacher les deux projets avant le déploiement.
2. Le secret de base transmis dans la conversation doit être révoqué/rotaté ;
   il n'a pas été enregistré dans le dépôt ni réaffiché.
3. Le plan Render gratuit ne fournit ni Shell ni One-Off Jobs. Les opérations
   d'initialisation doivent donc être réalisées depuis Neon ou par un flux
   applicatif sécurisé.
4. Les journaux Render du 26 août 2026 montrent une erreur SQLAlchemy pendant
   les mutations de schéma au démarrage, tout en laissant Uvicorn démarrer.
5. Les 79 fichiers de données suivis par le dépôt public ne sont pas encore
   qualifiés par le propriétaire des données.
6. Les tests Python concernés ne peuvent pas être exécutés localement : les
   dépendances ne sont pas présentes et leur installation réseau a été refusée.

## Verdict

**NO-GO** tant que l'administrateur et les rattachements projet ne sont pas
initialisés et que les fichiers DQE publics ne sont pas qualifiés. Aucun
déploiement ne doit être déclenché avant la levée de ces blocages.
