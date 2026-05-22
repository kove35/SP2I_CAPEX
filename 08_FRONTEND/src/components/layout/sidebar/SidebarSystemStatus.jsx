import React, { useState } from "react";
import { CheckCircle2, Database, RadioTower } from "lucide-react";
import { useSidebarStore } from "./sidebarStore";

export default function SidebarSystemStatus() {
  const { isCollapsed, apiStatus, syncStatus } = useSidebarStore();
  const [showDetails, setShowDetails] = useState(false);
  const allOk = apiStatus === "online" && ["pret", "ready"].includes(syncStatus);

  if (isCollapsed) {
    return (
      <div className="sidebar-system-status-compact" title="Statut systeme">
        <span className={allOk ? "status-dot online" : "status-dot error"} />
      </div>
    );
  }

  return (
    <div className="sidebar-system-status">
      <button
        type="button"
        className="system-status-toggle"
        onClick={() => setShowDetails((value) => !value)}
        title="Statut des services"
      >
        <span className={allOk ? "status-dot online" : "status-dot error"} />
        <span className="status-label">{allOk ? "Services OK" : "Services a verifier"}</span>
      </button>

      {showDetails ? (
        <div className="system-status-details">
          <span title={`API ${apiStatus}`}>
            <RadioTower size={12} /> API {apiStatus}
          </span>
          <span title={`Synchronisation ${syncStatus}`}>
            <Database size={12} /> Sync {syncStatus}
          </span>
          <span title="PostgreSQL connecte">
            <CheckCircle2 size={12} /> PostgreSQL
          </span>
        </div>
      ) : null}
    </div>
  );
}
