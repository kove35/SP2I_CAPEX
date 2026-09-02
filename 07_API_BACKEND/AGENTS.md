# Backend FastAPI — Instructions Codex

Ces règles complètent les instructions du `AGENTS.md` racine.

## Architecture

- Routes : validation HTTP et orchestration courte uniquement.
- Services : cas d'usage métier.
- Core : moteurs déterministes et testables sans infrastructure.
- Repositories : accès PostgreSQL et SQL paramétré.
- Schemas : contrats Pydantic explicites.

Éviter d'ajouter de la logique à un fichier déjà surdimensionné. Extraire un
module cohérent lorsque `analytics_service.py`, `projects/routes.py`,
`analytics_repository.py` ou `cloud_migrations.py` est concerné.

## Sécurité

- En production, l'application doit refuser de démarrer sans secret JWT fort.
- L'inscription publique crée au maximum un utilisateur `VIEWER`.
- Toute lecture métier doit être limitée au projet autorisé.
- Toute écriture exige une autorisation de rôle explicite.
- Les routes `/debug/*` et les diagnostics détaillés sont désactivés ou
  réservés aux administrateurs hors développement.
- Ne jamais retourner une exception interne brute au client.
- Pour les uploads : limite avant lecture complète, contrôle du contenu réel,
  nom de fichier neutralisé et transaction pour la synchronisation.

## Données et migrations

- Ne pas utiliser `Base.metadata.create_all()` comme stratégie de migration de
  production.
- Toute migration SQL comprend : migration montante, validation et rollback.
- Ne pas réutiliser un numéro de migration existant.
- Les changements financiers incluent un test de réconciliation.

## Validation

Depuis la racine du dépôt :

```bash
python -m compileall -q 07_API_BACKEND/app
PYTHONPATH=07_API_BACKEND python -m pytest -q
```

Les tests ne doivent pas dépendre d'une base de production ni modifier une base
partagée.

