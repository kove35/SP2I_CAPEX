# État pré-déploiement SP2I

Date du contrôle : 29 août 2026 (UTC).

## Réalisé

- Branche de préparation : `codex/work-project-setup`.
- Déploiement automatique Render : désactivé sur le service réel.
- Snapshot Neon manuel créé sur la branche `production` à
  `2026-08-29 07:06:43 UTC`, sans expiration.
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

1. Le service Render contient 9 variables, mais il manque encore
   `SP2I_JWT_SECRET`, `FRONTEND_URL`, `CORS_ORIGIN_REGEX`,
   `ALLOW_STARTUP_SCHEMA_MUTATIONS` et les valeurs production validées.
2. Enregistrer ces variables dans Render constitue une modification sensible et
   peut préparer un redémarrage ; l'opération doit être faite après publication
   du code durci et avec confirmation au moment d'envoyer le secret.
3. Le projet Neon accessible ne contient, dans `neondb/public`, aucune table
   SP2I. La `DATABASE_URL` Render pointe donc vers un autre périmètre ou une base
   non accessible depuis ce compte. Les migrations et la création/validation de
   l'administrateur ne peuvent pas être exécutées de façon sûre depuis Neon.
4. Le plan Render gratuit ne fournit ni Shell ni One-Off Jobs. Le contrôle de
   schéma ne peut pas être lancé sur la base réellement utilisée depuis Render.
5. Les journaux Render du 26 août 2026 montrent une erreur SQLAlchemy pendant
   les mutations de schéma au démarrage, tout en laissant Uvicorn démarrer.
6. Les 79 fichiers de données suivis par le dépôt public ne sont pas encore
   qualifiés par le propriétaire des données.

## Verdict

**NO-GO** tant que la base réellement référencée par `DATABASE_URL` n'est pas
identifiée et validée, qu'un administrateur actif n'est pas confirmé, que les
variables Render ne sont pas enregistrées et que les fichiers DQE publics ne
sont pas qualifiés.
