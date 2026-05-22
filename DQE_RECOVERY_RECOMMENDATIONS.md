# SP2I_CAPEX - DQE Recovery Recommendations

Date : 2026-05-21

## Objectif

Aider a nettoyer le fichier `DQE_PROJECT_SP2I.xlsx` sans affaiblir les protections governance.

## Priorites de correction

### 1. Completer les unites manquantes

Cause dominante :

`MISSING_UNITE` : 76 occurrences.

Action recommandee :

- verifier les lignes sans unite ;
- completer avec `U`, `ENS`, `ML`, `M2`, `M3`, `KG`, `FORFAIT` selon le cas ;
- ne pas forcer une unite si la ligne est un titre, une note ou un total.

Impact attendu :

- baisse forte des warnings ;
- meilleure stabilite KPI ;
- meilleure detection articles/prestations.

### 2. Revoir les familles inconnues

Cause :

`UNKNOWN_FAMILY` : 14 occurrences.

Action recommandee :

- identifier si la designation appartient a une famille connue ;
- enrichir le lot ou la famille si elle est manquante ;
- laisser en revue si la ligne est trop ambigue.

Impact attendu :

- meilleure attribution familles ;
- moins de faux dashboards ;
- meilleure coherence procurement.

### 3. Corriger les quantites absentes

Cause :

`MISSING_QTE` : 3 occurrences.

Action recommandee :

- si la ligne est un article reel : ajouter la quantite ;
- si la ligne est un titre/commentaire : la classer comme ligne ignoree ;
- si la quantite est incluse dans la designation : la separer dans la colonne quantite.

Impact attendu :

- reduction des lignes en revue humaine ;
- meilleure fiabilite CAPEX.

## Regles de recuperation

| Situation | Statut recommande | Action |
| --- | --- | --- |
| Quantite absente mais designation claire | `REVIEW_REQUIRED` | Demander validation metier. |
| Unite absente mais designation et quantite presentes | `WARNING` | Completer unite avant decision. |
| Titre ou section | `IGNORED_TITLE` | Ne pas compter comme perte. |
| Sous-total | `IGNORED_SUBTOTAL` | Ignorer pour eviter double comptage. |
| Plusieurs articles dans une cellule | `REJECTED` | Separar en plusieurs lignes. |
| Cellules fusionnees | `REVIEW_REQUIRED` | Defusionner et recopier le contexte. |
| Format decale | `REJECTED` | Corriger les colonnes source. |

## Message utilisateur recommande

Au lieu de :

`Perte massive de lignes detectee pendant le parsing DQE`

Afficher :

`Certaines lignes du DQE ne peuvent pas encore alimenter les KPI. 0 lignes sont rejetees, 17 lignes demandent une revue humaine et 70 lignes ont des donnees incompletes a verifier.`

## Prochaine etape technique

Brancher cette couche d'explication dans le pipeline existant afin que le message de blocage affiche :

- nombre de lignes rejetees ;
- nombre de lignes a revoir ;
- nombre de lignes ignorees volontairement ;
- top 3 causes ;
- lien vers l'audit detaille.
