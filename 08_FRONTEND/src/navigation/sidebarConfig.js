import {
  AlertTriangle,
  BarChart3,
  Building2,
  Clock3,
  Database,
  FileSpreadsheet,
  GitCompare,
  Gauge,
  LayoutGrid,
  PackageSearch,
  Play,
  Route,
  Settings,
  ShieldAlert,
  Ship,
  Truck,
  Upload,
  Users,
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
    id: "overview",
    title: "Vue d'ensemble",
    icon: Gauge,
    path: "/app",
    items: [],
  },
  {
    id: "project",
    title: "Projet",
    icon: Building2,
    items: [
      { label: "Synthese projet", path: "/app/projects", icon: Building2 },
      { label: "DQE & donnees", path: "/app/dqe?tab=import", icon: FileSpreadsheet },
      { label: "Gouvernance qualite", path: "/app/dqe?tab=quality", icon: ShieldAlert },
      { label: "Documents projet", path: "/app/dqe?tab=history", icon: Database, badge: "audit" },
    ],
  },
  {
    id: "scenarios",
    title: "Scenarios",
    icon: GitCompare,
    items: [
      { label: "Simuler", path: "/app/simulation", icon: Play },
      { label: "Comparer", path: "/app/simulation?tab=compare", icon: GitCompare },
      { label: "Historique", path: "/app/simulation?tab=history", icon: Clock3 },
    ],
  },
  {
    id: "procurement",
    title: "Approvisionnement",
    icon: PackageSearch,
    items: [
      { label: "Decisions d'achat", path: "/app/procurement?tab=import", icon: Ship },
      { label: "Import strategique", path: "/app/procurement-intelligence", icon: PackageSearch },
      { label: "Containers & logistique", path: "/app/logistics", icon: Truck },
      { label: "Arbitrages achats", path: "/app/governance-cockpit", icon: ShieldAlert },
    ],
  },
  {
    id: "execution",
    title: "Execution",
    icon: Workflow,
    items: [
      { label: "Chantier & planning", path: "/app/site?tab=planning", icon: Workflow },
      { label: "Budget travaux", path: "/app/analytics?dashboard=capex", icon: BarChart3 },
      { label: "Suivi financier", path: "/app/analytics?dashboard=timeline", icon: Route },
    ],
  },
  {
    id: "pilotage",
    title: "Pilotage",
    icon: BarChart3,
    items: [
      { label: "Analytics", path: "/app/analytics?dashboard=drilldown", icon: LayoutGrid },
      { label: "Cockpit direction", path: "/app/analytics?dashboard=direction", icon: Gauge },
      { label: "Power BI", path: "/app/analytics?dashboard=direction", icon: BarChart3, badge: "BI" },
      { label: "Rapports", path: "/app/analytics?dashboard=timeline", icon: AlertTriangle },
    ],
  },
  {
    id: "other",
    title: "Autre",
    icon: Settings,
    items: [
      { label: "Organisation", path: "/app/projects", icon: Building2 },
      { label: "Utilisateurs", path: "/app/analytics?dashboard=users", icon: Users },
      { label: "Preferences", path: "/app/analytics?dashboard=admin", icon: Settings },
      { label: "Systeme", path: "/app/analytics?dashboard=monitoring", icon: Gauge },
    ],
  },
];
