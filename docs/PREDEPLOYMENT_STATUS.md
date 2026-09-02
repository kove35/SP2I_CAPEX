# État pré-déploiement SP2I

Date du contrôle : 1er septembre 2026 (UTC).

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
- Mot de passe de la branche Neon de test contenant l'identifiant exposé
  réinitialisé ; l'ancien secret n'est plus valide.
- Les huit classeurs DQE/source identifiés ont été supprimés de tout
  l'historique publié de `main`, de `codex/work-project-setup` et des tags
  `v0.9.0-governance-foundation`, `v5.3-cutover` et
  `v5.3-filter-cleanup`.
- Les références réécrites ont été publiées sur GitHub le 1er septembre 2026
  et vérifiées : aucun des huit chemins sensibles n'est joignable depuis les
  branches ou tags publics actifs.
- Une sauvegarde complète antérieure à la purge est conservée hors dépôt dans
  `SP2I_CAPEX_before_history_purge_20260901.bundle`.

## Blocages constatés

1. Le plan Render gratuit ne fournit ni Shell ni One-Off Jobs. Les opérations
   d'initialisation doivent donc être réalisées depuis Neon ou par un flux
   applicatif sécurisé.
2. Les journaux Render du 26 août 2026 montrent une erreur SQLAlchemy pendant
   les anciennes mutations de schéma au démarrage. Cette fonction est
   maintenant désactivée dans le manifeste et dans l'environnement Render.
3. Les tests Python concernés ne peuvent pas être exécutés localement : les
   dépendances ne sont pas présentes et leur installation réseau a été refusée.
   La compilation Python et le build de production frontend réussissent.

## Verdict

**Les deux blocages de gouvernance sont levés.** La branche peut passer en CI et
en validation pré-déploiement. Le GO production reste conditionné à la réussite
de la CI, au déploiement manuel Render et aux tests de fumée et d'isolation en
production.
