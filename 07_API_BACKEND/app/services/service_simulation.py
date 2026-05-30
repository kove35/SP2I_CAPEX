from __future__ import annotations

import logging
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.audit_trail_engine import AuditTrailEngine
from app.core.calculator import CalculateurCAPEX
from app.core.cleaner import DataCleaner
from app.core.decision_engine_v2 import DecisionEngineV2
from app.core.errors import SP2ICapexError, SimulationError, DataQualityError
from app.core.explainability_engine import ExplainabilityEngine
from app.core.kpi_engine import KPIEngine
from app.core.logistics_engine import LogisticsEngine
from app.core.logging_config import configure_simulation_logging
from app.core.parameter_registry_engine import ParameterRegistryEngine
from app.core.procurement_enrichment_engine import ProcurementEnrichmentEngine
from app.core.scenario_engine import ScenarioEngine
from app.core.scenario_persistence_engine import ScenarioPersistenceEngine
from app.repositories import RepositoryBPU, RepositoryMapping
from app.schemas import ScenarioRequest, SimulationRequest
from app.services.workflow_events import log_workflow_event


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
        if not lignes_entree:
            lignes_entree = self._load_fact_metre_for_simulation(project_id=demande.project_id)
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
                project_id=demande.project_id,
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
        scenario_engine = ScenarioEngine(parametres)
        return {
            "status": "SUCCESS" if lignes_normalisees else "EMPTY",
            "scenarios": scenario_engine.analyse_landed_cost_variations(
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
        project_id: int | None = None,
    ) -> dict[str, Any]:
        start = perf_counter()
        simulation_id = f"sim_{uuid4().hex}"
        run_id = f"run_{uuid4().hex}"
        scenario_id = f"scenario_{uuid4().hex}"

        # Trace structure to collect observability data at each pipeline step
        trace: dict[str, Any] = {
            "fact_metre": {"count": len(lignes_entree), "capex": 0.0},
            "normalisation": {},
            "optimisation": {},
            "procurement": {},
            "logistics": {},
            "decision": {},
            "scenario_final": {},
        }

        def _extract_capex_from_raw(l: dict[str, Any]) -> float:
            # Best-effort extraction of monetary value from heterogeneous keys
            for key in ("prix_total_ht", "prix_total", "montant_local", "CAPEX_LOCAL", "capex_local", "montant_total"):
                try:
                    val = l.get(key)
                except Exception:
                    val = None
                if val is None:
                    continue
                try:
                    return float(val)
                except Exception:
                    continue
            # fallback to quantite * prix_unitaire if available
            try:
                q = float(l.get("quantite") or l.get("QTE") or 0)
                pu = float(l.get("prix_unitaire_ht") or l.get("PU_LOCAL") or l.get("pu_local") or 0)
                return q * pu
            except Exception:
                return 0.0

        # initial capex from input
        try:
            trace["fact_metre"]["capex"] = round(sum(_extract_capex_from_raw(r) for r in lignes_entree), 2)
        except Exception:
            trace["fact_metre"]["capex"] = 0.0

        cleaner = DataCleaner(mode=mode)

        def _build_rejected_row(idx: int, raw: dict[str, Any], reason: str | None = None) -> dict[str, Any]:
            ligne_info = None
            if cleaner.warnings:
                matching = [w for w in cleaner.warnings if w.get("index") == idx]
                if matching:
                    ligne_info = matching[-1].get("ligne") if isinstance(matching[-1].get("ligne"), dict) else None
                    reason = reason or matching[-1].get("code")

            id_ligne = (
                ligne_info.get("id_ligne")
                if ligne_info
                else raw.get("id_ligne") or raw.get("ID_LIGNE")
            )
            lot_val = (
                ligne_info.get("lot") if ligne_info else raw.get("lot") or raw.get("LOT")
            )
            designation_val = (
                ligne_info.get("designation")
                if ligne_info
                else raw.get("designation") or raw.get("DESIGNATION")
            )
            quantite_val = None
            prix_total_val = None
            try:
                quantite_val = float(raw.get("quantite") or raw.get("QTE") or 0)
            except Exception:
                quantite_val = raw.get("quantite") or raw.get("QTE")
            try:
                prix_total_val = float(raw.get("prix_total_ht") or raw.get("prix_total") or raw.get("montant_local") or 0)
            except Exception:
                prix_total_val = raw.get("prix_total_ht") or raw.get("prix_total") or raw.get("montant_local")
            capex_val = None
            try:
                capex_val = float(raw.get("CAPEX_LOCAL") or raw.get("capex_local") or prix_total_val or 0)
            except Exception:
                capex_val = prix_total_val
            return {
                "index": idx,
                "id_ligne": id_ligne,
                "lot": lot_val,
                "designation": designation_val,
                "raison": reason or "UNKNOWN",
                "quantite": quantite_val,
                "prix_total": prix_total_val,
                "capex": capex_val,
            }

        # manual per-line normalization so we can record per-line rejections and reasons
        lignes_normalisees: list[dict[str, Any]] = []
        rejected_indices: list[int] = []
        rejected_rows: list[dict[str, Any]] = []
        for idx, raw in enumerate(lignes_entree, start=1):
            try:
                ln = cleaner.normaliser_ligne(raw, idx)
                if ln:
                    lignes_normalisees.append(ln)
                else:
                    rejected_indices.append(idx)
                    rejected_rows.append(_build_rejected_row(idx, raw))
            except DataQualityError as dq:
                # DataCleaner already recorded the warning in cleaner.warnings
                rejected_indices.append(idx)
                details = dq.details if hasattr(dq, "details") else {}
                reason = details.get("code") or (details.get("message") if isinstance(details, dict) else str(dq))
                rejected_rows.append(_build_rejected_row(idx, raw, reason=reason))
            except Exception:
                # Non-data-quality exception during normalization: record and continue
                logger.exception("Unexpected error while normalising line %s", idx)
                rejected_indices.append(idx)
                rejected_rows.append(_build_rejected_row(idx, raw, reason="UNEXPECTED_ERROR"))

        reasons: dict[str, dict[str, Any]] = {}
        for w in cleaner.warnings:
            code = w.get("code")
            reasons.setdefault(code, {"count": 0, "capex": 0.0, "examples": []})
            reasons[code]["count"] += 1
            widx = (w.get("index") or 1) - 1
            if 0 <= widx < len(lignes_entree):
                reasons[code]["capex"] += _extract_capex_from_raw(lignes_entree[widx])
                if len(reasons[code]["examples"]) < 3:
                    reasons[code]["examples"].append(
                        lignes_entree[widx].get("id_ligne") or lignes_entree[widx].get("lot") or lignes_entree[widx].get("designation")
                    )

        trace["normalisation"] = {
            "kept": len(lignes_normalisees),
            "rejected": len(lignes_entree) - len(lignes_normalisees),
            "reasons": reasons,
            "rejected_rows": rejected_rows,
        }

        # After attempting normalization of all lines, if strict mode and we have rejections, return an ERROR with full trace
        if cleaner.mode == "strict" and rejected_rows:
            duration = round(perf_counter() - start, 4)
            logger.info("simulation aborted strict mode after full pass: kept=%s rejected=%s", len(lignes_normalisees), len(lignes_entree) - len(lignes_normalisees))
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
                    "simulation_id": simulation_id,
                    "run_id": run_id,
                    "scenario_id": scenario_id,
                    "mode": mode,
                    "lignes_entree": len(lignes_entree),
                    "lignes_calculees": 0,
                    "line_counts": {
                        "dqe": len(lignes_entree),
                        "simulees": len(lignes_normalisees),
                    },
                    "temps_calcul_secondes": duration,
                    "persist": persist,
                    "project_id": project_id,
                },
                "warnings": cleaner.warnings,
                "errors": [r for r in (dq.as_dict() if hasattr(dq, "as_dict") else {"message": str(dq)} for dq in [DataQualityError("aggregated")])],
                "trace": trace,
            }

        calculateur = CalculateurCAPEX(parametres)
        # OPTIMISATION
        lignes_optim = calculateur.optimiser_lignes(lignes_normalisees)
        # dropped by optimiser (e.g., missing designation)
        dropped_by_optim = len(lignes_normalisees) - len(lignes_optim)
        # eligible/import vs local according to optimiser decision
        optim_by_decision = {"IMPORT": 0, "LOCAL": 0, "OTHER": 0}
        optim_capex = {"IMPORT": 0.0, "LOCAL": 0.0, "OTHER": 0.0}
        for l in lignes_optim:
            d = (l.get("DECISION") or l.get("DECISION_IMPORT") or "").upper()
            if d not in optim_by_decision:
                d = "OTHER"
            optim_by_decision[d] += 1
            optim_capex[d] += float(l.get("CAPEX_LOCAL") or l.get("MONTANT_LOCAL") or 0)

        trace["optimisation"] = {
            "kept": len(lignes_optim),
            "dropped": dropped_by_optim,
            "by_decision": optim_by_decision,
            "capex_by_decision": {k: round(v, 2) for k, v in optim_capex.items()},
        }

        # PROCUREMENT
        procurement_engine = ProcurementEnrichmentEngine()
        lignes_after_proc = [procurement_engine.enrich_line(ligne) for ligne in lignes_optim]
        # Build simple buckets for importability / procurement score to explain reductions
        buckets = {">=75": 0, ">=50": 0, ">=25": 0, "<25": 0}
        proc_capex = 0.0
        for l in lignes_after_proc:
            score = float(l.get("IMPORTABILITY_SCORE") or l.get("IMPORTABILITY_SCORE") or 0)
            proc_capex += float(l.get("CAPEX_LOCAL") or l.get("MONTANT_LOCAL") or 0)
            if score >= 75:
                buckets[">=75"] += 1
            elif score >= 50:
                buckets[">=50"] += 1
            elif score >= 25:
                buckets[">=25"] += 1
            else:
                buckets["<25"] += 1

        trace["procurement"] = {"total": len(lignes_after_proc), "buckets_importability": buckets, "capex_total": round(proc_capex, 2)}

        # LOGISTICS
        logistics_engine = LogisticsEngine()
        lignes_after_log = [logistics_engine.enrich_line(ligne) for ligne in lignes_after_proc]
        # Count by fill_rate and delivery risk
        fill_buckets = {">=0.8": 0, ">=0.5": 0, ">=0.35": 0, "<0.35": 0}
        risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        for l in lignes_after_log:
            fr = float(l.get("FILL_RATE") or 0)
            if fr >= 0.8:
                fill_buckets[">=0.8"] += 1
            elif fr >= 0.5:
                fill_buckets[">=0.5"] += 1
            elif fr >= 0.35:
                fill_buckets[">=0.35"] += 1
            else:
                fill_buckets["<0.35"] += 1
            dr = str(l.get("DELIVERY_RISK") or "").upper()
            if "HIGH" in dr or "ELEVE" in dr.upper():
                risk_counts["HIGH"] += 1
            elif "MED" in dr or "MOYEN" in dr.upper():
                risk_counts["MEDIUM"] += 1
            else:
                risk_counts["LOW"] += 1

        trace["logistics"] = {"total": len(lignes_after_log), "fill_buckets": fill_buckets, "delivery_risk": risk_counts}

        # DECISION
        decision_engine = DecisionEngineV2({**parametres, "scenario_type": scenario_type})
        lignes_after_decision = [decision_engine.enrich_line(ligne) for ligne in lignes_after_log]
        decision_counts: dict[str, int] = {"IMPORT": 0, "LOCAL": 0, "HYBRIDE": 0, "REJETE": 0, "OTHER": 0}
        decision_capex: dict[str, float] = {k: 0.0 for k in decision_counts}
        for l in lignes_after_decision:
            d = str(l.get("DECISION_FINALE") or l.get("DECISION") or "").upper()
            if d not in decision_counts:
                d = "OTHER"
            decision_counts[d] += 1
            decision_capex[d] += float(l.get("CAPEX_OPTIMISE") or l.get("CAPEX_LOCAL") or 0)

        trace["decision"] = {"counts": decision_counts, "capex_by_decision": {k: round(v, 2) for k, v in decision_capex.items()}}

        # Enrich audit and explanation
        parameter_registry = ParameterRegistryEngine(parametres)
        audit_engine = AuditTrailEngine(parameter_registry)
        explainability_engine = ExplainabilityEngine()
        lignes_calculees = [
            {
                **ligne,
                "AUDIT_TRAIL": audit_engine.build_line_audit(ligne),
                "EXPLANATION": explainability_engine.explain_line(ligne),
            }
            for ligne in lignes_after_decision
        ]

        parameter_registry = ParameterRegistryEngine(parametres)
        audit_engine = AuditTrailEngine(parameter_registry)
        explainability_engine = ExplainabilityEngine()
        lignes_calculees = [
            {
                **ligne,
                "AUDIT_TRAIL": audit_engine.build_line_audit(ligne),
                "EXPLANATION": explainability_engine.explain_line(ligne),
            }
            for ligne in lignes_calculees
        ]

        kpi = calculateur.calculer_kpi(lignes_calculees)
        kpi["procurement"] = KPIEngine().compute_procurement_kpi(lignes_calculees)
        self._enrichir_kpi_lignes(kpi, lignes_entree, lignes_normalisees, lignes_calculees)

        # scenario final summary
        trace["scenario_final"] = {"final_count": len(lignes_calculees), "capex_final": round(kpi.get("capex_optimise", 0), 2)}

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
                "line_counts": {
                    "dqe": kpi.get("lignes_dqe", len(lignes_entree)),
                    "simulees": kpi.get("lignes_simulees", len(lignes_calculees)),
                    "importables": kpi.get("lignes_importables", 0),
                    "retenues": kpi.get("lignes_retenues", 0),
                    "arbitrees": kpi.get("lignes_arbitrees", 0),
                },
                "temps_calcul_secondes": duration,
                "persist": persist,
                "project_id": project_id,
            },
            "warnings": cleaner.warnings,
            "errors": [],
            "trace": trace,
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
                project_id=project_id,
            )
        return response

    def _load_fact_metre_for_simulation(self, project_id: int | None = None) -> list[dict[str, Any]]:
        if self.db is None:
            return self.repository_bpu.lire_lignes_dqe()
        where_sql = "AND projet_id = :project_id" if project_id is not None else ""
        rows = self.db.execute(
            text(
                f"""
                SELECT
                    id_ligne,
                    designation,
                    quantite,
                    COALESCE(capex_local, prix_total_ht, 0) AS prix_total_ht,
                    COALESCE(pu_local, 0) AS prix_unitaire_ht,
                    COALESCE(famille, 'default') AS famille,
                    lot,
                    batiment,
                    niveau,
                    unite,
                    COALESCE(pu_import, 0) AS prix_fob,
                    COALESCE(risque, '') AS project_criticality,
                    projet_id
                FROM fact_metre
                WHERE COALESCE(designation, '') <> ''
                  {where_sql}
                ORDER BY id_ligne
                LIMIT 5000
                """
            ),
            {"project_id": project_id} if project_id is not None else {},
        ).mappings().all()
        if rows or project_id is None:
            return [dict(row) for row in rows]
        return self._load_fact_metre_for_simulation(project_id=None)

    def _enrichir_kpi_lignes(
        self,
        kpi: dict[str, Any],
        lignes_entree: list[dict[str, Any]],
        lignes_normalisees: list[dict[str, Any]],
        lignes_calculees: list[dict[str, Any]],
    ) -> None:
        procurement = kpi.get("procurement") or {}
        lignes_importables = int(procurement.get("LIGNES_IMPORTABLES") or 0)
        lignes_retenues = sum(1 for ligne in lignes_calculees if str(ligne.get("DECISION_FINALE") or ligne.get("DECISION_IMPORT") or "").upper() == "IMPORT")
        lignes_arbitrees = sum(1 for ligne in lignes_calculees if str(ligne.get("DECISION_FINALE") or ligne.get("DECISION_IMPORT") or "").strip())
        kpi.update(
            {
                "lignes_dqe": len(lignes_entree),
                "lignes_simulees": len(lignes_normalisees),
                "lignes_importables": lignes_importables,
                "lignes_retenues": lignes_retenues,
                "lignes_arbitrees": lignes_arbitrees,
            }
        )

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
        project_id: int | None = None,
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
        persistence_engine = ScenarioPersistenceEngine(self.db)
        persistence_engine.persist_scenario(
            scenario_name=scenario_name or scenario_type,
            scenario_type=scenario_type,
            parameters=parametres,
            created_by=created_by,
            scenario_id=scenario_uuid,
            run_id=run_uuid,
            simulation_id=simulation_uuid,
            lignes=lignes_calculees,
            description=scenario_description,
            is_baseline=scenario_type == "BASELINE",
            warnings=response["warnings"],
            errors=response["errors"],
            duration_ms=int(metadata["temps_calcul_secondes"] * 1000),
            status=response["status"],
            project_id=project_id,
        )
        if project_id is not None:
            log_workflow_event(
                self.db,
                project_id=project_id,
                event_type="SIMULATION_COMPLETED",
                entity_type="fact_simulation",
                entity_id=metadata["scenario_id"],
                previous_status="A_SIMULER",
                new_status="SIMULE",
                message="Simulation CAPEX executee et rattachee au workflow projet.",
                metadata={
                    "simulation_id": metadata["simulation_id"],
                    "run_id": metadata["run_id"],
                    "scenario_id": metadata["scenario_id"],
                    "lignes_calculees": metadata["lignes_calculees"],
                },
            )

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
            "container_strategy": ligne.get("CONTAINER_STRATEGY", ""),
            "shipment_strategy": ligne.get("SHIPMENT_STRATEGY", ""),
            "fill_rate": ligne.get("FILL_RATE", 0),
            "shipment_cost": ligne.get("SHIPMENT_COST", 0),
            "lead_time_total": ligne.get("LEAD_TIME_TOTAL", 0),
            "storage_cost": ligne.get("STORAGE_COST", 0),
            "delivery_risk": ligne.get("DELIVERY_RISK", ""),
            "logistics_analysis": ligne.get("LOGISTICS_ANALYSIS", {}),
            "importability_score": ligne.get("IMPORTABILITY_SCORE", 0),
            "sourcing_coverage": ligne.get("SOURCING_COVERAGE", 0),
            "procurement_score": ligne.get("PROCUREMENT_SCORE", 0),
            "supplier_maturity_score": ligne.get("SUPPLIER_MATURITY_SCORE", 0),
            "procurement_maturity_score": ligne.get("PROCUREMENT_MATURITY_SCORE", 0),
            "hidden_savings_potential": ligne.get("HIDDEN_SAVINGS_POTENTIAL", 0),
            "import_confidence_score": ligne.get("IMPORT_CONFIDENCE_SCORE", 0),
            "decision_scenario": ligne.get("DECISION_SCENARIO", "BASELINE"),
            "audit_trail": ligne.get("AUDIT_TRAIL", {}),
            "explanation": ligne.get("EXPLANATION", {}),
        }
