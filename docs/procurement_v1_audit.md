# Audit QA - SP2I Procurement Intelligence V1

Date : 2026-05-19  
Perimetre : Import Chine V1, sourcing, gain potentiel, scenarios achat, multi-devise, risques, export Excel.

## Synthese executive

La V1 Procurement Intelligence est utilisable pour une demonstration investisseurs/clients en mode cockpit decisionnel. Elle montre une chaine complete : DQE -> FACT_METRE -> arbitrage local/import -> cout rendu chantier -> gain net -> risques -> scenarios Chine -> export Excel.

Statut production readiness : **PRET DEMO / PILOTE CONTROLE**  
Statut achat reel : **NON PRET SANS RFQ FOURNISSEUR ET VALIDATION LOGISTIQUE**

Score global QA : **82 / 100**

## Endpoints audites

| Endpoint | Statut | Controle |
|---|---:|---|
| `/analytics/gain-analysis` | OK | Decomposition financiere nette, scenarios, risques, storytelling |
| `/analytics/procurement-scenarios` | OK | Eco China, Standard China, Premium China |
| `/analytics/suppliers` | OK avec reserve | Base fournisseurs traçable, un fournisseur sanitaire reste a qualifier |
| `/analytics/currency` | OK | FCFA, USD, EUR, taux exposes |
| `/analytics/import-risks` | OK | Risques monetises et classes |
| `/analytics/procurement-export` | OK | Export multi-feuilles openpyxl |

## Tests executes

| Test | Resultat |
|---|---|
| Compilation backend `python -m compileall 07_API_BACKEND\app` | OK |
| Build frontend `npm run build` | OK |
| Verification routes et services analytics | OK |
| Verification multi-devise frontend/backend | OK |
| Verification export Excel code path | OK |

Notes build frontend : Vite signale Node `20.16.0` alors que `20.19+` est recommande, et un warning de taille bundle. Ce ne sont pas des erreurs bloquantes.

## QA fournisseurs Chine

Objectif : eviter une base "mock" visible.

Corrections appliquees :
- Remplacement de fournisseurs generiques par references sourcing plus traçables.
- Ajout `source_url`.
- Ajout `source_confidence`.
- Ajout `supplier_confidence_score`.
- Ajout `qa_status`.

Fournisseurs V1 :

| Categorie | Fournisseur | Pays | Confiance |
|---|---|---:|---:|
| Alucobond | Shanghai Aludream Building Material Co., Ltd. | CN | Elevée |
| Electricite | Shanghai FATO Group Co., Ltd. | CN | Elevée |
| CVC | Midea Group | CN | Moyenne/elevee |
| Sanitaires | Shenzhen Sanitary Technology Benchmark | CN | A qualifier |
| Menuiserie aluminium | ZMR Windows and Doors | CN | Moyenne/elevee |
| Ascenseurs | SJEC Corporation | CN | Elevée |
| Mobilier medical | Guangzhou Medivara Medical Co., Ltd. | CN | Moyenne |

Probleme majeur restant :
- La categorie Sanitaires contient encore une reference benchmark non totalement qualifiee. Elle doit etre remplacee par un fournisseur verifie via RFQ ou base fournisseur interne.

Recommandation :
- Ajouter un champ `rfq_status` en V2 : `Non contacte`, `Contacte`, `Cotation recue`, `Qualifie`, `Blacklist`.

## QA landed cost

Formule V1 :

`Gain net = CAPEX local - (CAPEX import FOB + transport + douane + assurance + logistique + marge securite + risques estimes)`

Couts inclus :
- FOB
- maritime
- assurance
- douane
- port/logistique locale
- livraison chantier
- marge securite
- risques estimes

Statut : **OK pour demo et audit interne**.

Reserve :
- Les taux de cout rendu chantier sont des hypotheses SP2I V1. Ils doivent devenir configurables par pays, port, famille et incoterm.

## QA gain analysis

Points valides :
- Le gain n'est plus une estimation magique.
- Le drawer explique les postes de cout.
- Mini-waterfall disponible.
- Scenarios optimiste, realiste, pessimiste.
- Risques monetises.
- Export du detail du gain.

Point a surveiller :
- Si les donnees `capex_import` FACT_METRE representent deja un cout rendu chantier complet, la recomposition FOB peut sur-interpreter le cout. La metadata expose maintenant la formule pour audit.

Recommandation :
- Ajouter en V2 un champ `cost_basis`: `FOB`, `CIF`, `DDP`, `rendu_chantier`.

## QA multi-devise

Devises :
- FCFA
- USD
- EUR

Taux V1 :
- USD -> FCFA : 610
- EUR -> FCFA : 655.957

Statut : **OK V1**

Reserve :
- Les taux sont des references statiques. Pour production, brancher une table historisee validee finance ou provider FX.

## QA risques import

Risques couverts :
- Maritime
- Douane
- Devise
- Fournisseur
- Qualite
- Geopolitique
- Congestion portuaire

Chaque risque est monétise sur le CAPEX optimise.

Statut : **OK V1**

Amelioration V2 :
- Risques par port, famille, fournisseur, incoterm et date previsionnelle.

## QA procurement scenarios

Scenarios :
- Eco China : gain plus fort, qualite plus basse, risque plus eleve.
- Standard China : equilibre recommande.
- Premium China : qualite et risque maitrises, gain plus faible.

Statut : **OK V1**

Point important :
- Les scenarios sont des modeles de simulation. Ils ne remplacent pas une cotation fournisseur reelle.

## QA export Excel

Export : `SP2I_dossier_achat_chine.xlsx`

Feuilles generees :
- Synthese
- Detail gain
- Lignes FACT_METRE
- Fournisseurs Chine
- Containers
- Risques
- Scenarios
- Storytelling IA

Statut : **OK**

Recommandations :
- Ajouter formats numeriques Excel par devise.
- Ajouter onglet "Hypotheses".
- Ajouter signature/version dataset.

## QA frontend UX

Points valides :
- Devise active visible.
- KPI gain potentiel net explicable.
- Drawer detail gain.
- Export dossier achat.
- Onglets fournisseur, containers, cout rendu chantier, risques et strategies.

Problemes mineurs :
- Le wording "FOB / ROI" peut etre ambigu pour un utilisateur non specialiste.
- Certains tableaux restent denses et meritent des tooltips pedagogiques.

## QA data quality

Controle attendu :
Excel source -> parsing IA -> FACT_METRE -> Procurement analytics -> cockpit.

Statut :
- Le Data Quality Center existe.
- Les KPI procurement utilisent FACT_METRE.
- La devise source est preservee par colonnes `devise_source`, `montant_source`, `montant_fcfa`.

Reserve :
- Les lignes historiques n'ont pas encore de vraie devise source autre que FCFA.

## QA performance

Statut :
- Les endpoints utilisent les services analytics existants.
- Le calcul V1 charge au maximum 5000 lignes pour les analyses export/gain.
- Build frontend OK.

Risque :
- Le bundle frontend depasse 500 kB. A traiter par code splitting avant industrialisation large.

## QA storytelling IA

Statut :
- Les textes expliquent la logique sans promettre un gain non audite.
- Les recommandations mentionnent les reserves : scenario pessimiste, qualite dataset, volatilite import.

Amelioration :
- Generer le storytelling depuis les top lots/fournisseurs reels au lieu de templates.

## Problemes critiques

Aucun probleme critique bloquant la demo.

## Problemes majeurs

1. Base fournisseurs encore partiellement reference, pas encore RFQ.
2. Taux de change statiques.
3. Hypotheses landed cost globales, non parametrees par port/incoterm.
4. Export Excel a enrichir avec formats finance et onglet hypotheses.

## Recommandations V2

1. Workflow RFQ fournisseur.
2. Gestion incoterms : FOB, CIF, DAP, DDP.
3. Taux FX historises et source finance.
4. Port matrix Chine -> Afrique centrale.
5. Sourcing Turquie/UAE.
6. Scoring fournisseur base sur cotations reelles.
7. Validation achats avec statut : propose, en negociation, valide, rejete.

## Checklist production readiness

| Critere | Statut |
|---|---|
| Endpoints analytics disponibles | OK |
| Calcul gain net explicable | OK |
| Export audit-proof | OK |
| Multi-devise cockpit | OK |
| Risques monetises | OK |
| Fournisseurs traçables | Partiel |
| RFQ reel | A faire |
| Taux FX production | A faire |
| Incoterms production | A faire |
| Demo investisseurs | OK |
| Production achat reel | Pilote uniquement |

## Conclusion

SP2I Procurement Intelligence V1 est credible pour une demo premium et un pilote controle. Le produit raconte maintenant une histoire finance/procurement coherente : budget local, sourcing Chine, cout rendu chantier, gain net, risques, scenarios, export audit.

Pour passer en usage achat reel, la prochaine marche est claire : connecter des cotations RFQ, des taux FX historises, des incoterms et des donnees logistiques verifiees.
