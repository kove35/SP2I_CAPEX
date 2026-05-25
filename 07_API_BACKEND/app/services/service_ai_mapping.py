from __future__ import annotations

import logging
from typing import Any

from app.ai.excel_mapping_rules import (
    CHAMPS_DQE_MINIMUM,
    REGLES_MAPPING_EXCEL,
    normaliser_libelle,
)
from app.core import clean_lot, clean_niveau, nettoyer_nombre
from app.core.errors import PipelineIntegrityError
from app.core.ai import AIExcelOrchestrator
from app.governance.dqe_column_validator import validate_dqe_columns
from app.governance.dqe_issue_builder import build_dqe_issue, summarize_dqe_issues
from app.governance.rules import summarize_classified_rows
from app.repositories import RepositoryExcel
from app.schemas import SimulationItem, SimulationRequest
from app.services.service_simulation import ServiceSimulation
from app.utils.data_lineage import DataLineageTracker


logger = logging.getLogger("sp2i.pipeline")


class ServiceAIMapping:
    """
    Service d'analyse intelligente de fichiers Excel.

    Version progressive : l'intelligence est heuristique, transparente et
    testable. Un LLM pourra plus tard enrichir `analyser_excel`, mais il devra
    rester dans ce service et ne jamais calculer le CAPEX critique.
    """

    def __init__(
        self,
        repository_excel: RepositoryExcel | None = None,
        service_simulation: ServiceSimulation | None = None,
    ) -> None:
        self.repository_excel = repository_excel or RepositoryExcel()
        self.service_simulation = service_simulation or ServiceSimulation()
        self.ai_orchestrator = AIExcelOrchestrator()

    BLACKLIST_ANALYTICS_SHEETS = {
        "ANALYSE_SPATIALE",
        "RECAP",
        "RECAP_LOTS",
        "SYNTHESE",
        "SYNTHÈSE",
        "TABLEAU_BORD",
        "STATISTIQUES",
        "DASHBOARD",
    }

    def analyser_excel(self, contenu: bytes, nom_fichier: str, preview_limit: int = 25) -> dict[str, Any]:
        lineage = DataLineageTracker("excel_ai_mapping")
        feuilles = self.repository_excel.lire_workbook(contenu, nom_fichier)
        lineage.track("excel.workbook_loaded", rows_out=sum(len(lignes) for lignes in feuilles.values()), feuilles=list(feuilles))

        analyses = [self._analyser_feuille(nom, lignes) for nom, lignes in feuilles.items()]
        analyses_triees = sorted(analyses, key=lambda analyse: analyse["score_dqe"], reverse=True)
        meilleure_analyse = analyses_triees[0] if analyses_triees else None

        lignes_preview: list[dict[str, Any]] = []
        simulation_preview: dict[str, Any] | None = None

        ai_payload: dict[str, Any] = {}

        if meilleure_analyse and meilleure_analyse["score_dqe"] > 0:
            analyses_retenues, sheet_selection = self._selectionner_feuilles_metier(analyses_triees, feuilles)
            parse_result = self._parser_analyses_retenues(feuilles, analyses_retenues, meilleure_analyse, sheet_selection)
            lignes_completes = parse_result["lignes_normalisees"]
            lignes_preview = lignes_completes[:preview_limit]
            simulation_preview = self._simuler_preview(lignes_preview)
            lineage.audit_lots("excel.normalized_lots", lignes_completes)
            lineage.track(
                "ai.hybrid_interpretation",
                rows_in=len(parse_result["classified_rows"]),
                rows_out=len(lignes_completes),
                anomalies=len(parse_result["anomalies"]),
                confidence=parse_result["confidence"].get("global_confidence"),
            )
            ai_payload = parse_result

        return {
            "status": "SUCCESS" if meilleure_analyse else "EMPTY",
            "fichier": nom_fichier,
            "feuille_recommandee": meilleure_analyse["feuille"] if meilleure_analyse else None,
            "analyses": analyses_triees,
            "lignes_normalisees_preview": lignes_preview,
            "simulation_preview": simulation_preview,
            "ai_preview": ai_payload.get("intelligent_preview"),
            "ai_confidence": ai_payload.get("confidence"),
            "ai_anomalies": ai_payload.get("anomalies", []),
            "dqe_issues": ai_payload.get("dqe_issues", []),
            "dqe_issues_summary": ai_payload.get("dqe_issues_summary", {}),
            "ai_classified_rows": ai_payload.get("classified_rows", [])[:preview_limit],
            "ai_suggestions": self._generer_suggestions(meilleure_analyse, ai_payload),
            "lineage": lineage.as_dict(),
        }

    def extraire_lignes_normalisees(self, contenu: bytes, nom_fichier: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """
        Extrait toutes les lignes metier Excel pour alimenter le pipeline.

        Contrairement a `analyser_excel`, cette methode n'est pas une preview :
        elle est destinee a sauvegarder le JSON source complet avant calcul.
        """
        lineage = DataLineageTracker("excel_to_pipeline")
        feuilles = self.repository_excel.lire_workbook(contenu, nom_fichier)
        lineage.track("excel.workbook_loaded", rows_out=sum(len(lignes) for lignes in feuilles.values()), fichier=nom_fichier)
        analyses = [self._analyser_feuille(nom, lignes) for nom, lignes in feuilles.items()]
        meilleure_analyse = max(analyses, key=lambda analyse: analyse["score_dqe"])
        analyses_retenues, sheet_selection = self._selectionner_feuilles_metier(analyses, feuilles)
        parse_result = self._parser_analyses_retenues(feuilles, analyses_retenues, meilleure_analyse, sheet_selection)
        lignes = parse_result["lignes_normalisees"]
        lineage.audit_lots("excel.pipeline_lots", lignes)
        lineage.track(
            "ai.pipeline_interpretation",
            rows_in=len(parse_result["classified_rows"]),
            rows_out=len(lignes),
            anomalies=len(parse_result["anomalies"]),
            confidence=parse_result["confidence"].get("global_confidence"),
        )
        return lignes, {
            "fichier": nom_fichier,
            "feuille_recommandee": meilleure_analyse["feuille"],
            "analyse": meilleure_analyse,
            "ai_preview": parse_result["intelligent_preview"],
            "ai_confidence": parse_result["confidence"],
            "ai_anomalies": parse_result["anomalies"],
            "dqe_issues": parse_result["dqe_issues"],
            "dqe_issues_summary": parse_result["dqe_issues_summary"],
            "sheet_selection": sheet_selection,
            "lineage": lineage.as_dict(),
        }

    def _analyser_feuille(self, feuille: str, lignes: list[list[Any]]) -> dict[str, Any]:
        return self.ai_orchestrator.analyze_sheet(feuille, lignes)

    def _analyser_feuille_legacy(self, feuille: str, lignes: list[list[Any]]) -> dict[str, Any]:
        candidats = []
        for index, ligne in enumerate(lignes[:30], start=1):
            cellules_non_vides = [valeur for valeur in ligne if valeur not in (None, "")]
            if len(cellules_non_vides) < 3:
                continue

            mapping = self._mapper_colonnes(ligne)
            champs_detectes = {item["champ_standard"] for item in mapping}
            score = self._scorer_feuille(champs_detectes, mapping)
            candidats.append((score, index, mapping))

        if not candidats:
            return {
                "feuille": feuille,
                "ligne_entete": None,
                "score_dqe": 0,
                "lignes_detectees": 0,
                "mapping": [],
                "avertissements": ["Aucune ligne d'en-tete exploitable detectee."],
            }

        score, ligne_entete, mapping = max(candidats, key=lambda item: item[0])
        avertissements = self._avertissements_mapping(mapping)

        return {
            "feuille": feuille,
            "ligne_entete": ligne_entete,
            "score_dqe": round(score, 2),
            "lignes_detectees": self._compter_lignes_donnees(lignes, ligne_entete),
            "mapping": mapping,
            "avertissements": avertissements,
        }

    def _generer_suggestions(self, analyse: dict[str, Any] | None, ai_payload: dict[str, Any]) -> dict[str, Any]:
        if not analyse:
            return {
                "mapping": [],
                "human_validation_required": True,
                "next_actions": ["Verifier manuellement la structure du fichier."],
            }

        confidence = ai_payload.get("confidence") or {}
        ambiguous = [item for item in analyse.get("mapping", []) if item.get("confiance", 0) < 0.75]
        next_actions = []
        if ambiguous:
            next_actions.append("Valider les colonnes ambigues avant synchronisation.")
        if ai_payload.get("anomalies"):
            next_actions.append("Controler les anomalies detectees par le moteur IA.")
        if not next_actions:
            next_actions.append("La preview est exploitable pour synchronisation apres controle humain.")

        return {
            "mapping": analyse.get("mapping", []),
            "ambiguous_columns": ambiguous,
            "human_validation_required": confidence.get("needs_human_validation", True),
            "next_actions": next_actions,
        }

    def _selectionner_feuilles_metier(
        self,
        analyses: list[dict[str, Any]],
        feuilles: dict[str, list[list[Any]]],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """
        Selectionne les feuilles autorisees a alimenter FACT_METRE.

        Regle forte : une feuille `METRE` DQE prime sur les autres. Les feuilles
        de recap, dashboard ou analytics peuvent aider a comprendre le fichier,
        mais ne doivent jamais devenir la source metier principale.
        """
        evaluations = [self._evaluer_feuille_fact(analyse, feuilles.get(analyse["feuille"], [])) for analyse in analyses]
        ignored = [
            evaluation
            for evaluation in evaluations
            if evaluation["is_blacklisted"] or not evaluation["is_fact_candidate"]
        ]

        metre = [
            evaluation
            for evaluation in evaluations
            if evaluation["normalized_name"] == "METRE"
            and not evaluation["is_blacklisted"]
            and evaluation["document_type"] in {"DQE", "METRE"}
        ]
        if metre:
            best = max(metre, key=lambda item: item["fact_score"])
            selected_names = {best["sheet_name"]}
            reason = "Priorite absolue a la feuille METRE pour FACT_METRE."
        else:
            candidates = [
                evaluation
                for evaluation in evaluations
                if evaluation["is_fact_candidate"]
                and not evaluation["is_blacklisted"]
                and evaluation["fact_score"] >= 0.35
            ]
            if not candidates:
                candidates = [
                    evaluation
                    for evaluation in evaluations
                    if not evaluation["is_blacklisted"]
                    and evaluation["document_type"] in {"DQE", "METRE"}
                ]
            selected_names = {
                item["sheet_name"]
                for item in candidates
                if item["fact_score"] >= 0.35
            }
            reason = "Selection par score qualite feuille detaillee."

        retenues = [analyse for analyse in analyses if analyse["feuille"] in selected_names]
        if not retenues and analyses:
            fallback = next((analyse for analyse in analyses if not self._is_blacklisted_sheet(analyse["feuille"])), analyses[0])
            retenues = [fallback]
            selected_names = {fallback["feuille"]}
            reason = "Fallback controle : aucune feuille detaillee forte detectee."

        selection = {
            "source_fact_metre": sorted(selected_names),
            "reason": reason,
            "evaluations": evaluations,
            "ignored_sheets": ignored,
            "blacklist_active": sorted(self.BLACKLIST_ANALYTICS_SHEETS),
        }
        logger.info("FACT_METRE source selected: %s | %s", selection["source_fact_metre"], reason)
        for ignored_sheet in ignored:
            if ignored_sheet["is_blacklisted"]:
                logger.info("%s ignored (analytics sheet)", ignored_sheet["sheet_name"])
        return retenues, selection

    def _parser_analyses_retenues(
        self,
        feuilles: dict[str, list[list[Any]]],
        analyses: list[dict[str, Any]],
        analyse_reference: dict[str, Any],
        sheet_selection: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        lignes: list[dict[str, Any]] = []
        classified_rows: list[dict[str, Any]] = []
        anomalies: list[dict[str, Any]] = []
        rows_in = 0

        for analyse in analyses:
            sheet_rows = feuilles[analyse["feuille"]]
            rows_in += max(len(sheet_rows) - int(analyse.get("ligne_entete") or 0), 0)
            parse_result = self.ai_orchestrator.parse_and_enrich(sheet_rows, analyse)
            lignes.extend(parse_result["lignes_normalisees"])
            classified_rows.extend(
                {**row, "feuille": analyse["feuille"]}
                for row in parse_result["classified_rows"]
            )
            anomalies.extend(
                {**anomaly, "feuille": analyse["feuille"]}
                for anomaly in parse_result["anomalies"]
            )

        confidence = self.ai_orchestrator.confidence_engine.score(
            analyse_reference,
            lignes,
            anomalies,
            classified_rows,
        )
        governance_summary = summarize_classified_rows(classified_rows)
        confidence["governance_quality"] = governance_summary
        confidence["trust_score"] = self._calculer_trust_score_global(governance_summary)
        confidence["quality_taxonomy"] = "DATA_QUALITY_GOVERNANCE"
        dqe_issues = self._collecter_issues_dqe(feuilles, analyses, classified_rows, anomalies)
        confidence["dqe_issues_summary"] = summarize_dqe_issues(dqe_issues)
        intelligent_preview = self.ai_orchestrator.preview_generator.generate(
            lignes,
            analyse_reference,
            anomalies,
            confidence,
        )
        intelligent_preview["sheets_used"] = [analyse["feuille"] for analyse in analyses]
        intelligent_preview["source_fact_metre"] = (sheet_selection or {}).get("source_fact_metre", [])
        intelligent_preview["governance_quality"] = governance_summary
        intelligent_preview["dqe_issues_summary"] = confidence["dqe_issues_summary"]
        intelligent_preview["analytics_state"] = "LIVE"

        self._valider_integrite_pipeline(rows_in, lignes, classified_rows, sheet_selection, governance_summary)

        return {
            "lignes_normalisees": lignes,
            "classified_rows": classified_rows,
            "anomalies": anomalies,
            "confidence": confidence,
            "intelligent_preview": intelligent_preview,
            "sheet_selection": sheet_selection or {},
            "governance_quality": governance_summary,
            "dqe_issues": dqe_issues,
            "dqe_issues_summary": confidence["dqe_issues_summary"],
        }

    def _collecter_issues_dqe(
        self,
        feuilles: dict[str, list[list[Any]]],
        analyses: list[dict[str, Any]],
        classified_rows: list[dict[str, Any]],
        anomalies: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []

        if not feuilles or not any(feuilles.values()):
            issues.append(build_dqe_issue("FILE_EMPTY"))
            return issues

        if not analyses:
            issues.append(
                build_dqe_issue(
                    "DQE_SHEET_NOT_FOUND",
                    available_columns=[],
                    expected_aliases=["METRE", "DQE", "BUDGET", "DEVIS", "QUANTITATIF"],
                )
            )
            return issues

        for analyse in analyses:
            sheet_name = analyse.get("feuille")
            sheet_rows = feuilles.get(sheet_name, [])
            header_line = int(analyse.get("ligne_entete") or 0)
            header_row = sheet_rows[header_line - 1] if header_line and header_line <= len(sheet_rows) else []
            if not header_line:
                issues.append(build_dqe_issue("HEADER_NOT_FOUND", sheet_name=sheet_name))
                continue
            issues.extend(validate_dqe_columns(header_row, analyse.get("mapping", []), str(sheet_name or "")))

        issues.extend(self._issues_lignes_classifiees(classified_rows))
        issues.extend(self._issues_anomalies_normalisees(anomalies))
        return self._dedupliquer_issues(issues)

    def _issues_lignes_classifiees(self, classified_rows: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        for row in classified_rows:
            row_type = str(row.get("row_type") or "")
            if row_type in {"vide", "lot", "total", "ratio_analytics"}:
                if len(issues) >= limit:
                    continue
                issues.append(
                    build_dqe_issue(
                        "STRUCTURAL_ROW_IGNORED",
                        sheet_name=row.get("feuille"),
                        line_number=row.get("row_index"),
                        detected_value=row.get("raw_text"),
                        row_type=row_type,
                        reason=row.get("reason"),
                    )
                )
            elif row_type == "inconnu":
                issues.append(
                    build_dqe_issue(
                        "ARTICLE_LINE_NOT_NORMALIZED",
                        sheet_name=row.get("feuille"),
                        line_number=row.get("row_index"),
                        detected_value=row.get("raw_text"),
                        reason=row.get("reason"),
                    )
                )
        return issues

    def _issues_anomalies_normalisees(self, anomalies: list[dict[str, Any]]) -> list[dict[str, Any]]:
        mapping = {
            "quantite_incoherente": "ZERO_QUANTITY",
            "prix_absent": "EMPTY_PRICE",
            "doublon_possible": "DUPLICATE_ARTICLE_LINE",
            "prix_anormal": "LINE_AMOUNT_OUTLIER",
        }
        issues = []
        for anomaly in anomalies:
            issue_type = mapping.get(str(anomaly.get("anomaly_type") or ""))
            if not issue_type:
                continue
            issues.append(
                build_dqe_issue(
                    issue_type,
                    line_number=anomaly.get("line_id"),
                    detected_value=anomaly.get("reason"),
                    message=anomaly.get("reason"),
                    source="normalized_anomaly_detector",
                )
            )
        return issues

    def _dedupliquer_issues(self, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped: list[dict[str, Any]] = []
        seen: set[tuple[Any, ...]] = set()
        for issue in issues:
            key = (
                issue.get("issue_type"),
                issue.get("sheet_name"),
                issue.get("line_number"),
                issue.get("column_name"),
                issue.get("field"),
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(issue)
        return deduped

    def _evaluer_feuille_fact(self, analyse: dict[str, Any], rows: list[list[Any]]) -> dict[str, Any]:
        sheet_name = str(analyse.get("feuille") or "")
        normalized_name = self._normaliser_nom_feuille(sheet_name)
        mapping_fields = {item["champ_standard"] for item in analyse.get("mapping", [])}
        header_line = int(analyse.get("ligne_entete") or 0)
        data_rows = rows[header_line:] if header_line else rows

        detailed_rows = 0
        percentage_rows = 0
        total_rows = 0
        for row in data_rows:
            text = " ".join(str(value) for value in row if value not in (None, "")).strip()
            if not text:
                continue
            lowered = text.lower()
            if "%" in text:
                percentage_rows += 1
            if lowered.startswith("total") or "sous-total" in lowered or "recap" in lowered or "récap" in lowered:
                total_rows += 1
            numeric_values = [nettoyer_nombre(value, None) for value in row]
            numeric_count = sum(1 for value in numeric_values if value is not None and value > 0)
            text_count = sum(1 for value in row if isinstance(value, str) and len(value.strip()) >= 4)
            if numeric_count >= 2 and text_count >= 1 and "%" not in text:
                detailed_rows += 1

        non_empty = sum(1 for row in data_rows if sum(1 for value in row if value not in (None, "")) >= 3)
        percentage_ratio = percentage_rows / max(non_empty, 1)
        total_ratio = total_rows / max(non_empty, 1)
        required_score = len(mapping_fields & {"designation", "quantite"}) / 2
        amount_score = 1 if mapping_fields & {"prix_total_ht", "prix_unitaire_ht"} else 0
        detail_score = min(detailed_rows / 50, 1)
        name_bonus = 1 if normalized_name == "METRE" else 0
        fact_score = (
            required_score * 0.30
            + amount_score * 0.20
            + detail_score * 0.30
            + float(analyse.get("score_dqe") or 0) * 0.10
            + name_bonus * 0.10
            - percentage_ratio * 0.35
            - total_ratio * 0.20
        )
        document_type = analyse.get("classification", {}).get("document_type")
        is_blacklisted = self._is_blacklisted_sheet(sheet_name)
        is_fact_candidate = (
            document_type in {"DQE", "METRE"}
            and not is_blacklisted
            and required_score >= 0.5
            and amount_score > 0
            and percentage_ratio < 0.35
        )
        return {
            "sheet_name": sheet_name,
            "normalized_name": normalized_name,
            "document_type": document_type,
            "score_dqe": analyse.get("score_dqe", 0),
            "fact_score": round(max(fact_score, 0), 3),
            "detailed_rows": detailed_rows,
            "non_empty_rows": non_empty,
            "percentage_ratio": round(percentage_ratio, 3),
            "total_ratio": round(total_ratio, 3),
            "is_blacklisted": is_blacklisted,
            "is_fact_candidate": is_fact_candidate,
            "reason": self._raison_selection_feuille(is_blacklisted, is_fact_candidate, normalized_name, document_type),
        }

    def _raison_selection_feuille(
        self,
        is_blacklisted: bool,
        is_fact_candidate: bool,
        normalized_name: str,
        document_type: str | None,
    ) -> str:
        if is_blacklisted:
            return "Feuille analytics/recap ignoree pour FACT_METRE."
        if normalized_name == "METRE" and document_type in {"DQE", "METRE"}:
            return "Feuille METRE prioritaire pour lignes detaillees."
        if is_fact_candidate:
            return "Feuille detaillee eligible FACT_METRE."
        return "Feuille non retenue pour FACT_METRE."

    def _valider_integrite_pipeline(
        self,
        rows_in: int,
        lignes: list[dict[str, Any]],
        classified_rows: list[dict[str, Any]],
        sheet_selection: dict[str, Any] | None,
        governance_summary: dict[str, Any] | None = None,
    ) -> None:
        if rows_in <= 0:
            return
        rows_out = len(lignes)
        governance_summary = governance_summary or summarize_classified_rows(classified_rows)
        expected_detail_rows = sum(
            int(evaluation.get("detailed_rows") or 0)
            for evaluation in (sheet_selection or {}).get("evaluations", [])
            if evaluation.get("sheet_name") in set((sheet_selection or {}).get("source_fact_metre", []))
        )
        reference_rows = expected_detail_rows or rows_in
        # Les DQE reels contiennent beaucoup de lignes de structure. Le garde-
        # fou bloque les pertes catastrophiques, mais accepte un gros fichier si
        # plus de 200 articles exploitables et un CAPEX positif ont ete trouves.
        capex_detecte = sum(nettoyer_nombre(ligne.get("prix_total_ht"), 0) or 0 for ligne in lignes)
        has_business_volume = rows_out >= 200 and capex_detecte > 0
        blocking_loss_rows = int(governance_summary.get("blocking_loss_rows") or 0)
        review_required_rows = int(governance_summary.get("review_required_rows") or 0)
        ignored_rows = int(governance_summary.get("ignored_rows") or 0)
        should_block_for_loss = (
            rows_out < reference_rows * 0.30
            and reference_rows >= 50
            and not has_business_volume
            and blocking_loss_rows > 0
        )
        if should_block_for_loss:
            top_rejets: dict[str, int] = {}
            for row in classified_rows:
                if row.get("governance_status") == "REJECTED":
                    row_type = str(row.get("row_type") or "inconnu")
                    top_rejets[row_type] = top_rejets.get(row_type, 0) + 1
            logger.error(
                "Perte massive critique detectee rows_in=%s reference_rows=%s rows_out=%s blocking_loss_rows=%s selection=%s top_rejets=%s governance=%s",
                rows_in,
                reference_rows,
                rows_out,
                blocking_loss_rows,
                (sheet_selection or {}).get("source_fact_metre"),
                top_rejets,
                governance_summary,
            )
            raise PipelineIntegrityError(
                "Perte massive de lignes detectee pendant le parsing DQE.",
                details={
                    "rows_in": rows_in,
                    "reference_rows": reference_rows,
                    "expected_detail_rows": expected_detail_rows,
                    "rows_out": rows_out,
                    "lost_rows": blocking_loss_rows,
                    "loss_ratio": governance_summary.get("strict_loss_ratio", 0),
                    "review_required_rows": review_required_rows,
                    "ignored_rows": ignored_rows,
                    "governance_summary": governance_summary,
                    "sheet_selection": sheet_selection or {},
                    "top_rejets": top_rejets,
                },
            )
        if rows_out < rows_in * 0.30 and rows_in >= 50:
            logger.warning(
                "DQE parsing bruyant mais accepte rows_in=%s reference_rows=%s rows_out=%s review_required=%s ignored=%s blocking_loss=%s capex_detecte=%s",
                rows_in,
                reference_rows,
                rows_out,
                review_required_rows,
                ignored_rows,
                blocking_loss_rows,
                capex_detecte,
            )

    def _calculer_trust_score_global(self, governance_summary: dict[str, Any]) -> int:
        total = int(governance_summary.get("total_rows") or 0)
        if not total:
            return 0
        blocking = int(governance_summary.get("blocking_loss_rows") or 0)
        review = int(governance_summary.get("review_required_rows") or 0)
        warning = int(governance_summary.get("warning_rows") or 0)
        penalty = (blocking * 40) + (review * 3) + (warning * 10)
        return max(0, min(100, round(100 - (penalty / total))))

    def _normaliser_nom_feuille(self, sheet_name: str) -> str:
        return normaliser_libelle(sheet_name).upper()

    def _is_blacklisted_sheet(self, sheet_name: str) -> bool:
        normalized_name = self._normaliser_nom_feuille(sheet_name)
        return any(token in normalized_name for token in self.BLACKLIST_ANALYTICS_SHEETS)

    def _mapper_colonnes(self, ligne_entete: list[Any]) -> list[dict[str, Any]]:
        mapping: list[dict[str, Any]] = []
        champs_deja_mappes: set[str] = set()

        for colonne_index, libelle in enumerate(ligne_entete):
            if libelle in (None, ""):
                continue

            libelle_normalise = normaliser_libelle(libelle)
            meilleur_champ = None
            meilleur_score = 0.0
            meilleur_mot = ""

            for regle in REGLES_MAPPING_EXCEL:
                for mot_cle in regle.mots_cles:
                    mot_normalise = normaliser_libelle(mot_cle)
                    score = self._score_libelle(libelle_normalise, mot_normalise)
                    if score > meilleur_score:
                        meilleur_champ = regle.champ_standard
                        meilleur_score = score
                        meilleur_mot = mot_cle

            if meilleur_champ and meilleur_score >= 0.62 and meilleur_champ not in champs_deja_mappes:
                champs_deja_mappes.add(meilleur_champ)
                mapping.append(
                    {
                        "colonne_excel": str(libelle),
                        "colonne_index": colonne_index,
                        "champ_standard": meilleur_champ,
                        "confiance": round(meilleur_score, 2),
                        "raison": f"Libelle rapproche de '{meilleur_mot}'.",
                    }
                )

        return mapping

    def _score_libelle(self, libelle: str, mot_cle: str) -> float:
        if libelle == mot_cle:
            return 1.0
        if libelle.startswith(mot_cle) or libelle.endswith(mot_cle):
            return 0.9
        if mot_cle in libelle:
            return 0.78
        morceaux = set(libelle.split("_"))
        if mot_cle in morceaux:
            return 0.74
        return 0.0

    def _scorer_feuille(self, champs_detectes: set[str], mapping: list[dict[str, Any]]) -> float:
        score_minimum = len(champs_detectes & CHAMPS_DQE_MINIMUM) / len(CHAMPS_DQE_MINIMUM)
        score_confort = len(champs_detectes & {"lot", "batiment", "niveau", "unite", "prix_unitaire_ht"}) / 5
        score_confiance = (
            sum(item["confiance"] for item in mapping) / len(mapping)
            if mapping
            else 0
        )
        return min((score_minimum * 0.6) + (score_confort * 0.25) + (score_confiance * 0.15), 1)

    def _avertissements_mapping(self, mapping: list[dict[str, Any]]) -> list[str]:
        champs_detectes = {item["champ_standard"] for item in mapping}
        manquants = sorted(CHAMPS_DQE_MINIMUM - champs_detectes)
        if not manquants:
            return []
        return [f"Champs minimum non detectes: {', '.join(manquants)}."]

    def _compter_lignes_donnees(self, lignes: list[list[Any]], ligne_entete: int) -> int:
        count = 0
        for ligne in lignes[ligne_entete:]:
            if sum(1 for valeur in ligne if valeur not in (None, "")) >= 3:
                count += 1
        return count

    def extraire_lignes_normalisees_depuis_analyse(
        self,
        lignes: list[list[Any]],
        analyse: dict[str, Any],
        lineage: DataLineageTracker | None = None,
    ) -> list[dict[str, Any]]:
        ligne_entete = analyse.get("ligne_entete")
        if not ligne_entete:
            return []

        colonnes = {
            item["champ_standard"]: item["colonne_index"]
            for item in analyse["mapping"]
        }
        lignes_normalisees: list[dict[str, Any]] = []
        rejets: dict[str, int] = {}
        current_lot = ""
        rows_in = max(len(lignes) - ligne_entete, 0)

        for ligne in lignes[ligne_entete:]:
            ligne_normale, motif_rejet, current_lot = self._normaliser_ligne_excel(
                ligne,
                colonnes,
                current_lot,
            )
            if ligne_normale:
                lignes_normalisees.append(ligne_normale)
            elif motif_rejet:
                rejets[motif_rejet] = rejets.get(motif_rejet, 0) + 1

        if lineage:
            lineage.track(
                "excel.extract_business_rows",
                rows_in=rows_in,
                rows_out=len(lignes_normalisees),
                feuille=analyse["feuille"],
                ligne_entete=ligne_entete,
                rejets=rejets,
            )

        return lignes_normalisees

    def _normaliser_ligne_excel(
        self,
        ligne: list[Any],
        colonnes: dict[str, int],
        current_lot: str,
    ) -> tuple[dict[str, Any] | None, str | None, str]:
        def valeur(champ: str, defaut: Any = "") -> Any:
            index = colonnes.get(champ)
            if index is None or index >= len(ligne):
                return defaut
            return ligne[index] if ligne[index] is not None else defaut

        lot_cellule = valeur("lot", "")
        designation_brute = str(valeur("designation", "")).strip()
        texte_ligne = " ".join(str(v) for v in ligne if v not in (None, ""))

        lot_detecte = self._detecter_lot_hierarchique(lot_cellule, designation_brute, texte_ligne)
        if lot_detecte:
            current_lot = lot_detecte

        designation = str(valeur("designation", "")).strip()
        if not designation:
            return None, "designation_vide", current_lot

        if self._est_ligne_structurelle(designation, texte_ligne):
            return None, "ligne_structurelle", current_lot

        prix_total = valeur("prix_total_ht", 0)
        quantite = valeur("quantite", 0)
        if not prix_total and not quantite:
            return None, "sans_quantite_ni_montant", current_lot

        lot_final = clean_lot(lot_cellule) or current_lot
        if not lot_final:
            return None, "sans_lot", current_lot

        return {
            "id_ligne": str(valeur("id_ligne", "")),
            "lot": lot_final,
            "batiment": str(valeur("batiment", "")),
            "niveau": clean_niveau(valeur("niveau", "")),
            "designation": designation,
            "unite": str(valeur("unite", "")),
            "quantite": quantite,
            "prix_unitaire_ht": valeur("prix_unitaire_ht", 0),
            "prix_total_ht": prix_total,
            "source": "excel_ai_mapping",
        }, None, current_lot

    def _detecter_lot_hierarchique(self, lot_cellule: Any, designation: str, texte_ligne: str) -> str:
        for candidat in (lot_cellule, designation, texte_ligne):
            lot = clean_lot(candidat)
            if lot.startswith("LOT "):
                return lot
        return ""

    def _est_ligne_structurelle(self, designation: str, texte_ligne: str) -> bool:
        texte = f"{designation} {texte_ligne}".strip().lower()
        return (
            texte.startswith("lot ")
            or "sous-total" in texte
            or texte.startswith("total")
            or " total :" in texte
        )

    def _simuler_preview(self, lignes_normalisees: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not lignes_normalisees:
            return None

        items: list[SimulationItem] = []
        for ligne in lignes_normalisees:
            quantite = nettoyer_nombre(ligne.get("quantite"), 0) or 0
            prix_total = nettoyer_nombre(ligne.get("prix_total_ht"), 0) or 0

            # Les lignes Excel de type PM, sous-total ou note technique restent
            # visibles dans l'analyse, mais ne doivent pas casser la simulation.
            if not ligne.get("designation") or quantite <= 0 or prix_total <= 0:
                continue

            items.append(
                SimulationItem(
                    designation=str(ligne.get("designation") or ""),
                    quantite=quantite,
                    prix_total_ht=prix_total,
                    prix_unitaire_ht=nettoyer_nombre(ligne.get("prix_unitaire_ht"), 0) or 0,
                    lot=str(ligne.get("lot") or ""),
                    batiment=str(ligne.get("batiment") or ""),
                    niveau=str(ligne.get("niveau") or ""),
                    unite=str(ligne.get("unite") or ""),
                )
            )

        if not items:
            return None
        return self.service_simulation.simuler(SimulationRequest(items=items))
