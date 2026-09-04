# Impact — migration 033

## Objet

La migration crée une couche financière V6 unique et limitée par projet. Elle
réconcilie les quantités DQE canoniques avec les prix article V6, puis alimente
les vues Direction, coût projet et Cost Intelligence à partir de cette même
source.

## Objets ajoutés

- `vw_fact_metre_financial_v6`
- `vw_project_cost_summary_v6`
- `vw_dashboard_direction_v6_scoped`
- `vw_cost_intelligence_v6_scoped`

Les vues historiques ne sont ni remplacées ni supprimées. La migration échoue
et annule toute la transaction si une ligne canonique ne peut pas être reliée à
exactement un projet ou si un prix V6 manque.

## Effet API

`SP2I_FINANCIAL_SOURCE` utilise la nouvelle vue par défaut. Les endpoints V6
appliquent le projet demandé et ne lisent plus les vues globales. Les KPI brut,
optimisé et économie proviennent désormais du même grain financier.

## Hypothèses auditées

Les taux de coûts indirects, installation chantier, logistique import et aléas
restent les paramètres de politique V6 de la migration 031 (11 %, 4,2 %, 3,5 %
et 12 %). Ils sont exposés dans la vue de synthèse pour rendre cette hypothèse
visible et contrôlable.

## Retour arrière

Exécuter `rollback_033_v6_financial_reconciliation.sql`, puis remettre
`SP2I_FINANCIAL_SOURCE=vw_fact_metre_financial_canonical` si la variable avait
été explicitement configurée. Aucune donnée physique n'est modifiée.

## Validation Neon de test — 4 septembre 2026

Migration exécutée uniquement sur la branche éphémère
`codex-financial-reconciliation-v6`, créée depuis `production`. La production
n'a pas été modifiée.

| Contrôle | Résultat |
|---|---:|
| Projet | `PROJET_MPEMBA` |
| Lignes financières | 1 298 |
| Lots | 18 |
| CAPEX brut | 718 868 523,00 FCFA |
| CAPEX optimisé | 683 620 917,40 FCFA |
| Économie | 35 247 605,60 FCFA |
| Coût projet total | 955 692 569,23 FCFA |
| Surface | 1 263,90 m² |
| Appartements / niveaux | 6 / 3 |
| Lignes sans projet | 0 |
| Doublons de grain projet | 0 |
| Prix incomplets | 0 |
| Écarts synthèse / faits | 0 |
| Écarts Direction / faits | 0 |
| Fuite vers un projet inexistant | 0 |
