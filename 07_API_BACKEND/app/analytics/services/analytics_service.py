from __future__ import annotations

import hashlib
import json
from pathlib import Path
from time import perf_counter
from typing import Any

from sqlalchemy.orm import Session

from app.analytics.cache import analytics_cache
from app.analytics.repositories import AnalyticsRepository
from app.analytics.schemas import AnalyticsQuery
from app.analytics.utils.display_text import normalize_payload_labels


RACINE = Path(__file__).resolve().parents[4]


class AnalyticsService:
    """Service applicatif du moteur BI proprietaire SP2I."""

    def __init__(self, db: Session) -> None:
        self.repository = AnalyticsRepository(db)

    def dashboard(self, query: AnalyticsQuery, dashboard_type: str = "direction") -> dict[str, Any]:
        return self._cached(f"dashboard:{dashboard_type}", query, lambda: self._build_dashboard(query, dashboard_type))

    def capex(self, query: AnalyticsQuery) -> dict[str, Any]:
        return self._cached("capex", query, lambda: self._build_dashboard(query, "capex"))

    def kpis(self, query: AnalyticsQuery) -> dict[str, Any]:
        return self._cached("kpis", query, lambda: self._response(query, kpis=self.repository.kpis(query)))

    def risk(self, query: AnalyticsQuery) -> dict[str, Any]:
        return self._cached("risk", query, lambda: self._response(query, charts={"risk_matrix": self.repository.risk_matrix(query)}))

    def procurement(self, query: AnalyticsQuery) -> dict[str, Any]:
        return self._cached("procurement", query, lambda: self._build_dashboard(query, "procurement"))

    def logistics(self, query: AnalyticsQuery) -> dict[str, Any]:
        return self._cached("logistics", query, lambda: self._build_dashboard(query, "logistics"))

    def scenarios(self, query: AnalyticsQuery) -> dict[str, Any]:
        return self._response(query, table=self.repository.scenarios())

    def heatmap(self, query: AnalyticsQuery) -> dict[str, Any]:
        return self._response(query, charts={"heatmap": self.repository.heatmap(query)})

    def drilldown(self, query: AnalyticsQuery) -> dict[str, Any]:
        path = self.repository.drilldown_path(query.drilldown_level)
        grouped = self.repository.grouped(query, default_group=path["next"] or path["current"])
        return self._response(query, charts={"drilldown": grouped}, metadata={"drilldown": path})

    def timeline(self, query: AnalyticsQuery) -> dict[str, Any]:
        return self._response(query, charts={"timeline": self.repository.timeline(query)})

    def filter_options(self) -> dict[str, Any]:
        options = self.repository.filter_options()
        return normalize_payload_labels({
            "batiments": options.get("batiments", []),
            "niveaux": options.get("niveaux", []),
            "lots": options.get("lots", []),
            "familles": options.get("familles", []),
            "import_local": options.get("import_local", []),
        })

    def system_health(self) -> dict[str, Any]:
        return {
            "status": "SUCCESS",
            "filters": {},
            "pagination": {},
            "kpis": {},
            "charts": {},
            "table": [],
            "metadata": {
                "engine": "SP2I Analytics Engine V1",
                "database": "configured",
                "cache": analytics_cache.status(),
            },
        }

    def cache_status(self) -> dict[str, Any]:
        return {
            "status": "SUCCESS",
            "filters": {},
            "pagination": {},
            "kpis": {},
            "charts": {},
            "table": [],
            "metadata": analytics_cache.status(),
        }

    def debug_pipeline(self) -> dict[str, Any]:
        debug = self.repository.pipeline_debug()
        latest_source = self._latest_pipeline_source()
        return {
            "status": "SUCCESS",
            "filters": {},
            "pagination": {"page": 1, "page_size": len(debug["preview"]), "total": debug["fact_metre_count"]},
            "kpis": {
                "capex_brut": round(float(debug["sums"].get("capex_local_total") or 0), 2),
                "capex_optimise": round(float(debug["sums"].get("capex_optimise_total") or 0), 2),
                "economie_nette": round(float(debug["sums"].get("economie_total") or 0), 2),
                "nb_lignes": debug["fact_metre_count"],
            },
            "charts": {},
            "table": debug["preview"],
            "metadata": {
                "engine": "SP2I Analytics Engine V1",
                "debug": {
                    "columns": debug["columns"],
                    "sums": debug["sums"],
                    "views": debug["views"],
                    "latest_source": latest_source,
                    "cache": analytics_cache.status(),
                },
            },
            "warnings": debug["warnings"],
        }

    def qa_summary(self) -> dict[str, Any]:
        """Synthese QA lisible pour valider rapidement le moteur analytics."""
        query = AnalyticsQuery()
        kpis = self.repository.kpis(query)
        table, total = self.repository.table(query)
        heatmap = self.repository.heatmap(query)
        timeline = self.repository.timeline(query)
        grouped = self.repository.grouped(query, default_group="lot")
        cache_status = analytics_cache.status()

        capex_brut = float(kpis.get("capex_brut") or 0)
        economie = float(kpis.get("economie_nette") or 0)
        nb_lignes = int(kpis.get("nb_lignes") or 0)
        lots = {str(row.get("label")) for row in grouped if row.get("label")}
        checks = {
            "postgresql_connected": True,
            "fact_metre_non_empty": nb_lignes > 0,
            "nb_lignes_gt_500": nb_lignes > 500,
            "capex_brut_gt_0": capex_brut > 0,
            "economie_gt_0": economie > 0,
            "lots_gt_0": len(lots) > 0,
            "charts_ready": bool(grouped and heatmap),
            "ag_grid_ready": bool(table),
            "timeline_ready": bool(timeline),
            "cache_ready": cache_status.get("backend") == "in-memory",
        }
        warnings = [
            f"Check KO: {name}"
            for name, ok in checks.items()
            if not ok
        ]

        return {
            "status": "SUCCESS",
            "filters": {},
            "pagination": {"page": 1, "page_size": len(table), "total": total},
            "kpis": kpis,
            "charts": {
                "bar": grouped,
                "heatmap": heatmap,
                "timeline": timeline,
            },
            "table": table,
            "metadata": {
                "engine": "SP2I Analytics Engine V1",
                "qa_status": "PASS" if not warnings else "WARN",
                "checks": checks,
                "cache": cache_status,
                "dataset_target": {
                    "name": "SP2I_CAPEX_DEMO_V1",
                    "expected_rows": 584,
                    "expected_capex": 1129667152,
                },
            },
            "warnings": warnings,
        }

    def data_quality(self) -> dict[str, Any]:
        """Controle qualite bout-en-bout Excel -> FACT_METRE -> cockpit."""
        query = AnalyticsQuery()
        debug = self.repository.pipeline_debug()
        metrics = self.repository.quality_metrics()
        source = self._latest_pipeline_source()
        history = self.repository.import_audit_history()
        source_rows = int(source.get("rows_in_source_json") or 0)
        source_capex = float(source.get("capex_source") or 0)
        fact_rows = int(metrics.get("nb_lignes") or debug.get("fact_metre_count") or 0)
        analytics_capex = float(metrics.get("capex_local_total") or 0)
        capex_delta = analytics_capex - source_capex
        capex_delta_pct = abs(capex_delta) / source_capex if source_capex else 0
        line_delta = fact_rows - source_rows
        line_delta_pct = abs(line_delta) / source_rows if source_rows else 0
        family_pending = int(metrics.get("lignes_famille_a_classer") or 0)
        invalid_rows = (
            int(metrics.get("lignes_quantite_invalide") or 0)
            + int(metrics.get("lignes_capex_invalide") or 0)
            + int(metrics.get("lignes_sans_lot") or 0)
            + int(metrics.get("lignes_sans_designation") or 0)
        )
        anomalies = list(source.get("ai_anomalies") or [])
        warnings: list[str] = []
        if not source.get("available"):
            warnings.append("Aucun fichier source pipeline disponible.")
        if capex_delta_pct > 0.005:
            warnings.append("Ecart financier superieur a la tolerance de 0,5 %.")
        if source_rows and fact_rows != source_rows:
            warnings.append("Le nombre de lignes source et FACT_METRE differe.")
        if family_pending:
            warnings.append(f"{family_pending} lignes restent sans classification metier robuste.")
        if invalid_rows:
            warnings.append(f"{invalid_rows} controles ligne sont en anomalie dans FACT_METRE.")

        score = 100.0
        score -= min(35, capex_delta_pct * 1000)
        score -= min(20, line_delta_pct * 100)
        score -= min(20, (family_pending / max(fact_rows, 1)) * 100)
        score -= min(15, (invalid_rows / max(fact_rows, 1)) * 100)
        score -= min(10, len(anomalies) * 1.5)
        score = round(max(0, score), 1)

        checks = {
            "excel_source_available": bool(source.get("available")),
            "financial_reconciliation_ok": capex_delta_pct <= 0.005,
            "pipeline_rows_ok": bool(source_rows and fact_rows == source_rows),
            "fact_metre_non_empty": fact_rows > 0,
            "taxonomy_ok": family_pending == 0,
            "line_quality_ok": invalid_rows == 0,
        }

        return normalize_payload_labels({
            "status": "SUCCESS",
            "filters": {},
            "pagination": {"page": 1, "page_size": len(anomalies), "total": len(anomalies)},
            "kpis": {
                "score_qualite": score,
                "capex_source": round(source_capex, 2),
                "capex_analytics": round(analytics_capex, 2),
                "ecart_capex": round(capex_delta, 2),
                "ecart_capex_pct": round(capex_delta_pct, 6),
                "lignes_excel": source_rows,
                "lignes_fact_metre": fact_rows,
                "lignes_rejetees": max(source_rows - fact_rows, 0),
                "lignes_famille_a_classer": family_pending,
                "anomalies": len(anomalies) + invalid_rows,
            },
            "charts": {
                "pipeline": [
                    {"label": "Excel source", "value": source_rows},
                    {"label": "Parsing IA", "value": source_rows},
                    {"label": "FACT_METRE", "value": fact_rows},
                    {"label": "Cockpit", "value": fact_rows},
                ],
                "checks": checks,
            },
            "table": anomalies[:100],
            "metadata": {
                "engine": "SP2I Data Quality Center",
                "qa_status": "PASS" if not warnings else "WARN",
                "tolerance_capex_pct": 0.005,
                "source": source,
                "metrics": metrics,
                "history": history,
            },
            "warnings": warnings,
        })

    def query_performance(self) -> dict[str, Any]:
        start = perf_counter()
        query = AnalyticsQuery()
        self.repository.kpis(query)
        elapsed_ms = round((perf_counter() - start) * 1000, 2)
        return {
            "status": "SUCCESS",
            "filters": {},
            "pagination": {},
            "kpis": {},
            "charts": {},
            "table": [],
            "metadata": {"last_probe_ms": elapsed_ms, "target_ms": 500},
        }

    def _latest_pipeline_source(self) -> dict[str, Any]:
        chemin_source = RACINE / "03_DONNEES_ENTREE/dqe/dqe_source_brut.json"
        if not chemin_source.exists():
            return {"available": False, "reason": "Aucun fichier source courant trouve."}
        try:
            payload = json.loads(chemin_source.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            return {"available": False, "reason": f"Lecture source impossible: {exc}"}

        audit_excel = payload.get("audit_excel", {}) if isinstance(payload, dict) else {}
        sheet_selection = audit_excel.get("sheet_selection", {})
        ai_preview = audit_excel.get("ai_preview", {})
        lignes = payload.get("lignes", []) if isinstance(payload, dict) else []
        capex_source = 0.0
        for ligne in lignes:
            if not isinstance(ligne, dict):
                continue
            montant = (
                ligne.get("prix_total_ht")
                or ligne.get("montant_total")
                or ligne.get("montant_ht")
                or ligne.get("total_ht")
                or ligne.get("CAPEX_LOCAL")
                or ligne.get("CAPEX_LOCAL_MONTANT")
            )
            try:
                capex_source += float(str(montant or 0).replace(" ", "").replace(",", "."))
            except ValueError:
                quantite = ligne.get("quantite") or 0
                pu = ligne.get("prix_unitaire_ht") or ligne.get("PU_LOCAL") or 0
                try:
                    capex_source += float(quantite or 0) * float(pu or 0)
                except (TypeError, ValueError):
                    pass
        return {
            "available": True,
            "source": payload.get("source") if isinstance(payload, dict) else None,
            "rows_in_source_json": len(lignes),
            "capex_source": round(capex_source, 2),
            "source_fact_metre": sheet_selection.get("source_fact_metre", []),
            "selection_reason": sheet_selection.get("reason"),
            "sheet_evaluations": sheet_selection.get("evaluations", []),
            "ignored_sheets": sheet_selection.get("ignored_sheets", []),
            "blacklist_active": sheet_selection.get("blacklist_active", []),
            "ai_preview": ai_preview,
            "ai_anomalies": audit_excel.get("ai_anomalies", []),
        }

    def _build_dashboard(self, query: AnalyticsQuery, dashboard_type: str) -> dict[str, Any]:
        table, total = self.repository.table(query)
        group_default = {
            "direction": "lot",
            "capex": "lot",
            "procurement": "famille",
            "logistics": "decision_import",
            "chantier": "batiment",
        }.get(dashboard_type, "lot")
        return self._response(
            query,
            kpis=self.repository.kpis(query),
            charts={
                "bar": self.repository.grouped(query, default_group=group_default),
                "heatmap": self.repository.heatmap(query),
                "timeline": self.repository.timeline(query),
                "sankey": self.repository.sankey(query),
            },
            table=table,
            total=total,
            metadata={"dashboard": dashboard_type, "engine": "SP2I Analytics Engine V1"},
        )

    def _response(
        self,
        query: AnalyticsQuery,
        kpis: dict[str, Any] | None = None,
        charts: dict[str, Any] | None = None,
        table: list[dict[str, Any]] | None = None,
        total: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return normalize_payload_labels({
            "status": "SUCCESS",
            "filters": query.filters.model_dump(exclude_none=True),
            "pagination": {
                "page": query.page,
                "page_size": query.page_size,
                "total": total if total is not None else len(table or []),
            },
            "kpis": kpis or {},
            "charts": charts or {},
            "table": table or [],
            "metadata": metadata or {"engine": "SP2I Analytics Engine V1"},
        })

    def _cached(self, prefix: str, query: AnalyticsQuery, builder) -> dict[str, Any]:
        key = f"{prefix}:{hashlib.sha1(query.model_dump_json().encode()).hexdigest()}"
        cached = analytics_cache.get(key)
        if cached:
            cached["metadata"] = {**cached.get("metadata", {}), "cache_hit": True}
            return cached
        value = builder()
        value["metadata"] = {**value.get("metadata", {}), "cache_hit": False}
        analytics_cache.set(key, json.loads(json.dumps(value, default=str)))
        return value
