import React from "react";
import { createRoot } from "react-dom/client";
import { BarChart3, Building2, Ship } from "lucide-react";
import Direction from "./pages/Direction";
import Chantier from "./pages/Chantier";
import Import from "./pages/Import";
import "./styles.css";

const vues = [
  { id: "direction", libelle: "Direction", icone: BarChart3, composant: <Direction /> },
  { id: "chantier", libelle: "Chantier", icone: Building2, composant: <Chantier /> },
  { id: "import", libelle: "Import", icone: Ship, composant: <Import /> },
];

function App() {
  const [vueActive, setVueActive] = React.useState("direction");
  const vue = vues.find((item) => item.id === vueActive) ?? vues[0];

  return (
    <div className="application">
      <aside className="navigation">
        <strong>SP2I CAPEX</strong>
        <nav>
          {vues.map((item) => {
            const Icone = item.icone;
            return (
              <button
                key={item.id}
                className={item.id === vueActive ? "actif" : ""}
                onClick={() => setVueActive(item.id)}
                title={item.libelle}
              >
                <Icone size={18} />
                <span>{item.libelle}</span>
              </button>
            );
          })}
        </nav>
      </aside>
      {vue.composant}
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
