# SP2I_CAPEX - Governance Terminology Mapping

Date : 2026-05-21

## Mapping interface utilisateur

| Terme technique | Terme visible utilisateur |
| --- | --- |
| Procurement score | Fiabilite des achats |
| Confidence score | Niveau de confiance des donnees |
| Drift score | Ecart avec le marche |
| Review backlog | References a verifier |
| High risk | Risques critiques |
| Escalation | Validation superieure requise |
| Block import | Importation non autorisee |
| Double validation | Double verification obligatoire |
| Procurement review | Verification achat necessaire |
| Technical validation | Controle technique requis |
| Low confidence | Donnees peu fiables |
| High drift | Prix eloignes du marche |
| Governance score | Niveau global de controle |
| Review queue | Liste de controle avant decision |
| Audit timeline | Trace des decisions |
| Explainability | Explication metier |
| Benchmark | Prix de comparaison marche |
| Workflow | Etapes de verification |

## Mapping actions

| Terme technique | Action visible |
| --- | --- |
| Approve | Valider |
| Reject | Refuser |
| Escalate | Envoyer au responsable achat |
| Request review | Demander une verification |
| Request technical review | Demander un controle technique |
| Override recommendation | Modifier la recommandation avec justification |
| Add governance comment | Ajouter un commentaire de validation |

## Mapping etats

| Etat technique | Etat visible |
| --- | --- |
| PENDING | A verifier |
| IN_REVIEW | En cours de verification |
| APPROVED | Valide |
| REJECTED | Refuse |
| ESCALATED | Envoye au responsable |
| NEEDS_MORE_DATA | Donnees complementaires requises |
| BLOCKED | Bloque |
| HIGH_RISK | Risque eleve |
| CONDITIONALLY_READY | Pret sous controle |
| VERIFIED | Verifie |

## Regle de traduction

Les termes techniques restent autorises dans les structures de donnees et le code pour ne pas casser l'architecture.

Toute nouvelle interface visible doit utiliser le vocabulaire metier ci-dessus.
