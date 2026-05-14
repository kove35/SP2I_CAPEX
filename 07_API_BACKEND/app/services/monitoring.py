from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models import FactMetre, MonitoringLog


logger = logging.getLogger("sp2i-capex-monitoring")


class MonitoringService:
    """Service centralise pour les logs et metriques de monitoring."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def log_event(self, type: str, message: str, niveau: str = "INFO") -> None:
        """
        Enregistre un evenement technique ou metier.

        Exemple : API disponible, erreur pipeline, base indisponible.
        """
        self._save_log(type=type, message=message, niveau=niveau, valeur=None)

    def log_metric(self, type: str, valeur: float, message: str | None = None) -> None:
        """
        Enregistre une metrique numerique.

        Exemple : temps de reponse API, nombre de lignes, score qualite.
        """
        niveau = "ERROR" if self._is_critical_metric(type, valeur) else "INFO"
        self._save_log(
            type=type,
            message=message or f"Metric {type} = {valeur}",
            niveau=niveau,
            valeur=float(valeur),
        )

    def check_database_health(self) -> dict[str, Any]:
        """Teste PostgreSQL avec SELECT 1 et mesure le temps de reponse."""
        start = time.perf_counter()
        try:
            value = self.db.execute(text("SELECT 1")).scalar_one()
            duration = round(time.perf_counter() - start, 4)
            status = "OK" if value == 1 else "ERROR"
            niveau = "ERROR" if duration > 1 else "INFO"

            self._save_log(
                type="database_health",
                message=f"Database health {status}",
                niveau=niveau,
                valeur=duration,
            )

            return {
                "status": status,
                "response_time": duration,
            }
        except Exception as erreur:
            self.db.rollback()
            logger.error("Database health check failed: %s", erreur)
            return {
                "status": "ERROR",
                "response_time": None,
                "error": str(erreur),
            }

    def check_data_quality(self) -> dict[str, Any]:
        """
        Calcule la qualite DQE stockee en base.

        Regles simples :
        - quantite <= 0 : invalide ;
        - prix_total_ht <= 0 : invalide ;
        - statut_ligne different de OK : anomalie.
        """
        try:
            total = self.db.execute(select(func.count(FactMetre.id_ligne))).scalar_one()
            invalid_quantite = self.db.execute(
                select(func.count(FactMetre.id_ligne)).where(FactMetre.quantite <= 0)
            ).scalar_one()
            invalid_price = self.db.execute(
                select(func.count(FactMetre.id_ligne)).where(FactMetre.prix_total_ht <= 0)
            ).scalar_one()
            statut_non_ok = self.db.execute(
                select(func.count(FactMetre.id_ligne)).where(FactMetre.statut_ligne != "OK")
            ).scalar_one()

            anomalies = int(invalid_quantite) + int(invalid_price) + int(statut_non_ok)
            score = round(((int(total) - anomalies) / int(total)) * 100, 2) if total else 0.0
            score = max(score, 0.0)
            niveau = "ERROR" if score < 70 else "WARNING" if anomalies else "INFO"

            self._save_log(
                type="data_quality_score",
                message=f"Score qualite DQE = {score}%",
                niveau=niveau,
                valeur=score,
            )
            self._save_log(
                type="data_quality_anomalies",
                message=f"Anomalies DQE = {anomalies}",
                niveau=niveau,
                valeur=float(anomalies),
            )

            return {
                "nb_lignes": int(total),
                "anomalies": anomalies,
                "invalid_quantite": int(invalid_quantite),
                "invalid_price": int(invalid_price),
                "statut_non_ok": int(statut_non_ok),
                "score_qualite": score,
            }
        except Exception as erreur:
            self.db.rollback()
            logger.error("Data quality check failed: %s", erreur)
            return {
                "nb_lignes": 0,
                "anomalies": 0,
                "score_qualite": 0.0,
                "error": str(erreur),
            }

    def get_status(self) -> dict[str, Any]:
        """Retourne un statut global pret pour un dashboard ou une API."""
        database = self.check_database_health()
        quality = self.check_data_quality()

        return {
            "api": "OK",
            "database": database["status"],
            "response_time": database.get("response_time"),
            "nb_lignes": quality.get("nb_lignes", 0),
            "anomalies": quality.get("anomalies", 0),
            "score_qualite": quality.get("score_qualite", 0.0),
            "niveau": self._global_level(database, quality),
        }

    def _save_log(
        self,
        type: str,
        message: str,
        niveau: str = "INFO",
        valeur: float | None = None,
    ) -> None:
        """
        Sauvegarde un log sans casser le flux appelant.

        En monitoring, il vaut mieux perdre un log que bloquer une requete API.
        """
        try:
            log = MonitoringLog(
                type=type,
                message=message,
                niveau=niveau,
                valeur=valeur,
            )
            self.db.add(log)
            self.db.commit()
        except Exception as erreur:
            self.db.rollback()
            logger.error("Monitoring log not saved: %s", erreur)

    def _is_critical_metric(self, type: str, valeur: float) -> bool:
        """Regles d'alerte simples pour passer une metrique en ERROR."""
        if type == "api_response_time" and valeur > 1:
            return True
        if type == "data_quality_score" and valeur < 70:
            return True
        return False

    def _global_level(self, database: dict[str, Any], quality: dict[str, Any]) -> str:
        """Determine le niveau global du systeme."""
        if database.get("status") != "OK":
            return "ERROR"
        if float(quality.get("score_qualite") or 0) < 70:
            return "ERROR"
        if int(quality.get("anomalies") or 0) > 0:
            return "WARNING"
        return "INFO"
