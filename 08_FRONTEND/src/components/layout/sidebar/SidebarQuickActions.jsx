import React from "react";
import { sidebarQuickActions } from "../../../navigation/sidebarConfig";
import { useSidebarStore } from "./sidebarStore";

export default function SidebarQuickActions({ onNavigate }) {
  const { isCollapsed, closeMobile } = useSidebarStore();

  const handleClick = (path) => {
    onNavigate(path);
    closeMobile();
  };

  return (
    <div className="sidebar-quick-actions" aria-label="Actions rapides">
      {sidebarQuickActions.map((action) => {
        const Icon = action.icon;
        return (
          <button key={action.label} type="button" onClick={() => handleClick(action.path)} title={isCollapsed ? action.label : undefined}>
            <Icon size={16} />
            <span>{action.label}</span>
          </button>
        );
      })}
    </div>
  );
}
