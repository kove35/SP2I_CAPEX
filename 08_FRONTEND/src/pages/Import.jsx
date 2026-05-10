import React from "react";

const API_BASE_URL = "http://localhost:8000";
const LIGNES_PAR_PAGE = 10;

const exempleLignes = [
  {
    id_ligne: "DEMO-001",
    designation: "Beton arme pour fondations",
    quantite: 12,
    unite: "m3",
    prix_unitaire_ht: 95000,
    prix_total_ht: 1140000,
    famille: "gros_oeuvre",
    statut_ligne: "OK",
  },
  {
    id_ligne: "DEMO-002",
    designation: "Cable electrique principal",
    quantite: 0,
    unite: "ml",
    prix_unitaire_ht: 4200,
    prix_total_ht: 0,
    famille: "electricite",
    statut_ligne: "QUANTITE_INVALIDE",
  },
  {
    id_ligne: "DEMO-003",
    designation: "Climatisation split",
    quantite: 8,
    unite: "u",
    prix_unitaire_ht: 240000,
    prix_total_ht: 2500000,
    famille: "climatisation",
    statut_ligne: "ECART_PRIX_SUP_20",
  },
];

export default function Import() {
  const [apiStatus, setApiStatus] = React.useState("CHECKING");
  const [fichier, setFichier] = React.useState(null);
  const [rawData, setRawData] = React.useState(exempleLignes);
  const [editableData, setEditableData] = React.useState(exempleLignes);
  const [uploadEnCours, setUploadEnCours] = React.useState(false);
  const [filtreStatut, setFiltreStatut] = React.useState("TOUS");
  const [filtreTexte, setFiltreTexte] = React.useState("");
  const [filtreFamille, setFiltreFamille] = React.useState("TOUTES");
  const [tri, setTri] = React.useState({ champ: "designation", direction: "asc" });
  const [page, setPage] = React.useState(1);
  const [logs, setLogs] = React.useState([
    "Interface DQE Control Center initialisee.",
    "Des lignes de demonstration sont affichees tant qu'aucun DQE n'est uploade.",
  ]);

  const ajouterLog = (message) => {
    const heure = new Date().toLocaleTimeString();
    setLogs((logsActuels) => [`${heure} - ${message}`, ...logsActuels]);
  };

  const appelerApi = async (url, options = {}) => {
    const reponse = await fetch(`${API_BASE_URL}${url}`, options);
    const contenu = await reponse.json().catch(() => ({}));

    if (!reponse.ok) {
      throw new Error(contenu.detail || contenu.error || `Erreur HTTP ${reponse.status}`);
    }

    return contenu;
  };

  const verifierApi = React.useCallback(async () => {
    setApiStatus("CHECKING");
    ajouterLog("GET /health envoye.");

    try {
      await appelerApi("/health");
      setApiStatus("OK");
      ajouterLog("API disponible.");
    } catch (erreur) {
      setApiStatus("KO");
      ajouterLog(`API indisponible : ${erreur.message}`);
    }
  }, []);

  React.useEffect(() => {
    verifierApi();
  }, [verifierApi]);

  const convertirNombre = (valeur) => {
    const nombre = Number(String(valeur).replace(",", "."));
    return Number.isFinite(nombre) ? nombre : 0;
  };

  const recalculerStatut = (ligne) => {
    const quantite = convertirNombre(ligne.quantite);
    const prixUnitaire = convertirNombre(ligne.prix_unitaire_ht);
    const prixTotal = convertirNombre(ligne.prix_total_ht);
    const prixCalcule = quantite * prixUnitaire;

    if (quantite <= 0) return "QUANTITE_INVALIDE";
    if (prixUnitaire <= 0) return "PRIX_UNITAIRE_INVALIDE";
    if (prixTotal <= 0) return "PRIX_TOTAL_INVALIDE";
    if (prixCalcule > 0 && Math.abs(prixTotal - prixCalcule) / prixCalcule > 0.2) {
      return "ECART_PRIX_SUP_20";
    }

    return "OK";
  };

  const normaliserLigne = (ligne, index) => {
    const quantite = convertirNombre(ligne.quantite);
    const prixUnitaire = convertirNombre(ligne.prix_unitaire_ht);
    const prixTotal = Number((quantite * prixUnitaire).toFixed(2));
    const ligneNormalisee = {
      id_ligne: ligne.id_ligne || ligne.cle_metier || `DQE-${index + 1}`,
      designation: ligne.designation || "",
      quantite,
      unite: ligne.unite || "u",
      prix_unitaire_ht: prixUnitaire,
      prix_total_ht: prixTotal,
      famille: ligne.famille || "default",
      statut_ligne: ligne.statut_ligne || "OK",
    };

    return {
      ...ligneNormalisee,
      statut_ligne: recalculerStatut(ligneNormalisee),
    };
  };

  const extraireLignesDepuisReponse = (reponse) => {
    const candidats = [
      reponse?.lignes,
      reponse?.resume?.lignes,
      reponse?.data,
      reponse?.resultats,
      reponse?.dqe?.lignes,
    ];

    return candidats.find((candidat) => Array.isArray(candidat)) || [];
  };

  const statistiques = React.useMemo(() => {
    const total = rawData.length;
    const anomalies = editableData.filter((ligne) => ligne.statut_ligne !== "OK").length;
    const lignesOk = total - anomalies;
    const score = total ? Math.round((lignesOk / total) * 100) : 0;

    return { total, anomalies, lignesOk, score };
  }, [rawData, editableData]);

  const familles = React.useMemo(() => {
    return [...new Set(editableData.map((ligne) => ligne.famille).filter(Boolean))].sort();
  }, [editableData]);

  const filteredData = React.useMemo(() => {
    const texte = filtreTexte.trim().toLowerCase();

    return editableData
      .map((ligne, index) => ({ ...ligne, indexOriginal: index }))
      .filter((ligne) => {
        const correspondStatut =
          filtreStatut === "TOUS" ||
          (filtreStatut === "OK" && ligne.statut_ligne === "OK") ||
          (filtreStatut === "ANOMALIES" && ligne.statut_ligne !== "OK");
        const correspondTexte = !texte || ligne.designation.toLowerCase().includes(texte);
        const correspondFamille = filtreFamille === "TOUTES" || ligne.famille === filtreFamille;

        return correspondStatut && correspondTexte && correspondFamille;
      })
      .sort((a, b) => {
        const valeurA = a[tri.champ];
        const valeurB = b[tri.champ];
        const direction = tri.direction === "asc" ? 1 : -1;

        if (typeof valeurA === "number" && typeof valeurB === "number") {
          return (valeurA - valeurB) * direction;
        }

        return String(valeurA ?? "").localeCompare(String(valeurB ?? "")) * direction;
      });
  }, [editableData, filtreStatut, filtreTexte, filtreFamille, tri]);

  const totalPages = Math.max(1, Math.ceil(filteredData.length / LIGNES_PAR_PAGE));
  const pageCourante = Math.min(page, totalPages);
  const paginatedData = filteredData.slice(
    (pageCourante - 1) * LIGNES_PAR_PAGE,
    pageCourante * LIGNES_PAR_PAGE
  );

  React.useEffect(() => {
    setPage(1);
  }, [filtreStatut, filtreTexte, filtreFamille]);

  const statutGlobal = React.useMemo(() => {
    if (statistiques.score > 90) {
      return {
        classe: "dqe-status-ok",
        titre: "DQE fiable",
        texte: "Le niveau de qualite est excellent. Le fichier peut etre exploite pour analyse.",
      };
    }

    if (statistiques.score > 70) {
      return {
        classe: "dqe-status-warning",
        titre: "DQE a controler",
        texte: "Certaines lignes doivent etre corrigees avant exploitation BI.",
      };
    }

    return {
      classe: "dqe-status-error",
      titre: "DQE critique",
      texte: "Le score qualite est trop faible. Corrige les anomalies avant decision.",
    };
  }, [statistiques.score]);

  const modifierTri = (champ) => {
    setTri((triActuel) => ({
      champ,
      direction:
        triActuel.champ === champ && triActuel.direction === "asc" ? "desc" : "asc",
    }));
  };

  const indicateurTri = (champ) => {
    if (tri.champ !== champ) return "↕";
    return tri.direction === "asc" ? "↑" : "↓";
  };

  const modifierLigne = (indexOriginal, champ, valeur) => {
    setEditableData((lignesActuelles) =>
      lignesActuelles.map((ligne, ligneIndex) => {
        if (ligneIndex !== indexOriginal) return ligne;

        const ligneModifiee = {
          ...ligne,
          [champ]:
            champ === "quantite" || champ === "prix_unitaire_ht"
              ? convertirNombre(valeur)
              : valeur,
        };

        const quantite = convertirNombre(ligneModifiee.quantite);
        const prixUnitaire = convertirNombre(ligneModifiee.prix_unitaire_ht);
        const prixTotal = Number((quantite * prixUnitaire).toFixed(2));
        const ligneRecalculee = { ...ligneModifiee, prix_total_ht: prixTotal };

        return {
          ...ligneRecalculee,
          statut_ligne: recalculerStatut(ligneRecalculee),
        };
      })
    );
  };

  const gererSelectionFichier = (event) => {
    const fichierSelectionne = event.target.files?.[0];
    if (!fichierSelectionne) return;

    if (!fichierSelectionne.name.toLowerCase().endsWith(".json")) {
      setFichier(null);
      ajouterLog("Erreur : seul un fichier JSON est accepte pour /dqe/upload.");
      return;
    }

    setFichier(fichierSelectionne);
    ajouterLog(`Fichier selectionne : ${fichierSelectionne.name}`);
  };

  const lireLignesDepuisFichier = async (fichierJson) => {
    const texte = await fichierJson.text();
    const donnees = JSON.parse(texte);
    const lignesFichier = extraireLignesDepuisReponse(donnees);

    if (!lignesFichier.length) {
      throw new Error("Le JSON ne contient pas de tableau lignes exploitable.");
    }

    return lignesFichier.map(normaliserLigne);
  };

  const uploaderDqe = async () => {
    if (!fichier) {
      ajouterLog("Upload annule : aucun fichier JSON selectionne.");
      return;
    }

    const formData = new FormData();
    formData.append("fichier", fichier);
    setUploadEnCours(true);
    ajouterLog("POST /dqe/upload envoye.");

    try {
      const lignesFichier = await lireLignesDepuisFichier(fichier);
      setRawData(lignesFichier);
      setEditableData(lignesFichier);
      setPage(1);
      ajouterLog(`${lignesFichier.length} lignes chargees depuis le fichier source.`);

      const reponse = await appelerApi("/dqe/upload", {
        method: "POST",
        body: formData,
      });

      const lignesApi = extraireLignesDepuisReponse(reponse);

      if (lignesApi.length > 0) {
        const lignesNormaliseesApi = lignesApi.map(normaliserLigne);
        setRawData(lignesNormaliseesApi);
        setEditableData(lignesNormaliseesApi);
        setPage(1);
        ajouterLog(`${lignesApi.length} lignes recues depuis l'API.`);
      } else {
        ajouterLog("Upload termine. KPI conserve depuis le JSON source local.");
      }

      if (Array.isArray(reponse.logs)) {
        setLogs((logsActuels) => [...reponse.logs, ...logsActuels]);
      }
    } catch (erreur) {
      ajouterLog(`Erreur API upload : ${erreur.message}`);
    } finally {
      setUploadEnCours(false);
    }
  };

  const recalculerToutesLesLignes = () => {
    setEditableData((lignesActuelles) => lignesActuelles.map(normaliserLigne));
    ajouterLog("Recalcul manuel effectue sur toutes les lignes.");
  };

  const exporterCsv = () => {
    const colonnes = [
      "designation",
      "quantite",
      "unite",
      "prix_unitaire_ht",
      "prix_total_ht",
      "famille",
      "statut_ligne",
    ];
    const contenu = [
      colonnes.join(";"),
      ...filteredData.map((ligne) =>
        colonnes
          .map((colonne) => `"${String(ligne[colonne] ?? "").replaceAll('"', '""')}"`)
          .join(";")
      ),
    ].join("\n");
    const blob = new Blob([contenu], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const lien = document.createElement("a");
    lien.href = url;
    lien.download = "dqe_control_center.csv";
    lien.click();
    URL.revokeObjectURL(url);
    ajouterLog("Export CSV genere avec les filtres actifs.");
  };

  const exporterBi = () => {
    const donneesBi = filteredData.map((ligne) => ({
      id_ligne: ligne.id_ligne,
      designation: ligne.designation,
      famille: ligne.famille,
      quantite: ligne.quantite,
      unite: ligne.unite,
      prix_unitaire_ht: ligne.prix_unitaire_ht,
      prix_total_ht: ligne.prix_total_ht,
      montant_local: ligne.prix_total_ht,
      statut_ligne: ligne.statut_ligne,
      decision_import: "A_ANALYSER",
      source: "DQE_CONTROL_CENTER",
    }));
    const blob = new Blob([JSON.stringify(donneesBi, null, 2)], {
      type: "application/json;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const lien = document.createElement("a");
    lien.href = url;
    lien.download = "dqe_export_bi.json";
    lien.click();
    URL.revokeObjectURL(url);
    ajouterLog("Export BI JSON genere avec les filtres actifs.");
  };

  const classeStatut = (statut) => {
    if (statut === "OK") return "dqe-badge-ok";
    if (String(statut).includes("ECART")) return "dqe-badge-warning";
    return "dqe-badge-error";
  };

  const classeLigne = (statut) => {
    if (statut === "OK") return "dqe-row-ok";
    if (String(statut).includes("ECART")) return "dqe-row-warning";
    return "dqe-row-error";
  };

  return (
    <main className="dqe-center">
      <style>{`
        .dqe-center {
          min-height: 100vh;
          padding: 28px;
          background: #f3f6fa;
          color: #0f172a;
          font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        .dqe-shell { max-width: 1500px; margin: 0 auto; display: grid; gap: 20px; }
        .dqe-header {
          display: flex; justify-content: space-between; gap: 18px; align-items: center;
          padding: 24px; border-radius: 18px; background: linear-gradient(135deg, #1e3a5f, #2563eb);
          color: #fff; box-shadow: 0 18px 45px rgba(30, 58, 95, 0.18);
        }
        .dqe-eyebrow { margin: 0 0 8px; color: #bfdbfe; font-size: 12px; font-weight: 800; letter-spacing: .18em; text-transform: uppercase; }
        .dqe-title { margin: 0; font-size: clamp(28px, 4vw, 42px); line-height: 1.05; letter-spacing: 0; }
        .dqe-subtitle { margin: 10px 0 0; color: #dbeafe; max-width: 720px; line-height: 1.55; }
        .dqe-api-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
        .dqe-pill { display: inline-flex; align-items: center; gap: 8px; border-radius: 999px; padding: 10px 14px; font-weight: 800; font-size: 13px; background: rgba(255,255,255,.12); }
        .dqe-pill-ok { color: #064e3b; background: #d1fae5; }
        .dqe-pill-ko { color: #7f1d1d; background: #fee2e2; }
        .dqe-pill-checking { color: #78350f; background: #fef3c7; }
        .dqe-button {
          border: 0; border-radius: 12px; min-height: 42px; padding: 0 16px; font-weight: 800; cursor: pointer;
          background: #3b82f6; color: #fff; box-shadow: 0 10px 25px rgba(59,130,246,.22);
        }
        .dqe-button:hover { background: #2563eb; }
        .dqe-button.secondary { background: #fff; color: #1e3a5f; box-shadow: none; }
        .dqe-button.dark { background: #0f172a; }
        .dqe-button.ghost { background: #eef4ff; color: #1e3a5f; box-shadow: none; }
        .dqe-button:disabled { opacity: .55; cursor: not-allowed; }
        .dqe-kpis { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
        .dqe-card {
          background: #fff; border: 1px solid #dbe5f0; border-radius: 16px; padding: 18px;
          box-shadow: 0 10px 26px rgba(15,23,42,.06);
        }
        .dqe-kpi-label { margin: 0; color: #64748b; font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: .06em; }
        .dqe-kpi-value { display: block; margin-top: 10px; font-size: 34px; color: #1e3a5f; line-height: 1; }
        .dqe-kpi-help { margin: 8px 0 0; color: #64748b; font-size: 13px; }
        .dqe-status {
          border-radius: 16px; padding: 16px 18px; border: 1px solid; display: flex; justify-content: space-between; gap: 12px; align-items: center;
        }
        .dqe-status h2 { margin: 0 0 4px; font-size: 18px; }
        .dqe-status p { margin: 0; font-size: 14px; }
        .dqe-status-ok { background: #ecfdf5; border-color: #a7f3d0; color: #065f46; }
        .dqe-status-warning { background: #fffbeb; border-color: #fde68a; color: #92400e; }
        .dqe-status-error { background: #fef2f2; border-color: #fecaca; color: #991b1b; }
        .dqe-layout { display: grid; grid-template-columns: minmax(0, 1fr) 340px; gap: 18px; align-items: start; }
        .dqe-panel { background: #fff; border: 1px solid #dbe5f0; border-radius: 18px; box-shadow: 0 10px 26px rgba(15,23,42,.06); overflow: hidden; }
        .dqe-panel-header { padding: 18px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
        .dqe-panel-title { margin: 0; color: #1e3a5f; font-size: 20px; }
        .dqe-panel-text { margin: 6px 0 0; color: #64748b; font-size: 14px; }
        .dqe-filters { padding: 14px 18px; border-bottom: 1px solid #e2e8f0; display: grid; grid-template-columns: 1.2fr .8fr .8fr; gap: 12px; background: #f8fafc; }
        .dqe-field label { display: block; margin-bottom: 6px; color: #475569; font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: .05em; }
        .dqe-input, .dqe-select {
          width: 100%; min-height: 40px; border: 1px solid #cbd5e1; border-radius: 10px; background: #fff;
          padding: 0 11px; color: #0f172a; outline: none; font: inherit;
        }
        .dqe-input:focus, .dqe-select:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,.14); }
        .dqe-table-wrap { overflow-x: auto; }
        .dqe-table { width: 100%; border-collapse: separate; border-spacing: 0; min-width: 1080px; }
        .dqe-table th {
          position: sticky; top: 0; z-index: 1; background: #f1f5f9; color: #334155;
          text-align: left; padding: 12px; border-bottom: 1px solid #cbd5e1; font-size: 12px; text-transform: uppercase; letter-spacing: .05em;
        }
        .dqe-sort { border: 0; background: transparent; color: inherit; font: inherit; font-weight: 900; cursor: pointer; display: inline-flex; gap: 6px; align-items: center; padding: 0; }
        .dqe-table td { padding: 10px 12px; border-bottom: 1px solid #e2e8f0; vertical-align: middle; }
        .dqe-row-ok { background: #fff; }
        .dqe-row-warning { background: #fffbeb; }
        .dqe-row-error { background: #fff7f7; }
        .dqe-cell-input {
          width: 100%; min-height: 36px; border: 1px solid #cbd5e1; border-radius: 9px; padding: 0 9px;
          background: rgba(255,255,255,.88); outline: none; font: inherit;
        }
        .dqe-cell-input:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,.12); }
        .dqe-money { font-weight: 900; color: #0f172a; text-align: right; white-space: nowrap; }
        .dqe-badge { display: inline-flex; border-radius: 999px; padding: 7px 10px; font-size: 11px; font-weight: 900; border: 1px solid; white-space: nowrap; }
        .dqe-badge-ok { color: #047857; background: #ecfdf5; border-color: #a7f3d0; }
        .dqe-badge-warning { color: #b45309; background: #fffbeb; border-color: #fde68a; }
        .dqe-badge-error { color: #b91c1c; background: #fef2f2; border-color: #fecaca; }
        .dqe-pagination { padding: 14px 18px; display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; background: #fff; }
        .dqe-page-actions { display: flex; gap: 10px; align-items: center; }
        .dqe-side { display: grid; gap: 18px; }
        .dqe-upload-box { border: 1px dashed #93c5fd; border-radius: 14px; padding: 14px; background: #eff6ff; }
        .dqe-file { width: 100%; font: inherit; font-size: 13px; }
        .dqe-log-box { max-height: 280px; overflow: auto; display: grid; gap: 8px; padding: 12px; background: #020617; border-radius: 14px; }
        .dqe-log-line { margin: 0; color: #cbd5e1; background: rgba(255,255,255,.06); padding: 9px; border-radius: 9px; font-size: 12px; line-height: 1.45; }
        @media (max-width: 1100px) {
          .dqe-layout { grid-template-columns: 1fr; }
          .dqe-filters { grid-template-columns: 1fr; }
        }
        @media (max-width: 760px) {
          .dqe-center { padding: 16px; }
          .dqe-header, .dqe-status { align-items: flex-start; flex-direction: column; }
          .dqe-kpis { grid-template-columns: 1fr; }
        }
      `}</style>

      <section className="dqe-shell">
        <header className="dqe-header">
          <div>
            <p className="dqe-eyebrow">SP2I CAPEX</p>
            <h1 className="dqe-title">DQE Control Center</h1>
            <p className="dqe-subtitle">
              Controle qualite, edition inline, filtres dynamiques, tri, pagination, upload DQE
              et exports pour exploitation metier.
            </p>
          </div>

          <div className="dqe-api-actions">
            <span
              className={`dqe-pill ${
                apiStatus === "OK"
                  ? "dqe-pill-ok"
                  : apiStatus === "KO"
                    ? "dqe-pill-ko"
                    : "dqe-pill-checking"
              }`}
            >
              {apiStatus === "OK" ? "● API OK" : apiStatus === "KO" ? "● API KO" : "● Verification"}
            </span>
            <button type="button" onClick={verifierApi} className="dqe-button secondary">
              Rafraichir
            </button>
          </div>
        </header>

        <section className="dqe-kpis">
          <article className="dqe-card">
            <p className="dqe-kpi-label">Nombre de lignes</p>
            <strong className="dqe-kpi-value">{statistiques.total}</strong>
            <p className="dqe-kpi-help">{filteredData.length} lignes apres filtres</p>
          </article>

          <article className="dqe-card">
            <p className="dqe-kpi-label">Anomalies</p>
            <strong className="dqe-kpi-value" style={{ color: "#dc2626" }}>
              {statistiques.anomalies}
            </strong>
            <p className="dqe-kpi-help">{statistiques.lignesOk} lignes OK</p>
          </article>

          <article className="dqe-card">
            <p className="dqe-kpi-label">Score qualite</p>
            <strong className="dqe-kpi-value" style={{ color: "#059669" }}>
              {statistiques.score}%
            </strong>
            <p className="dqe-kpi-help">Lignes OK / total</p>
          </article>
        </section>

        <section className={`dqe-status ${statutGlobal.classe}`}>
          <div>
            <h2>{statutGlobal.titre}</h2>
            <p>{statutGlobal.texte}</p>
          </div>
          <strong>{statistiques.score}%</strong>
        </section>

        <section className="dqe-layout">
          <article className="dqe-panel">
            <div className="dqe-panel-header">
              <div>
                <h2 className="dqe-panel-title">Table DQE professionnelle</h2>
                <p className="dqe-panel-text">
                  Clique sur les entetes pour trier. Les totaux se recalculent a chaque edition.
                </p>
              </div>
              <button type="button" onClick={recalculerToutesLesLignes} className="dqe-button">
                Recalculer
              </button>
            </div>

            <div className="dqe-filters">
              <div className="dqe-field">
                <label>Recherche designation</label>
                <input
                  className="dqe-input"
                  value={filtreTexte}
                  onChange={(event) => setFiltreTexte(event.target.value)}
                  placeholder="Ex: beton, cable, climatisation..."
                />
              </div>

              <div className="dqe-field">
                <label>Statut</label>
                <select
                  className="dqe-select"
                  value={filtreStatut}
                  onChange={(event) => setFiltreStatut(event.target.value)}
                >
                  <option value="TOUS">Tous</option>
                  <option value="OK">OK</option>
                  <option value="ANOMALIES">Anomalies uniquement</option>
                </select>
              </div>

              <div className="dqe-field">
                <label>Famille</label>
                <select
                  className="dqe-select"
                  value={filtreFamille}
                  onChange={(event) => setFiltreFamille(event.target.value)}
                >
                  <option value="TOUTES">Toutes</option>
                  {familles.map((famille) => (
                    <option key={famille} value={famille}>
                      {famille}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="dqe-table-wrap">
              <table className="dqe-table">
                <thead>
                  <tr>
                    <th>
                      <button className="dqe-sort" onClick={() => modifierTri("designation")}>
                        Designation {indicateurTri("designation")}
                      </button>
                    </th>
                    <th>
                      <button className="dqe-sort" onClick={() => modifierTri("quantite")}>
                        Quantite {indicateurTri("quantite")}
                      </button>
                    </th>
                    <th>Unite</th>
                    <th>
                      <button className="dqe-sort" onClick={() => modifierTri("prix_unitaire_ht")}>
                        PU HT {indicateurTri("prix_unitaire_ht")}
                      </button>
                    </th>
                    <th>
                      <button className="dqe-sort" onClick={() => modifierTri("prix_total_ht")}>
                        Total HT {indicateurTri("prix_total_ht")}
                      </button>
                    </th>
                    <th>
                      <button className="dqe-sort" onClick={() => modifierTri("famille")}>
                        Famille {indicateurTri("famille")}
                      </button>
                    </th>
                    <th>Statut</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedData.map((ligne) => (
                    <tr key={ligne.id_ligne || ligne.indexOriginal} className={classeLigne(ligne.statut_ligne)}>
                      <td style={{ minWidth: 280 }}>
                        <input
                          className="dqe-cell-input"
                          value={ligne.designation}
                          onChange={(event) =>
                            modifierLigne(ligne.indexOriginal, "designation", event.target.value)
                          }
                        />
                      </td>
                      <td style={{ minWidth: 110 }}>
                        <input
                          className="dqe-cell-input"
                          type="number"
                          value={ligne.quantite}
                          onChange={(event) =>
                            modifierLigne(ligne.indexOriginal, "quantite", event.target.value)
                          }
                        />
                      </td>
                      <td style={{ minWidth: 90 }}>
                        <input
                          className="dqe-cell-input"
                          value={ligne.unite}
                          onChange={(event) =>
                            modifierLigne(ligne.indexOriginal, "unite", event.target.value)
                          }
                        />
                      </td>
                      <td style={{ minWidth: 130 }}>
                        <input
                          className="dqe-cell-input"
                          type="number"
                          value={ligne.prix_unitaire_ht}
                          onChange={(event) =>
                            modifierLigne(ligne.indexOriginal, "prix_unitaire_ht", event.target.value)
                          }
                        />
                      </td>
                      <td className="dqe-money" style={{ minWidth: 140 }}>
                        {Number(ligne.prix_total_ht).toLocaleString("fr-FR")}
                      </td>
                      <td style={{ minWidth: 160 }}>
                        <input
                          className="dqe-cell-input"
                          value={ligne.famille}
                          onChange={(event) =>
                            modifierLigne(ligne.indexOriginal, "famille", event.target.value)
                          }
                        />
                      </td>
                      <td style={{ minWidth: 170 }}>
                        <span className={`dqe-badge ${classeStatut(ligne.statut_ligne)}`}>
                          {ligne.statut_ligne}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="dqe-pagination">
              <span>
                {filteredData.length} ligne(s) trouvee(s) · {LIGNES_PAR_PAGE} par page
              </span>
              <div className="dqe-page-actions">
                <button
                  type="button"
                  className="dqe-button ghost"
                  onClick={() => setPage((pageActuelle) => Math.max(1, pageActuelle - 1))}
                  disabled={pageCourante === 1}
                >
                  {"<<"} Precedent
                </button>
                <strong>
                  Page {pageCourante} / {totalPages}
                </strong>
                <button
                  type="button"
                  className="dqe-button ghost"
                  onClick={() => setPage((pageActuelle) => Math.min(totalPages, pageActuelle + 1))}
                  disabled={pageCourante === totalPages}
                >
                  Suivant {">>"}
                </button>
              </div>
            </div>
          </article>

          <aside className="dqe-side">
            <section className="dqe-card">
              <h2 className="dqe-panel-title">Upload DQE</h2>
              <p className="dqe-panel-text">Envoie un fichier JSON vers l'endpoint /dqe/upload.</p>
              <div className="dqe-upload-box" style={{ marginTop: 14 }}>
                <input
                  className="dqe-file"
                  type="file"
                  accept=".json,application/json"
                  onChange={gererSelectionFichier}
                />
              </div>
              {fichier && <p className="dqe-panel-text">{fichier.name}</p>}
              <button
                type="button"
                onClick={uploaderDqe}
                disabled={!fichier || uploadEnCours || apiStatus !== "OK"}
                className="dqe-button dark"
                style={{ width: "100%", marginTop: 14 }}
              >
                {uploadEnCours ? "Upload en cours..." : "Uploader"}
              </button>
            </section>

            <section className="dqe-card">
              <h2 className="dqe-panel-title">Export</h2>
              <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
                <button type="button" onClick={exporterCsv} className="dqe-button">
                  Export CSV
                </button>
                <button type="button" onClick={exporterBi} className="dqe-button dark">
                  Export BI
                </button>
              </div>
            </section>

            <section className="dqe-card" style={{ background: "#0f172a", color: "#fff" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                <h2 className="dqe-panel-title" style={{ color: "#fff" }}>Logs</h2>
                <button type="button" onClick={() => setLogs([])} className="dqe-button ghost">
                  Vider
                </button>
              </div>
              <div className="dqe-log-box" style={{ marginTop: 14 }}>
                {logs.length ? (
                  logs.map((log, index) => (
                    <p className="dqe-log-line" key={`${log}-${index}`}>
                      {log}
                    </p>
                  ))
                ) : (
                  <p className="dqe-log-line">Aucun log pour le moment.</p>
                )}
              </div>
            </section>
          </aside>
        </section>
      </section>
    </main>
  );
}
