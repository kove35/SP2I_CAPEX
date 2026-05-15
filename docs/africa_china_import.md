# Import Chine vers Pointe-Noire

Le contexte principal de SP2I CAPEX est Pointe-Noire, Congo-Brazzaville.

L'import Chine peut etre tres competitif, mais il ajoute des contraintes que le
moteur doit rendre visibles.

## Contraintes typiques

```text
delai maritime long
douane incertaine
congestion portuaire
transport local
acompte fournisseur
paiement avant expedition
MOQ parfois eleve
SAV plus complexe
certifications produit
```

## Lecture metier

Un produit simple comme le carrelage ou la peinture peut etre un bon candidat a
l'import. Un ascenseur, un groupe electrogene ou un equipement technique peut
necessiter plus de controles : installation, SAV, pieces de rechange,
certification et garantie.

## Role de PostgreSQL et Power BI

PostgreSQL conserve les scores calcules :

```text
global_risk_score
lead_time_days
cashflow_score
moq_risk_score
complexity_score
```

Power BI affiche ces indicateurs, filtre et compare les scenarios. Il ne doit
pas recalculer le risque.
