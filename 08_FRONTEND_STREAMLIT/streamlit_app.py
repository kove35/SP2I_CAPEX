from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="SP2I BUILD",
    page_icon="SP2I",
    layout="wide",
)


def get_setting(name: str, default: str = "") -> str:
    """Lit d'abord Streamlit secrets, puis les variables d'environnement."""
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return str(value or os.getenv(name, default))


API_URL = get_setting("API_URL", "http://localhost:8000").rstrip("/")


def api_get(path: str) -> dict[str, Any]:
    response = requests.get(f"{API_URL}{path}", timeout=30)
    response.raise_for_status()
    return response.json()


def api_post_file(path: str, uploaded_file) -> dict[str, Any]:
    files = {
        "fichier": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "application/octet-stream",
        )
    }
    response = requests.post(f"{API_URL}{path}", files=files, timeout=180)
    response.raise_for_status()
    return response.json()


def render_powerbi(embed_url: str) -> None:
    if not embed_url:
        st.info("Renseigne l'URL Power BI dans les secrets Streamlit pour activer ce dashboard.")
        return
    components.iframe(embed_url, height=720, scrolling=True)


def render_kpis(summary: dict[str, Any]) -> None:
    columns = st.columns(5)
    kpis = [
        ("CAPEX local", summary.get("capex_local_total", 0)),
        ("CAPEX optimise", summary.get("capex_optimise_total", 0)),
        ("Economie", summary.get("economie_totale", 0)),
        ("Taux economie", f"{summary.get('taux_economie_global', 0)} %"),
        ("Lignes", summary.get("nb_lignes", 0)),
    ]
    for column, (label, value) in zip(columns, kpis):
        column.metric(label, value)


def render_upload_flow() -> None:
    st.subheader("Importer et controler un fichier DQE")
    uploaded_file = st.file_uploader(
        "Formats acceptes : XLSX, XLSM, XLS, CSV, PDF",
        type=["xlsx", "xlsm", "xls", "csv", "pdf"],
    )

    if not uploaded_file:
        st.caption("Le fichier est envoye au backend FastAPI. Streamlit ne calcule pas les KPI metier.")
        return

    col_preview, col_sync = st.columns([1, 1])
    extension = uploaded_file.name.lower().rsplit(".", 1)[-1]

    with col_preview:
        if st.button("Analyser sans ecrire en base", use_container_width=True):
            try:
                endpoint = "/dqe/extract" if extension == "pdf" else "/api/upload/excel"
                result = api_post_file(endpoint, uploaded_file)
                st.session_state["last_preview"] = result
                st.success("Analyse terminee.")
            except requests.HTTPError as error:
                st.error(f"Erreur API : {error.response.text}")
            except Exception as error:
                st.error(f"Erreur upload : {error}")

    with col_sync:
        disabled = extension == "pdf"
        if st.button("Synchroniser PostgreSQL", disabled=disabled, use_container_width=True):
            try:
                result = api_post_file("/api/upload/excel/sync", uploaded_file)
                st.session_state["last_sync"] = result
                st.success("PostgreSQL synchronise.")
            except requests.HTTPError as error:
                st.error(f"Erreur API : {error.response.text}")
            except Exception as error:
                st.error(f"Erreur synchronisation : {error}")

    preview = st.session_state.get("last_preview")
    if preview:
        st.markdown("### Preview intelligente")
        ai_preview = preview.get("ai_preview") or {}
        cols = st.columns(4)
        cols[0].metric("Lots detectes", ai_preview.get("lots_detected", "-"))
        cols[1].metric("Score qualite", ai_preview.get("quality_score", "-"))
        cols[2].metric("Colonnes reconnues", ai_preview.get("recognized_columns", "-"))
        cols[3].metric("Lignes invalides", ai_preview.get("invalid_rows", "-"))

        lignes = preview.get("lignes_normalisees_preview") or []
        if lignes:
            st.dataframe(pd.DataFrame(lignes), use_container_width=True, height=280)

        anomalies = preview.get("ai_anomalies") or []
        if anomalies:
            st.warning("Anomalies detectees par le moteur IA.")
            st.dataframe(pd.DataFrame(anomalies), use_container_width=True, height=240)

    if st.session_state.get("last_sync"):
        st.markdown("### Derniere synchronisation")
        st.json(st.session_state["last_sync"])


def main() -> None:
    st.title("SP2I BUILD")
    st.caption("Cockpit cloud de test : FastAPI Render, PostgreSQL Render, Power BI Service.")

    with st.sidebar:
        st.header("SP2I")
        st.caption(f"API : {API_URL}")
        page = st.radio(
            "Navigation",
            ["Cockpit", "DQE intelligent", "PostgreSQL/API", "Power BI"],
        )

        try:
            health = api_get("/health")
            st.success(f"Backend {health.get('statut', 'OK')}")
        except Exception:
            st.error("Backend indisponible")

    if page == "Cockpit":
        st.subheader("KPI CAPEX")
        try:
            render_kpis(api_get("/capex/summary"))
        except Exception as error:
            st.warning(f"KPI indisponibles : {error}")

        st.markdown("### Workflow cloud")
        st.write("Upload fichier -> IA DQE -> normalisation -> PostgreSQL -> API -> Power BI.")

    elif page == "DQE intelligent":
        render_upload_flow()

    elif page == "PostgreSQL/API":
        st.subheader("Diagnostic configuration")
        try:
            st.json(api_get("/debug/config"))
        except Exception as error:
            st.error(f"Diagnostic indisponible : {error}")

        st.subheader("Dernieres lignes fact_metre")
        try:
            data = api_get("/fact_metre?limit=50")
            rows = data.get("data") or data.get("lignes") or data
            st.dataframe(pd.DataFrame(rows), use_container_width=True, height=420)
        except Exception as error:
            st.warning(f"Lecture fact_metre indisponible : {error}")

    elif page == "Power BI":
        dashboard = st.selectbox(
            "Dashboard",
            ["Direction", "Finance", "Import", "Chantier", "DQE"],
        )
        key = f"POWERBI_{dashboard.upper()}_URL"
        render_powerbi(get_setting(key))


if __name__ == "__main__":
    main()
