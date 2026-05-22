import React from "react";
import { X } from "lucide-react";
import { sidebarSections } from "../../../navigation/sidebarConfig";
import SidebarCollapseToggle from "./SidebarCollapseToggle";
import SidebarProjectStatus from "./SidebarProjectStatus";
import SidebarSection from "./SidebarSection";
import SidebarSystemStatus from "./SidebarSystemStatus";
import { useSidebarStore } from "./sidebarStore";

export default function Sidebar({ activePath, onNavigate }) {
  const { isCollapsed, isMobileOpen, closeMobile, activeProject } = useSidebarStore();
  const generalSections = sidebarSections.filter((section) => section.area === "general");
  const workspaceSections = sidebarSections.filter((section) => section.area === "workspace");
  const otherSections = sidebarSections.filter((section) => section.area === "other");
  const hasProject = Boolean(activeProject);

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

        <nav className="sidebar-nav modern-sidebar-nav">
          {generalSections.map((section) => (
            <SidebarSection key={section.id} section={section} activePath={activePath} onNavigate={onNavigate} />
          ))}
        </nav>

        <SidebarProjectStatus onNavigate={onNavigate} />

        <nav className="sidebar-nav modern-sidebar-nav">
          {hasProject ? workspaceSections.map((section) => (
            <SidebarSection key={section.id} section={section} activePath={activePath} onNavigate={onNavigate} />
          )) : (
            <div className="sidebar-no-project">
              <span>Selectionnez un projet</span>
              <button type="button" onClick={() => onNavigate("/app/projects")}>Mes projets</button>
            </div>
          )}
        </nav>

        <nav className="sidebar-nav modern-sidebar-nav sidebar-nav-other">
          {otherSections.map((section) => (
            <SidebarSection key={section.id} section={section} activePath={activePath} onNavigate={onNavigate} />
          ))}
        </nav>

        <SidebarSystemStatus />
      </aside>
      {isMobileOpen ? <button className="sidebar-mobile-backdrop" type="button" aria-label="Fermer le menu" onClick={closeMobile} /> : null}
    </>
  );
}
