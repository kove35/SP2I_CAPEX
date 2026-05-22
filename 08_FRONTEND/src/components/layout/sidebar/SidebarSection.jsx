import React from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import SidebarItem from "./SidebarItem";
import { useSidebarStore } from "./sidebarStore";

export default function SidebarSection({ section, activePath, onNavigate }) {
  const { isCollapsed, openedSections, toggleSection } = useSidebarStore();
  const Icon = section.icon;
  const activeRoute = activePath.split("?")[0];
  const activeSearch = activePath.split("?")[1] || "";
  const items = section.items || [];
  const sectionRoute = section.path?.split("?")[0] || "";
  const sectionSearch = section.path?.split("?")[1] || "";
  const isActiveSection = section.path
    ? section.path === activePath || (sectionRoute === activeRoute && (sectionSearch ? activeSearch === sectionSearch : !activeSearch))
    : false;
  const hasActiveItem = items.some((item) => {
    const itemRoute = item.path.split("?")[0];
    const itemSearch = item.path.split("?")[1] || "";
    return item.path === activePath || (itemRoute === activeRoute && (itemSearch ? activeSearch === itemSearch : !activeSearch));
  });
  const isOpen = openedSections.includes(section.id) || hasActiveItem;
  const shouldRenderItems = isOpen && !isCollapsed && items.length > 0;

  const handleTrigger = () => {
    if (section.path) {
      onNavigate(section.path);
      return;
    }
    toggleSection(section.id);
  };

  return (
    <section className={`sidebar-section ${isOpen ? "open" : ""} ${hasActiveItem || isActiveSection ? "has-active" : ""}`}>
      <button
        type="button"
        className="sidebar-section-trigger"
        onClick={handleTrigger}
        title={isCollapsed ? section.title : undefined}
      >
        <span className="sidebar-section-icon"><Icon size={17} /></span>
        <span className="sidebar-section-title">{section.title}</span>
        {section.badge ? <span className="sidebar-section-badge">{section.badge}</span> : null}
        {items.length > 0 ? (
          <span className="sidebar-section-chevron">{isOpen ? <ChevronDown size={15} /> : <ChevronRight size={15} />}</span>
        ) : null}
      </button>
      {shouldRenderItems ? (
        <div className="sidebar-section-items">
          {items.map((item) => (
            <SidebarItem key={`${section.id}-${item.label}`} item={item} activePath={activePath} onNavigate={onNavigate} />
          ))}
        </div>
      ) : null}
    </section>
  );
}
