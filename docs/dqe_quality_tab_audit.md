# Audit onglet Qualite donnees DQE

Date : 2026-05-19

Perimetre :

- sidebar `DQE & donnees projet`
- page React `DqePage.jsx`
- services frontend upload Excel
- endpoints backend DQE/upload/analytics disponibles
- coherence avec le pipeline DQE et `FACT_METRE`

## Synthese

L'onglet `Qualite donnees` existe, mais il n'est pas encore un vrai cockpit de qualite projet. Il affiche uniquement un resume local issu de la derniere analyse Excel de la session courante.

En pratique :

- si l'utilisateur n'a pas analyse un fichier dans la session React, l'onglet est presque vide ;
- il ne lit pas les donnees deja synchronisees en PostgreSQL ;
- il ne montre pas les lignes en anomalie ;
- il ne montre pas les controles critiques du pipeline ;
- il ne donne pas de preuve que `FACT_METRE` est coherent.

L'onglet doit evoluer d'un etat "resume preview" vers un vrai tableau de controle qualite DQE.

## Flux actuel observe

Navigation :

- `Qualite donnees` pointe vers `/app/dqe?tab=quality`
- la page charge `DqePage`
- l'etat `analysis` est uniquement local au composant React
- les informations affichees viennent de `analysis.ai_preview`, `analysis.ai_confidence`, `analysis.ai_anomalies` et `validationResult`

Services utilises :

- analyse non destructive : `/api/upload/excel`
- sync destructive : `/api/upload/excel/sync`
- validation mapping : `/dqe/validate-mapping/{file_id}`

Endpoints disponibles mais non utilises par l'onglet :

- `/dqe/stats`
- `/dqe/ai-preview/{file_id}`
- `/dqe/ai-analyze/{file_id}`
- `/dqe/ai-suggestions/{file_id}`
- `/analytics/debug/pipeline`
- `/analytics/qa-summary`

## Points positifs

- le mapping frontend utilise bien `data.status === "SUCCESS"` ;
- le score DQE est calcule correctement sur une valeur entre 0 et 1 ;
- les nouvelles cles backend sont lues :
  - `ai_preview.quality_score`
  - `ai_preview.lots_detected`
  - `ai_preview.recognized_columns`
  - `ai_preview.estimated_capex_detected`
  - `ai_anomalies`
- la preview et la sync sont separees, ce qui protege PostgreSQL ;
- les erreurs API sont affichees au lieu d'etre silencieuses.

## Problemes UX / produit

### 1. Onglet non autonome

`Qualite donnees` depend de `analysis`, qui existe seulement apres un upload/analyse dans la page courante.

Consequences :

- refresh navigateur = perte du diagnostic qualite ;
- changement d'onglet = pas de donnees persistantes ;
- impossible d'auditer le dernier DQE synchronise sans re-uploader le fichier ;
- experience confuse pour un utilisateur direction/projet.

Action recommandee :

- charger automatiquement `/analytics/debug/pipeline` ou `/analytics/qa-summary` quand l'onglet `quality` est ouvert ;
- afficher le dernier dataset synchronise meme sans fichier local.

### 2. Pas de tableau des anomalies

L'onglet affiche seulement :

- nombre d'avertissements mapping ;
- nombre d'anomalies IA.

Il n'affiche pas :

- liste des anomalies ;
- ligne Excel concernee ;
- colonne concernee ;
- severite ;
- action recommandee ;
- statut corrige/non corrige.

Action recommandee :

- ajouter un tableau "Points a controler" base sur `ai_anomalies` et `classified_rows` ;
- regrouper par type :
  - mapping ;
  - quantite ;
  - montant ;
  - lot ;
  - feuille ;
  - lignes ignorees.

### 3. Pas de controles pipeline apres sync

Apres envoi en base, l'onglet ne verifie pas :

- nombre de lignes `FACT_METRE` ;
- somme `capex_local` ;
- lignes sans lot ;
- lignes sans montant ;
- vues analytics disponibles ;
- cache analytics vide/recharge.

Action recommandee :

- appeler `/analytics/debug/pipeline` apres `syncExcel` ;
- afficher :
  - lignes inserees ;
  - total CAPEX ;
  - lignes invalides ;
  - source `FACT_METRE` retenue ;
  - feuilles ignorees ;
  - warnings SQL.

### 4. Libelles encore trop techniques

L'interface montre encore :

- `Score DQE`
- `Confiance globale IA`
- `File ID`
- `Endpoint preview`
- `Endpoint sync`

Ces informations sont utiles pour l'equipe technique, mais trop visibles pour un utilisateur metier.

Action recommandee :

- remplacer par des labels metier :
  - `Fiabilite du fichier`
  - `Confiance de lecture`
  - `Reference d'import`
  - `Analyse du fichier`
  - `Envoi en base projet`
- cacher les endpoints dans un bloc diagnostic technique repliable.

### 5. Navigation DQE ambigue

Dans la sidebar :

- `Envoyer en base` pointe vers `/app/dqe?tab=import`
- `Historique imports` pointe vers `/app/dqe?tab=analysis`

Ces deux entrees ne correspondent pas a de vrais onglets dedies.

Action recommandee :

- creer `tab=sync` pour l'envoi en base ;
- creer `tab=history` pour l'historique ;
- ou supprimer temporairement ces entrees tant que les vues ne sont pas distinctes.

### 6. Pas d'historique d'import

Le backend garde l'analyse IA en memoire via `AIFileStore`, mais il n'y a pas encore d'historique persistant consultable depuis l'onglet qualite.

Impact :

- impossible de comparer deux imports ;
- impossible de savoir quel fichier a alimente la base ;
- impossible d'auditer le dernier import cloud apres redeploiement.

Action recommandee :

- creer une table `dqe_import_run` ou reutiliser `simulation_run` avec type `DQE_IMPORT` ;
- stocker :
  - fichier ;
  - date ;
  - utilisateur futur ;
  - lignes detectees ;
  - lignes normalisees ;
  - score qualite ;
  - CAPEX detecte ;
  - status sync ;
  - warnings.

## Proposition de cible UX

L'onglet `Qualite donnees` devrait devenir :

1. `Synthese qualite`
   - Fiabilite fichier
   - Lignes lues
   - Lignes exploitables
   - Lots detectes
   - Budget detecte
   - Colonnes reconnues

2. `Points a controler`
   - tableau anomalies
   - criticite
   - action recommandee

3. `Controle avant envoi en base`
   - feuille source retenue
   - feuilles ignorees
   - taux de perte
   - mapping colonnes

4. `Controle apres envoi en base`
   - lignes `FACT_METRE`
   - CAPEX PostgreSQL
   - vues analytics OK/KO
   - cache analytics

5. `Diagnostic technique`
   - file_id
   - endpoints
   - payload brut replie

## Endpoints a connecter

Minimum sans nouveau backend :

- `/analytics/debug/pipeline`
- `/analytics/qa-summary`
- `/dqe/stats`
- `/dqe/ai-analyze/{file_id}`

Ideal V2 :

- `/dqe/imports`
- `/dqe/imports/{import_id}`
- `/dqe/imports/{import_id}/quality`

## Priorites recommandees

Priorite 1 :

- connecter l'onglet `quality` a `/analytics/debug/pipeline` pour qu'il fonctionne meme sans upload local.

Priorite 2 :

- afficher les anomalies IA dans un vrai tableau metier.

Priorite 3 :

- separer les onglets `sync` et `history` au lieu de pointer vers `import` et `analysis`.

Priorite 4 :

- franciser les labels techniques et cacher les endpoints dans un panneau diagnostic.

Priorite 5 :

- ajouter un historique persistant des imports DQE.

## Conclusion

L'onglet `Qualite donnees` est une bonne premiere brique, mais il reste trop statique et trop local. Pour devenir credible en production, il doit auditer le dernier DQE synchronise, afficher les anomalies ligne par ligne et prouver la coherence entre Excel, pipeline, PostgreSQL et Analytics Engine.
