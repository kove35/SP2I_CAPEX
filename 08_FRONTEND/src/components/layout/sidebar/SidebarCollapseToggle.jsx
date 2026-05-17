import React from "react";
import { ChevronsLeft, ChevronsRight, Menu } from "lucide-react";
import { useSidebarStore } from "./sidebarStore";

export default function SidebarCollapseToggle() {
  const { isCollapsed, toggleCollapsed, toggleMobile } = useSidebarStore();

  return (
    <div className="sidebar-toggle-row">
      <button className="icon-button sidebar-mobile-trigger" type="button" onClick={toggleMobile} title="Ouvrir le menu">
        <Menu size={18} />
      </button>
      <button className="sidebar-collapse-toggle" type="button" onClick={toggleCollapsed} title={isCollapsed ? "Deplier" : "Replier"}>
        {isCollapsed ? <ChevronsRight size={16} /> : <ChevronsLeft size={16} />}
        <span>{isCollapsed ? "Ouvrir" : "Replier"}</span>
      </button>
    </div>
  );
}
