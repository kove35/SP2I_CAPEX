import React from "react";
import {
  BarChart3,
  Building2,
  CheckCircle2,
  CircleDollarSign,
  FileSpreadsheet,
  Menu,
  ShieldCheck,
} from "lucide-react";
import LoginCard from "./LoginCard";

const decisionPillars = [
  ["Budget travaux", "Pilotage financier", CircleDollarSign],
  ["DQE", "Donnees structurees", FileSpreadsheet],
  ["Decision", "Arbitrages strategiques", ShieldCheck],
  ["Chantier", "Suivi exécution", Building2],
  ["Pilotage", "Tableaux direction", BarChart3],
];

const optimizationEngines = [
  "Achats",
  "Import",
  "Chaine logistique",
  "Logistique chantier",
];

export default function LandingPage({ onNavigate }) {
  const openProjectHub = () => onNavigate("/app/projects");

  return (
    <main className="marketing-page one-screen">
      <section className="hero-section one-screen-hero">
        <nav className="marketing-nav">
          <strong>SP2I CAPEX</strong>
          <div>
            <button type="button" onClick={() => onNavigate("/app")}>Decouvrir SP2I</button>
            <details className="landing-menu">
              <summary aria-label="Ouvrir le menu SP2I">
                <Menu size={17} />
                <span>Menu</span>
              </summary>
              <div className="landing-menu-panel">
                <button type="button" onClick={openProjectHub}>Espace projet</button>
                <button type="button" onClick={() => onNavigate("/app/governance-cockpit")}>Gouvernance</button>
                <button type="button" onClick={() => onNavigate("/app/procurement-intelligence")}>Analyse achats</button>
                <button type="button" onClick={() => onNavigate("/app/analytics")}>Tableaux de pilotage</button>
              </div>
            </details>
          </div>
        </nav>

        <div className="hero-content one-screen-content">
          <div className="hero-copy">
            <p className="eyebrow">Pointe-Noire | Congo-Brazzaville</p>
            <h1>Systeme de Pilotage des Investissements Immobiliers</h1>
            <p>
              Plateforme SaaS collaborative pour piloter les projets immobiliers,
              isoler les workspaces, gouverner les DQE et suivre les decisions
              CAPEX avec plusieurs roles utilisateurs.
            </p>

            <div className="hero-actions">
              <button type="button" onClick={openProjectHub}>Se connecter</button>
              <button type="button" onClick={openProjectHub}>Creer un compte</button>
              <button type="button" onClick={() => onNavigate("/app")}>Decouvrir SP2I</button>
            </div>

            <div className="local-commercial-strip">
              <span>Directeur commercial Congo-Brazzaville</span>
              <strong>M. Gouadi Pierre</strong>
            </div>
          </div>

          <LoginCard onAuthenticated={openProjectHub} onDiscover={() => onNavigate("/app")} />
        </div>

        <div className="one-screen-bottom">
          <section className="one-screen-panel">
            <h2>Pilotage immobilier</h2>
            <div className="pillar-row">
              {decisionPillars.map(([title, text, Icon]) => (
                <article key={title}>
                  <Icon size={18} />
                  <strong>{title}</strong>
                  <span>{text}</span>
                </article>
              ))}
            </div>
          </section>

          <section className="one-screen-panel">
            <h2>Workspace collaboratif</h2>
            <div className="optimization-list">
              {["Utilisateurs", "Roles", "Projets", ...optimizationEngines.slice(0, 1)].map((item) => (
                <span key={item}><CheckCircle2 size={15} /> {item}</span>
              ))}
            </div>
            <p>Organisation, utilisateurs, projets et DQE deviennent les points d'entree du pilotage CAPEX.</p>
          </section>
        </div>
      </section>
    </main>
  );
}
