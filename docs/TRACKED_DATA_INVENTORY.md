# Inventaire des donnees suivies par Git - ETAT APRES LOT 4

Audit realise : septembre 2026, apres le retrait controle (Lot 4) des donnees a
provenance indeterminee. Aucune donnee metier sensible n'est reproduite ici.

## SUIVI ET AUTORISE

- `02_REFERENTIELS/mapping_familles.xlsx`, `02_REFERENTIELS/ratios_fob.xlsx`
  (INTERNE_DEMONTRE - referentiels de calcul conserves).
- `07_API_BACKEND/app/core/capex_taxonomy/*.json` (20) et
  `07_API_BACKEND/app/core/financial_ranges/*.json` (20) : JSON moteur
  (INTERNE, requis au runtime).
- JSON non nominatifs : `01_PARAMETRES/parametres_import_pointe_noire.json`,
  `03_DONNEES_ENTREE/dqe/*.json` (squelettes vides), `ARCHIVES/DATASET_METADATA.json`,
  rapports de recette (run_recette_report.json).
- CSV vides places en sorties runtime : `05_RESULTATS/*.csv`,
  `06_ANALYSE_BI/dataset/*.csv` (0 octet).
- SQL de migrations/vues et documentation (docs/).

## RETIRE DU SUIVI - LOCAL/IGNORE

Fichiers retires de l'index Git (git rm --cached) mais conserves localement
et ignores via .gitignore (Lot 4) :

- 65 XLSX racine/resultats a provenance indeterminee (masters de reference,
  DQE_TEST, audits DQE, benchmarks, supplier registries, procurement, TCO, FOB,
  market, drift, governance, audit/reference-engine) dont
  `05_RESULTATS/audit_qualite_dqe.xlsx`.
- 2 PBIX : `06_ANALYSE_BI/MPEMBA_V2/SP2I_CAPEX_MPEMBA_V2.pbix`,
  `06_ANALYSE_BI/dashboards/SP2I_CAPEX_Dashboard.pbix`.
- 13 JSON d'artefacts devtools/audit : `AUDIT_REFERENCE_ENGINE.json` et
  `*_STATS.json` racine (12).

## A VERIFIER

- Classification proprietaire finale des fichiers retires (SYNTHETIQUE / INTERNE
  / CONFIDENTIEL) si une re-publication est envisagee.
- Contenu des PBIX (mode Import documente) hors depot.

## DONNEES DEJA PURGEES ANTERIEUREMENT

- 8 classeurs DQE/source des dossiers 03_DONNEES_ENTREE et 03_DONNEES_REFERENCE
  (purgés de l'historique public le 1er septembre 2026).
- Anciennes valeurs de connexion Neon remplacees par des placeholders
  (Lot 1) ; artefact d'audit Neon `neon_integrity_audit_result.json` retire
  du suivi.
