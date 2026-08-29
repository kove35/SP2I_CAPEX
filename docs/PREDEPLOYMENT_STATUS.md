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
- Premier compte administrateur actif créé dans Neon après confirmation
  explicite, avec un mot de passe temporaire fort stocké uniquement sous forme
  de dérivé PBKDF2-SHA256 (600 000 itérations).
- Les deux projets dimensionnels ont désormais chacun un projet applicatif et
  une adhésion administrateur : 2 projets, 2 adhésions, 0 périmètre non lié et
  0 ligne de mesure hors périmètre.
- Rotation du mot de passe ajoutée à l'API authentifiée
  (`POST /auth/change-password`) et à l'interface, depuis le contrôle de
  sécurité du compte dans la barre supérieure.

## Blocages constatés

1. Le secret de la base Neon sans lien avec la cible SP2I, transmis dans la
   conversation, doit être révoqué/rotaté par son propriétaire ; il n'a pas été
   enregistré dans le dépôt et n'est pas utilisé par Render.
2. Le plan Render gratuit ne fournit ni Shell ni One-Off Jobs. Les opérations
   d'initialisation doivent donc être réalisées depuis Neon ou par un flux
   applicatif sécurisé.
3. Les journaux Render du 26 août 2026 montrent une erreur SQLAlchemy pendant
   les anciennes mutations de schéma au démarrage. Cette fonction est
   maintenant désactivée dans le manifeste et dans l'environnement Render.
4. Les 79 fichiers de données suivis par le dépôt public, dont 8 fichiers
   DQE/source identifiés, ne sont pas encore qualifiés par le propriétaire des
   données.
5. Les tests Python concernés ne peuvent pas être exécutés localement : les
   dépendances ne sont pas présentes et leur installation réseau a été refusée.
   La compilation Python et le build de production frontend réussissent.

## Verdict

**NO-GO de gouvernance** tant que les fichiers DQE publics ne sont pas qualifiés
et que l'ancien secret Neon exposé n'est pas révoqué. L'initialisation
applicative de la base est terminée ; aucun déploiement ne doit néanmoins être
déclenché avant la levée de ces deux blocages.
