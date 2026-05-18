import React from "react";
import {
  ArrowRight,
  BarChart3,
  Building2,
  CheckCircle2,
  CircleDollarSign,
  FileSpreadsheet,
  Gauge,
  LineChart,
  Menu,
  ShieldCheck,
} from "lucide-react";

const decisionPillars = [
  ["Budget travaux", "Pilotage financier", CircleDollarSign],
  ["DQE", "Donnees structurees", FileSpreadsheet],
  ["Decision", "Arbitrages strategiques", ShieldCheck],
  ["Chantier", "Suivi execution", Building2],
  ["Pilotage", "Tableaux direction", BarChart3],
];

const optimizationEngines = [
  "Achats",
  "Import",
  "Chaine logistique",
  "Logistique chantier",
];

export default function LandingPage({ onNavigate }) {
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
                <button type="button" onClick={() => onNavigate("/app")}>Cockpit</button>
                <button type="button" onClick={() => onNavigate("/app/simulation")}>Tester un scenario</button>
                <button type="button" onClick={() => onNavigate("/app/dqe")}>DQE & donnees</button>
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
              Plateforme decisionnelle de pilotage budgetaire, d'analyse strategique
              et d'optimisation immobiliere pour les projets et chantiers a
              Pointe-Noire.
            </p>

            <div className="hero-actions">
              <button type="button" onClick={() => onNavigate("/app/simulation")}>
                Lancer une simulation <ArrowRight size={17} />
              </button>
              <button type="button" onClick={() => onNavigate("/app")}>Voir le cockpit</button>
              <button type="button" onClick={() => onNavigate("/app/analytics")}>Pilotage direction</button>
            </div>

            <div className="local-commercial-strip">
              <span>Directeur commercial Congo-Brazzaville</span>
              <strong>M. Gouadi Pierre</strong>
            </div>
          </div>

          <div className="cockpit-mockup one-screen-mockup" aria-label="Mockup cockpit decisionnel SP2I">
            <div className="mockup-top">
              <span>Investment Decision Center</span>
              <strong>Live</strong>
            </div>
            <div className="mockup-grid">
              <article><span>Budget optimise</span><strong>1.9 Md</strong></article>
              <article><span>Rentabilite</span><strong>+14.6%</strong></article>
              <article><span>Scenarios</span><strong>12</strong></article>
              <article><span>Risque global</span><strong>MEDIUM</strong></article>
            </div>
            <div className="route-line">
              <span>DQE</span><i /><LineChart size={18} /><i /><span>Decision</span><i /><Gauge size={18} /><i /><span>Pilotage</span>
            </div>
          </div>
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
            <h2>Optimisation integree</h2>
            <div className="optimization-list">
              {optimizationEngines.map((item) => (
                <span key={item}><CheckCircle2 size={15} /> {item}</span>
              ))}
            </div>
            <p>Import, containers et logistique restent des leviers au service du budget travaux.</p>
          </section>
        </div>
      </section>
    </main>
  );
}
