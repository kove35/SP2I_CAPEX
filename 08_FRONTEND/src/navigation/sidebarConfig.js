import {
  Building2,
  GitCompare,
  Gauge,
  PackageSearch,
  Play,
  Settings,
  Upload,
  Workflow,
} from "lucide-react";

// Actions projet disponibles hors sidebar, via ProjectQuickActions.
export const sidebarQuickActions = [
  { label: "Importer DQE", path: "/app/dqe?tab=import", icon: Upload },
  { label: "Nouveau scenario", path: "/app/simulation?tab=scenarios", icon: GitCompare },
  { label: "Tester un scenario", path: "/app/simulation", icon: Play },
];

export const sidebarSections = [
  {
    id: "navigation",
    title: "Navigation",
    icon: Gauge,
    defaultOpen: true,
    items: [
      { label: "Vue d'ensemble", path: "/app", icon: Gauge },
      { label: "Projet", path: "/app/dqe?tab=import", icon: Building2 },
      { label: "Scenarios", path: "/app/simulation?tab=scenarios", icon: GitCompare },
      { label: "Execution", path: "/app/site?tab=planning", icon: Workflow },
      { label: "Approvisionnement", path: "/app/procurement?tab=import", icon: PackageSearch },
    ],
  },
  {
    id: "other",
    title: "Autre",
    icon: Settings,
    defaultOpen: true,
    items: [
      { label: "Parametres", path: "/app/analytics?dashboard=admin", icon: Settings },
    ],
  },
];
