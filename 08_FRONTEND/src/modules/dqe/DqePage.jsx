import React from "react";
import { useQuery } from "@tanstack/react-query";
import AnalyticsCard from "../../ui/AnalyticsCard";
import KpiCard from "../../ui/KpiCard";
import { analyzeExcel, syncExcel, validateAiMapping } from "../../services/excelUploadService";
import { getAnalyticsDataQuality } from "../../services/analyticsService";

const SUPPORTED_UPLOAD_EXTENSIONS = [".xlsx", ".xlsm", ".xls", ".csv"];

function hasSupportedExtension(fileName) {
  const lowerName = fileName.toLowerCase();
  return SUPPORTED_UPLOAD_EXTENSIONS.some((extension) => lowerName.endsWith(extension));
}

function isSuccessResponse(data) {
  return data?.status === "SUCCESS";
}

export default function DqePage() {
  const [tab, setTab] = React.useState(new URLSearchParams(window.location.search).get("tab") || "import");
  const [file, setFile] = React.useState(null);
  const [analysis, setAnalysis] = React.useState(null);
  const [syncResult, setSyncResult] = React.useState(null);
  const [validationResult, setValidationResult] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const dataQuality = useQuery({
    queryKey: ["analytics-data-quality", syncResult?.db_sync?.fact_metre_sql_count || 0],
    queryFn: getAnalyticsDataQuality,
    enabled: ["quality", "history", "sync"].includes(tab),
    staleTime: 30_000,
  });

  React.useEffect(() => {
    setTab(new URLSearchParams(window.location.search).get("tab") || "import");
  }, [window.location.search]);

  const recommendedSheet = analysis?.feuille_recommandee || "-";
  const bestAnalysis = analysis?.analyses?.[0] || {};
  const previewRows = Array.isArray(analysis?.lignes_normalisees_preview)
    ? analysis.lignes_normalisees_preview
    : [];
  const aiPreview = analysis?.ai_preview || {};
  const aiConfidence = analysis?.ai_confidence || {};
  const aiAnomalies = Array.isArray(analysis?.ai_anomalies) ? analysis.ai_anomalies : [];
  const aiSuggestions = analysis?.ai_suggestions || {};
  const lineCount = bestAnalysis.lignes_detectees || previewRows.length || 0;
  const qualityScore = Math.round(Number(aiPreview.quality_score ?? bestAnalysis.score_dqe ?? 0) * 100);
  const recognizedColumns = aiPreview.recognized_columns ?? "-";
  const lotsDetected = aiPreview.lots_detected ?? "-";
  const estimatedBudget = Number(aiPreview.estimated_capex_detected || 0);
  const warningCount = bestAnalysis.avertissements?.length || 0;
  const qualityPayload = dataQuality.data || {};
  const qualityKpis = qualityPayload.kpis || {};
  const qualityMeta = qualityPayload.metadata || {};
  const importHistory = qualityMeta.history || [];
  const pipelineSteps = qualityPayload.charts?.pipeline || [];
  const qualityWarnings = qualityPayload.warnings || [];
  const qualityAnomalies = Array.isArray(qualityPayload.table) ? qualityPayload.table : [];
  const qualityCenterScore = Math.round(Number(qualityKpis.score_qualite ?? qualityScore ?? 0));
  const capexSource = Number(qualityKpis.capex_source || 0);
  const capexAnalytics = Number(qualityKpis.capex_analytics || 0);
  const capexGapPct = Number(qualityKpis.ecart_capex_pct || 0) * 100;

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];
    setError("");
    setSyncResult(null);
    setValidationResult(null);

    if (!selectedFile) {
      setFile(null);
      return;
    }

    if (!hasSupportedExtension(selectedFile.name)) {
      setFile(null);
      setAnalysis(null);
      setError("Le fichier doit etre au format .xlsx, .xlsm, .xls ou .csv.");
      return;
    }

    setFile(selectedFile);
  };

  const runAnalysis = async () => {
    if (!file) {
      setError("Selectionne d'abord un fichier Excel.");
      return;
    }

    setLoading(true);
    setError("");
    setSyncResult(null);
    try {
      const result = await analyzeExcel(file);
      console.log("API RESPONSE DQE ANALYZE", result);
      if (!isSuccessResponse(result)) {
        setAnalysis(null);
        setError(result?.message || result?.detail || "Erreur analyse DQE.");
        return;
      }
      setAnalysis(result);
      setError(null);
    } catch (apiError) {
      setError(`Analyse DQE indisponible : ${apiError.message}`);
    } finally {
      setLoading(false);
    }
  };

  const runValidateMapping = async () => {
    if (!analysis?.file_id) {
      setError("Analyse d'abord un fichier Excel avant validation humaine.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const result = await validateAiMapping(analysis.file_id, bestAnalysis.mapping || []);
      setValidationResult(result);
    } catch (apiError) {
      setError(`Validation de la correspondance indisponible : ${apiError.message}`);
    } finally {
      setLoading(false);
    }
  };

  const runSync = async () => {
    if (!file) {
      setError("Selectionne d'abord un fichier Excel.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const result = await syncExcel(file);
      console.log("API RESPONSE DQE SYNC", result);
      if (result?.status && result.status !== "SUCCESS" && result.status !== "OK") {
        setError(result?.message || result?.detail || "Erreur synchronisation PostgreSQL.");
        return;
      }
      setSyncResult(result);
      setError(null);
    } catch (apiError) {
      setError(`Synchronisation PostgreSQL indisponible : ${apiError.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="cockpit-page cockpit-page-fit">
      <section className="page-hero compact">
        <p className="eyebrow">DQE & donnees projet</p>
        <h1>Importer, verifier et fiabiliser le budget du projet</h1>
      </section>
      <div className="tab-row">
        <button className={tab === "import" ? "active" : ""} onClick={() => setTab("import")} type="button">Importer le DQE</button>
        <button className={tab === "analysis" ? "active" : ""} onClick={() => setTab("analysis")} type="button">Analyse DQE</button>
        <button className={tab === "mapping" ? "active" : ""} onClick={() => setTab("mapping")} type="button">Correspondance</button>
        <button className={tab === "sync" ? "active" : ""} onClick={() => setTab("sync")} type="button">Envoyer en base</button>
        <button className={tab === "quality" ? "active" : ""} onClick={() => setTab("quality")} type="button">Qualite donnees</button>
        <button className={tab === "history" ? "active" : ""} onClick={() => setTab("history")} type="button">Historique imports</button>
      </div>
      {error ? <div className="app-error">{error}</div> : null}
      <section className="metric-grid">
        <KpiCard label="Fichier" value={file ? "Excel" : "Aucun"} />
        <KpiCard label="Feuille recommandee" value={recommendedSheet} />
        <KpiCard label="Score DQE" value={`${qualityScore}%`} tone={qualityScore >= 80 ? "success" : "warning"} />
        <KpiCard label="Lots detectes" value={lotsDetected} />
      </section>
      <section className="cockpit-split">
        <AnalyticsCard title={tab === "mapping" ? "Correspondance des colonnes" : tab === "quality" ? "Centre de controle qualite" : tab === "sync" ? "Envoi controle en base projet" : tab === "history" ? "Historique des imports DQE" : "Apercu du DQE importe"} eyebrow="Import assiste">
          {tab === "import" ? (
            <div className="excel-upload-zone">
              <label>
                Fichier DQE/BPU
                <input type="file" accept=".xlsx,.xlsm,.xls,.csv" onChange={handleFileChange} />
              </label>
              <div className="excel-actions">
                <button className="primary-action" type="button" onClick={runAnalysis} disabled={!file || loading}>
                  {loading ? "Analyse..." : "Analyser Excel"}
                </button>
                <button className="primary-action secondary-action" type="button" onClick={runValidateMapping} disabled={!analysis?.file_id || loading}>
                  Valider la correspondance
                </button>
                <button className="primary-action secondary-action" type="button" onClick={runSync} disabled={!file || loading}>
                  Envoyer en base projet
                </button>
              </div>
              {file ? <p>Fichier selectionne : <strong>{file.name}</strong></p> : <p>Formats acceptes : .xlsx, .xlsm, .xls et .csv.</p>}
            </div>
          ) : null}

          {tab === "analysis" || tab === "import" ? (
            <>
              <div className="ai-preview-grid">
                <span>Colonnes reconnues <strong>{recognizedColumns}</strong></span>
                <span>Colonnes ambigues <strong>{aiPreview.ambiguous_columns ?? "-"}</strong></span>
                <span>Anomalies <strong>{aiPreview.invalid_rows ?? aiAnomalies.length}</strong></span>
                <span>Budget detecte <strong>{estimatedBudget.toLocaleString("fr-FR")}</strong></span>
              </div>
              <div className="data-table-wrap panel-scroll">
                <table className="data-table">
                  <thead><tr><th>Designation</th><th>Lot</th><th>Famille IA</th><th>Quantite</th><th>PU local</th></tr></thead>
                  <tbody>
                    {previewRows.map((row, index) => (
                      <tr key={row.id_ligne || `${row.designation}-${index}`}>
                        <td>{row.designation || "-"}</td>
                        <td>{row.lot || "-"}</td>
                        <td>{row.famille_ai || row.famille || "-"}</td>
                        <td>{row.quantite || 0}</td>
                        <td>{row.prix_unitaire_ht || row.pu_local || 0}</td>
                      </tr>
                    ))}
                    {!previewRows.length ? <tr><td colSpan="5">Analyse un fichier Excel pour afficher l'apercu nettoye.</td></tr> : null}
                  </tbody>
                </table>
              </div>
            </>
          ) : null}

          {tab === "mapping" ? (
            <div className="data-table-wrap panel-scroll">
              <table className="data-table">
                <thead><tr><th>Colonne Excel</th><th>Champ SP2I</th><th>Confiance</th><th>Raison</th></tr></thead>
                <tbody>
                  {(bestAnalysis.mapping || []).map((mapping) => (
                    <tr key={`${mapping.colonne_excel}-${mapping.champ_standard}`}>
                      <td>{mapping.colonne_excel}</td>
                      <td>{mapping.champ_standard}</td>
                      <td>{Math.round(Number(mapping.confiance || 0) * 100)}%</td>
                      <td>{mapping.raison}</td>
                    </tr>
                  ))}
                  {!bestAnalysis.mapping?.length ? <tr><td colSpan="4">Aucune correspondance disponible avant analyse Excel.</td></tr> : null}
                </tbody>
              </table>
            </div>
          ) : null}

          {tab === "sync" ? (
            <div className="excel-upload-zone">
              <p>Cette action remplace les donnees analytiques courantes uniquement si le fichier produit un FACT_METRE exploitable.</p>
              <label>
                Fichier DQE/BPU a envoyer
                <input type="file" accept=".xlsx,.xlsm,.xls,.csv" onChange={handleFileChange} />
              </label>
              <div className="excel-actions">
                <button className="primary-action secondary-action" type="button" onClick={runAnalysis} disabled={!file || loading}>
                  Controler avant envoi
                </button>
                <button className="primary-action" type="button" onClick={runSync} disabled={!file || loading}>
                  {loading ? "Envoi..." : "Envoyer en base projet"}
                </button>
              </div>
              <ul className="signal-list">
                <li>Protection active : sync vide ou sans CAPEX positif bloquee.</li>
                <li>Audit cree automatiquement apres synchronisation.</li>
                <li>Dernier statut : {syncResult?.db_sync?.status || syncResult?.status || "non lance"}.</li>
              </ul>
            </div>
          ) : null}

          {tab === "quality" ? (
            <div className="quality-center">
              <div className="ai-preview-grid">
                <span>Qualite donnees <strong>{qualityCenterScore}%</strong></span>
                <span>CAPEX fichier <strong>{capexSource.toLocaleString("fr-FR")}</strong></span>
                <span>CAPEX cockpit <strong>{capexAnalytics.toLocaleString("fr-FR")}</strong></span>
                <span>Ecart financier <strong>{capexGapPct.toFixed(3)}%</strong></span>
              </div>
              <ul className="signal-list">
                <li>Controle financier : tolerance maximale 0,5 % entre le fichier source et FACT_METRE.</li>
                <li>Lignes fichier : {qualityKpis.lignes_excel ?? lineCount} | lignes en base : {qualityKpis.lignes_fact_metre ?? "-"}.</li>
                <li>Classification metier a completer : {qualityKpis.lignes_famille_a_classer ?? "-"} ligne(s).</li>
                <li>Source retenue : {(qualityMeta.source?.source_fact_metre || [recommendedSheet]).join(", ") || "-"}.</li>
                <li>Statut QA : {qualityMeta.qa_status || (qualityWarnings.length ? "WARN" : "PASS")}.</li>
              </ul>
              <div className="data-table-wrap panel-scroll">
                <table className="data-table">
                  <thead><tr><th>Etape</th><th>Lignes</th></tr></thead>
                  <tbody>
                    {pipelineSteps.map((step) => (
                      <tr key={step.label}>
                        <td>{step.label}</td>
                        <td>{Number(step.value || 0).toLocaleString("fr-FR")}</td>
                      </tr>
                    ))}
                    {!pipelineSteps.length ? <tr><td colSpan="2">Aucun controle pipeline disponible pour le moment.</td></tr> : null}
                  </tbody>
                </table>
              </div>
              {qualityWarnings.length ? (
                <div className="app-error">
                  {qualityWarnings.map((warning) => <div key={warning}>{warning}</div>)}
                </div>
              ) : null}
              <div className="data-table-wrap panel-scroll">
                <table className="data-table">
                  <thead><tr><th>Point a controler</th><th>Severite</th><th>Action recommandee</th></tr></thead>
                  <tbody>
                    {qualityAnomalies.slice(0, 12).map((item, index) => (
                      <tr key={`${item.code || item.type || "anomaly"}-${index}`}>
                        <td>{item.message || item.reason || item.code || item.type || "Anomalie detectee"}</td>
                        <td>{item.severity || item.niveau || "A controler"}</td>
                        <td>{item.action || "Verifier la ligne source avant synchronisation."}</td>
                      </tr>
                    ))}
                    {!qualityAnomalies.length ? <tr><td colSpan="3">Aucune anomalie detaillee remontee par le dernier controle.</td></tr> : null}
                  </tbody>
                </table>
              </div>
              {dataQuality.isLoading ? <p>Controle qualite en cours...</p> : null}
              {dataQuality.error ? <p className="app-error">Controle qualite indisponible : {dataQuality.error.message}</p> : null}
            </div>
          ) : null}

          {tab === "history" ? (
            <div className="data-table-wrap panel-scroll">
              <table className="data-table">
                <thead><tr><th>Date</th><th>Fichier</th><th>Score</th><th>Lignes</th><th>CAPEX</th><th>Ecart</th></tr></thead>
                <tbody>
                  {importHistory.map((item) => (
                    <tr key={item.import_id || `${item.fichier}-${item.created_at}`}>
                      <td>{item.created_at ? new Date(item.created_at).toLocaleString("fr-FR") : "-"}</td>
                      <td>{item.fichier || "-"}</td>
                      <td>{Math.round(Number(item.score_qualite || 0))}%</td>
                      <td>{Number(item.lignes_fact_metre || 0).toLocaleString("fr-FR")}</td>
                      <td>{Number(item.capex_fact_metre || 0).toLocaleString("fr-FR")}</td>
                      <td>{(Number(item.ecart_capex_pct || 0) * 100).toFixed(3)}%</td>
                    </tr>
                  ))}
                  {!importHistory.length ? <tr><td colSpan="6">Aucun historique persistant disponible avant le prochain envoi en base.</td></tr> : null}
                </tbody>
              </table>
            </div>
          ) : null}
        </AnalyticsCard>
        <aside className="context-panel">
          <AnalyticsCard title="Action suivante" eyebrow="Parcours projet">
            <ul className="signal-list">
              <li>1. Selectionner le fichier Excel DQE/BPU.</li>
              {(aiSuggestions.next_actions || [
                "2. Lancer l'analyse pour verifier feuille, lignes et mapping.",
                "3. Synchroniser PostgreSQL uniquement si la preview est correcte.",
                "4. Lancer ensuite la simulation budgetaire.",
              ]).map((action) => <li key={action}>{action}</li>)}
            </ul>
          </AnalyticsCard>
          <AnalyticsCard title="Statut de l'import" eyebrow="DQE vers SP2I">
            <ul className="signal-list">
              <li>File ID : {analysis?.file_id || "-"}</li>
              <li>Apercu IA : {analysis ? "OK" : "en attente"}</li>
              <li>Validation humaine : {validationResult ? "OK" : "non validee"}</li>
              <li>Envoi en base projet : {syncResult ? "OK" : "non lance"}</li>
              <li>Endpoint preview : /api/upload/excel</li>
              <li>Endpoint sync : /api/upload/excel/sync</li>
            </ul>
          </AnalyticsCard>
        </aside>
      </section>
    </main>
  );
}
