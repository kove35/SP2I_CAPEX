import React from "react";
import { Anchor, Boxes, Ship, Truck } from "lucide-react";
import { formatMoney } from "../../../shared/formatters";

export default function LogistiquePanel({ logistics = {} }) {
  const items = [
    { label: "Containers", value: logistics.containers || 0, icon: Boxes },
    { label: "Lignes import", value: logistics.importOrders || 0, icon: Ship },
    { label: "ETA moyen", value: `${Math.round(Number(logistics.averageEta || 0))} j`, icon: Truck },
    { label: "Douane", value: logistics.customsStatus || "À planifier", icon: Anchor },
  ];
  return (
    <article className="appro-panel">
      <header className="appro-panel-header">
        <div>
          <span>Logistique</span>
          <strong>Containers, port, douane et chantier</strong>
        </div>
      </header>
      <div className="appro-logistics-grid">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.label}>
              <span><Icon size={14} /> {item.label}</span>
              <strong>{item.value}</strong>
            </div>
          );
        })}
      </div>
      <div className="appro-logistics-flow">
        {["Commande", "Fabrication", "Maritime", "Port", "Douane", "Chantier"].map((step) => <span key={step}>{step}</span>)}
      </div>
      <p className="appro-prudent-note">Coût transport estimé : {formatMoney(logistics.transportCost)}. À consolider avec les volumes, incoterms et disponibilités chantier.</p>
    </article>
  );
}
