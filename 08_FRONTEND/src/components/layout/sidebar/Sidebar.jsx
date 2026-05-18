import React from "react";
import { X } from "lucide-react";
import { sidebarSections } from "../../../navigation/sidebarConfig";
import SidebarCollapseToggle from "./SidebarCollapseToggle";
import SidebarProjectStatus from "./SidebarProjectStatus";
import SidebarQuickActions from "./SidebarQuickActions";
import SidebarSection from "./SidebarSection";
import { useSidebarStore } from "./sidebarStore";

export default function Sidebar({ activePath, onNavigate }) {
  const { isCollapsed, isMobileOpen, closeMobile } = useSidebarStore();

  return (
    <>
      <aside className={`saas-sidebar modern-sidebar ${isCollapsed ? "collapsed" : ""} ${isMobileOpen ? "mobile-open" : ""}`}>
        <div className="brand-block modern-brand">
          <div className="brand-mark">S</div>
          <div className="brand-copy">
            <strong>SP2I</strong>
            <span>Pilotage immobilier</span>
          </div>
          <button className="icon-button sidebar-close-mobile" type="button" onClick={closeMobile} title="Fermer">
            <X size={18} />
          </button>
        </div>

        <SidebarCollapseToggle />
        <SidebarQuickActions onNavigate={onNavigate} />
        <SidebarProjectStatus />

        <nav className="sidebar-nav modern-sidebar-nav">
          {sidebarSections.map((section) => (
            <SidebarSection key={section.id} section={section} activePath={activePath} onNavigate={onNavigate} />
          ))}
        </nav>
      </aside>
      {isMobileOpen ? <button className="sidebar-mobile-backdrop" type="button" aria-label="Fermer le menu" onClick={closeMobile} /> : null}
    </>
  );
}
