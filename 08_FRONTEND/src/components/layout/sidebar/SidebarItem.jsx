import React from "react";
import { useSidebarStore } from "./sidebarStore";

export default function SidebarItem({ item, activePath, onNavigate }) {
  const { isCollapsed, closeMobile } = useSidebarStore();
  const Icon = item.icon;
  const itemPath = item.path || "";
  const activeRoute = activePath.split("?")[0];
  const itemRoute = itemPath.split("?")[0];
  const activeSearch = activePath.split("?")[1] || "";
  const itemSearch = itemPath.split("?")[1] || "";
  const isActive = !item.disabled && (itemPath === activePath || (itemSearch ? itemRoute === activeRoute && activeSearch === itemSearch : itemRoute === activeRoute && !activeSearch));

  const handleNavigate = () => {
    if (item.disabled || !itemPath) return;
    onNavigate(itemPath);
    closeMobile();
  };

  return (
    <button
      type="button"
      className={`sidebar-item ${isActive ? "active" : ""} ${item.disabled ? "disabled" : ""}`}
      onClick={handleNavigate}
      disabled={item.disabled}
      title={isCollapsed ? item.label : item.disabled ? `${item.label} bientot disponible` : undefined}
    >
      <span className="sidebar-item-icon"><Icon size={17} /></span>
      <span className="sidebar-item-label">{item.label}</span>
      {item.badge ? <span className="sidebar-item-badge">{item.badge}</span> : null}
    </button>
  );
}
