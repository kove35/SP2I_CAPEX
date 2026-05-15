from __future__ import annotations

import logging
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core import CalculateurCAPEX, DataCleaner, DecisionEngine, ProcurementEngine
from app.core.errors import SP2ICapexError, SimulationError
from app.core.logging_config import configure_simulation_logging
from app.repositories import RepositoryBPU, RepositoryMapping, RepositoryRun, RepositoryScenario, RepositorySimulation
from app.schemas import ScenarioRequest, SimulationRequest


RACINE = Path(__file__).resolve().parents[3]
configure_simulation_logging()
logger = logging.getLogger("sp2i.simulation")
error_logger = logging.getLogger("sp2i.errors")


class ServiceSimulation:
    """
    Cas d'usage applicatif pour la simulation CAPEX.

    Le service orchestre les couches :
    schemas Pydantic -> core metier -> repositories. Il ne contient pas les
    formules CAPEX elles-memes, mais decide quand les appeler.
    """

    def __init__(
        self,
        repository_bpu: RepositoryBPU | None = None,
        repository_mapping: RepositoryMapping | None = None,
        db: Session | None = None,
    ) -> None:
        self.repository_bpu = repository_bpu or RepositoryBPU(RACINE)
        self.repository_mapping = repository_mapping or RepositoryMapping(RACINE)
        self.db = db

    def simuler(self, demande: SimulationRequest) -> dict[str, Any]:
        lignes_entree = [item.model_dump(exclude_none=True) for item in demande.items]
        parametres = demande.parameters.model_dump(exclude_none=True)

        try:
            return self._simuler_lignes(
                lignes_entree,
                parametres=parametres,
                inclure_sensibilite=demande.inclure_sensibilite,
                mode=demande.mode,
                summary_only=demande.summary_only,
                return_lines=demande.return_lines,
                persist=demande.persist,
                scenario_name=demande.scenario_name,
                scenario_type=demande.scenario_type,
                scenario_description=demande.scenario_description,
                created_by=demande.created_by,
            )
        except SP2ICapexError as erreur:
            if self.db is not None:
                self.db.rollback()
            error_logger.error("Simulation error: %s | %s", erreur.code, erreur.message)
            return self._reponse_erreur(erreur, lignes_entree, demande.mode, demande.persist)
        except Exception as erreur:
            if self.db is not None:
                self.db.rollback()
            wrapped = SimulationError("Erreur inattendue pendant la simulation.", {"error": str(erreur)})
            error_logger.exception("Unexpected simulation error")
            return self._reponse_erreur(wrapped, lignes_entree, demande.mode, demande.persist)

    def simuler_source_courante(self) -> dict[str, Any]:
        """
        Compatibilite avec l'ancien endpoint `/import/optimize`.

        On lit encore le DQE normalise depuis le repository fichier, puis on
        ecrit le CSV historique attendu par Power BI et les scripts existants.
        """
        parametres = self.repository_mapping.lire_parametres_import()
        resultat = self._simuler_lignes(self.repository_bpu.lire_lignes_dqe(), parametres, mode="tolerant")
        self.repository_bpu.enregistrer_optimisation(resultat["lignes_export"])

        kpi = resultat["kpi"]
        return {
            "statut": "IMPORT_OPTIMISE",
            "lignes": kpi["lignes"],
            "montant_local": kpi["capex_local"],
            "capex_optimise": kpi["capex_optimise"],
            "economie_nette": kpi["economie_nette"],
            "fichier_resultat": str(self.repository_bpu.chemin_optimisation),
        }

    def analyser_scenarios(self, demande: ScenarioRequest) -> dict[str, Any]:
        lignes_entree = [item.model_dump(exclude_none=True) for item in demande.items]
        parametres = demande.parameters.model_dump(exclude_none=True)
        lignes_normalisees = DataCleaner(mode=demande.mode).normaliser_lignes(lignes_entree)
        calculateur = CalculateurCAPEX(parametres)
        return {
            "status": "SUCCESS" if lignes_normalisees else "EMPTY",
            "scenarios": calculateur.analyse_sensibilite(
                lignes_normalisees,
                demande.variations_landed_cost,
            ),
        }

    def _simuler_lignes(
        self,
        lignes_entree: list[dict[str, Any]],
        parametres: dict[str, Any] | None = None,
        inclure_sensibilite: bool = False,
        mode: str = "tolerant",
        summary_only: bool = False,
        return_lines: bool = True,
        persist: bool = False,
        scenario_name: str | None = None,
        scenario_type: str = "BASELINE",
        scenario_description: str = "",
        created_by: str = "system",
    ) -> dict[str, Any]:
        start = perf_counter()
        simulation_id = f"sim_{uuid4().hex}"
        run_id = f"run_{uuid4().hex}"
        scenario_id = f"scenario_{uuid4().hex}"

        cleaner = DataCleaner(mode=mode)
        lignes_normalisees = cleaner.normaliser_lignes(lignes_entree)
        calculateur = CalculateurCAPEX(parametres)
        lignes_calculees = calculateur.optimiser_lignes(lignes_normalisees)
        procurement_engine = ProcurementEngine()
        lignes_calculees = [procurement_engine.enrich_line(ligne) for ligne in lignes_calculees]
        decision_engine = DecisionEngine(parametres)
        lignes_calculees = [decision_engine.enrich_line(ligne) for ligne in lignes_calculees]
        kpi = calculateur.calculer_kpi(lignes_calculees)

        sensibilite = []
        if inclure_sensibilite:
            sensibilite = calculateur.analyse_sensibilite(lignes_normalisees, [-0.1, 0, 0.1])

        duration = round(perf_counter() - start, 4)
        logger.info(
            "simulation_id=%s run_id=%s mode=%s lignes_entree=%s lignes_calculees=%s capex_local=%s economie=%s duration=%s",
            simulation_id,
            run_id,
            mode,
            len(lignes_entree),
            len(lignes_calculees),
            kpi["capex_local"],
            kpi["economie_nette"],
            duration,
        )

        lignes_api = []
        if return_lines and not summary_only:
            lignes_api = [self._formater_ligne_api(ligne) for ligne in lignes_calculees]

        response = {
            "status": "SUCCESS" if lignes_calculees else "EMPTY",
            "kpi": kpi,
            "lignes": lignes_api,
            "lignes_export": lignes_calculees,
            "sensibilite": sensibilite,
            "metadata": {
                "simulation_id": simulation_id,
                "run_id": run_id,
                "scenario_id": scenario_id,
                "mode": mode,
                "lignes_entree": len(lignes_entree),
                "lignes_calculees": len(lignes_calculees),
                "temps_calcul_secondes": duration,
                "persist": persist,
            },
            "warnings": cleaner.warnings,
            "errors": [],
        }
        if persist:
            self._persist_simulation(
                response=response,
                lignes_calculees=lignes_calculees,
                parametres=parametres or {},
                scenario_name=scenario_name,
                scenario_type=scenario_type,
                scenario_description=scenario_description,
                created_by=created_by,
            )
        return response

    def _reponse_erreur(
        self,
        erreur: SP2ICapexError,
        lignes_entree: list[dict[str, Any]],
        mode: str,
        persist: bool,
    ) -> dict[str, Any]:
        return {
            "status": "ERROR",
            "kpi": {
                "lignes": 0,
                "capex_local": 0,
                "capex_import": 0,
                "capex_optimise": 0,
                "economie_nette": 0,
                "taux_economie": 0,
                "lignes_import": 0,
                "lignes_local": 0,
            },
            "lignes": [],
            "lignes_export": [],
            "sensibilite": [],
            "metadata": {
                "simulation_id": f"sim_{uuid4().hex}",
                "run_id": f"run_{uuid4().hex}",
                "scenario_id": f"scenario_{uuid4().hex}",
                "mode": mode,
                "lignes_entree": len(lignes_entree),
                "lignes_calculees": 0,
                "temps_calcul_secondes": 0,
                "persist": persist,
            },
            "warnings": [],
            "errors": [erreur.as_dict()],
        }

    def _persist_simulation(
        self,
        response: dict[str, Any],
        lignes_calculees: list[dict[str, Any]],
        parametres: dict[str, Any],
        scenario_name: str | None,
        scenario_type: str,
        scenario_description: str,
        created_by: str,
    ) -> None:
        if self.db is None:
            raise SimulationError(
                "Impossible de persister la simulation sans session PostgreSQL.",
                details={"hint": "Verifier l'injection FastAPI get_service_simulation."},
            )

        metadata = response["metadata"]
        scenario_uuid = metadata["scenario_id"].replace("scenario_", "")
        run_uuid = metadata["run_id"].replace("run_", "")
        simulation_uuid = metadata["simulation_id"].replace("sim_", "")
        scenario_repo = RepositoryScenario(self.db)
        run_repo = RepositoryRun(self.db)
        simulation_repo = RepositorySimulation(self.db)

        scenario_repo.create_scenario(
            scenario_id=scenario_uuid,
            scenario_nom=scenario_name or scenario_type,
            scenario_type=scenario_type,
            description=scenario_description,
            parameters=parametres,
            is_baseline=scenario_type == "BASELINE",
            created_by=created_by,
        )
        run_repo.create_run(
            run_id=run_uuid,
            scenario_id=scenario_uuid,
            rows_in=metadata["lignes_entree"],
            source_type="API",
        )
        rows_out = simulation_repo.save_simulation_lines(
            simulation_id=simulation_uuid,
            scenario_id=scenario_uuid,
            run_id=run_uuid,
            lignes=lignes_calculees,
        )
        run_repo.complete_run(
            run_id=run_uuid,
            rows_out=rows_out,
            rows_rejected=max(metadata["lignes_entree"] - rows_out, 0),
            warnings=response["warnings"],
            errors=response["errors"],
            duration_ms=int(metadata["temps_calcul_secondes"] * 1000),
            status=response["status"],
        )
        self.db.commit()

    def _formater_ligne_api(self, ligne: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_ligne": ligne.get("id_ligne"),
            "designation": ligne.get("designation", ""),
            "famille": ligne.get("famille", "default"),
            "lot": ligne.get("lot", ""),
            "quantite": ligne.get("QTE", 0),
            "pu_local": ligne.get("PU_LOCAL", 0),
            "pu_import_ht": ligne.get("PU_IMPORT_HT", 0),
            "capex_local": ligne.get("CAPEX_LOCAL", 0),
            "capex_import": ligne.get("CAPEX_IMPORT", 0),
            "capex_optimise": ligne.get("CAPEX_OPTIMISE", 0),
            "economie_nette": ligne.get("ECONOMIE_NETTE", 0),
            "taux_import": ligne.get("TAUX_IMPORT", 0),
            "decision_import": ligne.get("DECISION_IMPORT", "LOCAL"),
            "score_confiance": ligne.get("SCORE_CONFIANCE", 0),
            "decision_finale": ligne.get("DECISION_FINALE", ligne.get("DECISION_IMPORT", "LOCAL")),
            "decision_type": ligne.get("DECISION_TYPE", ""),
            "decision_score": ligne.get("FINAL_DECISION_SCORE", 0),
            "decision_confidence": ligne.get("DECISION_CONFIDENCE", ""),
            "decision_reason": ligne.get("DECISION_REASON", {}),
            "global_risk_score": ligne.get("GLOBAL_RISK_SCORE", 0),
            "risk_level": ligne.get("RISK_LEVEL", ""),
            "lead_time_days": ligne.get("TOTAL_IMPORT_LEAD_TIME", 0),
            "cashflow_score": ligne.get("CASHFLOW_SCORE", 0),
            "moq_risk_score": ligne.get("MOQ_RISK_SCORE", 0),
            "complexity_score": ligne.get("IMPORT_COMPLEXITY_SCORE", 0),
            "procurement_analysis": ligne.get("PROCUREMENT_ANALYSIS", {}),
        }
