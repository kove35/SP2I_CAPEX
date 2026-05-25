import {
  BarChart3,
  Building2,
  Database,
  FileSpreadsheet,
  GitCompare,
  Gauge,
  PackageSearch,
  Play,
  Settings,
  ShieldAlert,
  Truck,
  Upload,
  Users,
  Workflow,
} from "lucide-react";

// Actions projet disponibles hors sidebar, via ProjectQuickActions.
export const sidebarQuickActions = [
  { label: "Importer DQE", path: "/app/dqe?tab=import", icon: Upload },
  { label: "Nouveau scénario", path: "/app/simulation?tab=scenarios", icon: GitCompare },
  { label: "Tester un scénario", path: "/app/simulation", icon: Play },
];

export const sidebarSections = [
  {
    id: "general",
    area: "general",
    title: "Général",
    icon: Building2,
    items: [
      { label: "Mes projets", path: "/app/projects", icon: Building2 },
      { label: "Organisation", icon: Building2, disabled: true, badge: "bientôt" },
      { label: "Utilisateurs", path: "/app/analytics?dashboard=users", icon: Users },
    ],
  },
  {
    id: "workspace",
    area: "workspace",
    title: "Workspace projet",
    icon: Gauge,
    requiresProject: true,
    items: [
      { label: "Synthèse", path: "/app", icon: Gauge },
      { label: "DQE & données", path: "/app/dqe?tab=import", icon: FileSpreadsheet },
      { label: "Gouvernance", path: "/app/governance-cockpit", icon: ShieldAlert },
      { label: "Scénarios", path: "/app/simulation", icon: Play },
      { label: "Approvisionnement", path: "/app/procurement?tab=import", icon: PackageSearch },
      { label: "Pilotage appro.", path: "/app/approvisionnement", icon: Truck },
      { label: "Exécution", path: "/app/site?tab=planning", icon: Workflow },
      { label: "Pilotage", path: "/app/analytics?dashboard=direction", icon: BarChart3 },
      { label: "Documents", path: "/app/dqe?tab=history", icon: Database, badge: "audit" },
    ],
  },
  {
    id: "other",
    area: "other",
    title: "Autre",
    icon: Settings,
    items: [
      { label: "Paramètres", path: "/app/analytics?dashboard=admin", icon: Settings },
      { label: "Système", path: "/app/analytics?dashboard=monitoring", icon: Truck },
    ],
  },
];
