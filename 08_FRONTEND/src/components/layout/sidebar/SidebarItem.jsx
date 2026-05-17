import React from "react";
import { useSidebarStore } from "./sidebarStore";

export default function SidebarItem({ item, activePath, onNavigate }) {
  const { isCollapsed, closeMobile } = useSidebarStore();
  const Icon = item.icon;
  const activeRoute = activePath.split("?")[0];
  const itemRoute = item.path.split("?")[0];
  const activeSearch = activePath.split("?")[1] || "";
  const itemSearch = item.path.split("?")[1] || "";
  const isActive = item.path === activePath || (itemSearch ? itemRoute === activeRoute && activeSearch === itemSearch : itemRoute === activeRoute && !activeSearch);

  const handleNavigate = () => {
    onNavigate(item.path);
    closeMobile();
  };

  return (
    <button
      type="button"
      className={`sidebar-item ${isActive ? "active" : ""}`}
      onClick={handleNavigate}
      title={isCollapsed ? item.label : undefined}
    >
      <span className="sidebar-item-icon"><Icon size={17} /></span>
      <span className="sidebar-item-label">{item.label}</span>
      {item.badge ? <span className="sidebar-item-badge">{item.badge}</span> : null}
    </button>
  );
}
