# Classification Engine Rules

Source de validation: `03_DONNEES_REFERENCE/DQE_PROJECT_SP2I.xlsx`, onglet `DQE_CLEAN`.

## Normalisation

Le moteur normalise maintenant les designations avant scoring:

- accents retires
- casse uniformisee
- separateurs harmonises
- espaces multiples supprimes
- unites chantier harmonisees: `kva`, `wc`, `ah`, `vdc`
- synonymes chantier: `GROUPE ELECT.`, `GE`, `G/E`, `GPE` vers `groupe electrogene`
- synonymes solaires: `photovalta`, `photovolta` vers `photovoltaique`
- synonymes prestation: `F&P`, `F P`, `fourn pose` vers `fourniture pose`

## Familles stabilisees

Les familles cible sont:

- `ELECTRICITE`
- `HVAC`
- `PLOMBERIE`
- `MENUISERIE`
- `GROS_OEUVRE`
- `REVETEMENTS`
- `PEINTURE`
- `MEDICAL`
- `SECURITE`
- `IT_RESEAUX`
- `SOLAIRE`
- `VRD`
- `DEMOLITION`
- `INSTALLATION_CHANTIER`
- `LOGISTIQUE_CHANTIER`
- `SECURITE_HSE`
- `ETUDES_CONTROLES`
- `ETANCHEITE`
- `FACADE`

Les alias historiques restent compatibles: `RESEAUX_IT`, `ENERGIE_SOLAIRE`, `MENUISERIE_ALU`, `MENUISERIE_BOIS`, `EQUIPEMENTS_MEDICAUX`.

## Sous-lots

Les sous-lots explicites sont detectes par priorite metier:

- `GROUPE_ELECTROGENE`
- `TGBT`
- `ECLAIRAGE`
- `PRISES`
- `ONDULEURS`
- `PANNEAUX`
- `CLIMATISATION`
- `VENTILATION`
- `SANITAIRE`
- `EVACUATION`
- `ALIMENTATION_EAU`
- `ALUCOBOND`
- `PEINTURE_INTERIEURE`
- `RESEAUX_DIVERS`
- `VIDEOSURVEILLANCE`
- `CONTROLE_ACCES`

## Type ligne

Types officiels:

- `ARTICLE`
- `PRESTATION`
- `TRAVAUX`
- `FOURNITURE`
- `EQUIPEMENT`
- `TOTAL`
- `DOCUMENTAIRE`
- `VALIDATION`
- `TITRE_SECTION`

Les types `TOTAL`, `DOCUMENTAIRE`, `VALIDATION` et `TITRE_SECTION` sont classes comme non importables et ne doivent pas porter une recommandation procurement.

## Priorites

Le scoring favorise:

- mots techniques precis
- puissance ou unite specifique: `kva`, `wc`, `ah`, `mm2`
- coherence famille/lot/sous-lot
- equipement identifiable

Le scoring penalise:

- `materiel`
- `divers`
- `accessoires`
- `ensemble`
- `travaux`
- `installation`
- `raccordement`

## Faux positifs bloques

Exemples de blocage:

- `Mobilisation du personnel et du materiel` ne peut plus devenir `IT_RESEAUX`.
- `Porte metallique du local groupe electrogene` ne peut plus devenir groupe electrogene.
- `Isolation thermo-acoustique` ne peut plus devenir solaire par erreur de mots generiques.

## Explainability

Chaque ligne classifiee renvoie:

- `classification_confidence`: `HIGH`, `MEDIUM`, `LOW`
- `classification_reason`: mots-cles, synonymes, contexte ou exclusion ayant justifie le resultat
- `type_ligne`: type officiel stabilise

Exemple attendu:

`GROUPE ELECT. PAO 75 KVA INSON` -> detection par `groupe electrogene`, `kva`, contexte `ELECTRICITE`, confiance `HIGH/MEDIUM` selon coherence DQE.
