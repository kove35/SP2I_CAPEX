import React from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import SidebarItem from "./SidebarItem";
import { useSidebarStore } from "./sidebarStore";

export default function SidebarSection({ section, activePath, onNavigate }) {
  const { isCollapsed, openedSections, toggleSection } = useSidebarStore();
  const Icon = section.icon;
  const isOpen = openedSections.includes(section.id);
  const activeRoute = activePath.split("?")[0];
  const activeSearch = activePath.split("?")[1] || "";
  const hasActiveItem = section.items.some((item) => {
    const itemRoute = item.path.split("?")[0];
    const itemSearch = item.path.split("?")[1] || "";
    return item.path === activePath || (itemRoute === activeRoute && (itemSearch ? activeSearch === itemSearch : !activeSearch));
  });
  const shouldRenderItems = isOpen && !isCollapsed;

  return (
    <section className={`sidebar-section ${isOpen ? "open" : ""} ${hasActiveItem ? "has-active" : ""}`}>
      <button
        type="button"
        className="sidebar-section-trigger"
        onClick={() => toggleSection(section.id)}
        title={isCollapsed ? section.title : undefined}
      >
        <span className="sidebar-section-icon"><Icon size={17} /></span>
        <span className="sidebar-section-title">{section.title}</span>
        {section.badge ? <span className="sidebar-section-badge">{section.badge}</span> : null}
        <span className="sidebar-section-chevron">{isOpen ? <ChevronDown size={15} /> : <ChevronRight size={15} />}</span>
      </button>
      {shouldRenderItems ? (
        <div className="sidebar-section-items">
          {section.items.map((item) => (
            <SidebarItem key={`${section.id}-${item.label}`} item={item} activePath={activePath} onNavigate={onNavigate} />
          ))}
        </div>
      ) : null}
    </section>
  );
}
