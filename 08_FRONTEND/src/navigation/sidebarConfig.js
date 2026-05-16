import {
  BarChart3,
  Building2,
  CircleDollarSign,
  Database,
  Factory,
  FileSpreadsheet,
  GitCompare,
  Home,
  PackageSearch,
  Route,
  Settings,
  Ship,
  Truck,
} from "lucide-react";

export const sidebarSections = [
  {
    title: "Cockpit",
    items: [{ label: "Cockpit", path: "/app", icon: Home }],
  },
  {
    title: "Investissements & CAPEX",
    items: [
      { label: "Simulation", path: "/app/simulation", icon: CircleDollarSign },
      { label: "Scenarios", path: "/app/simulation?tab=scenarios", icon: GitCompare },
      { label: "Historique", path: "/app/simulation?tab=history", icon: Database },
      { label: "Comparaison", path: "/app/simulation?tab=compare", icon: BarChart3 },
    ],
  },
  {
    title: "Pilotage Projet",
    items: [
      { label: "Planning", path: "/app/site?tab=planning", icon: Building2 },
      { label: "Dependances", path: "/app/site?tab=dependencies", icon: Route },
      { label: "Livraisons", path: "/app/site?tab=deliveries", icon: Truck },
      { label: "Criticite", path: "/app/site?tab=criticality", icon: BarChart3 },
    ],
  },
  {
    title: "DQE & Data",
    items: [
      { label: "Import Excel", path: "/app/dqe?tab=import", icon: FileSpreadsheet },
      { label: "Analyse DQE", path: "/app/dqe?tab=analysis", icon: Database },
      { label: "Normalisation", path: "/app/dqe?tab=mapping", icon: GitCompare },
      { label: "Qualite donnees", path: "/app/dqe?tab=quality", icon: BarChart3 },
    ],
  },
  {
    title: "Procurement & Supply Chain",
    items: [
      { label: "Fournisseurs", path: "/app/procurement?tab=suppliers", icon: PackageSearch },
      { label: "Import", path: "/app/procurement?tab=import", icon: Factory },
      { label: "Cashflow", path: "/app/procurement?tab=cashflow", icon: CircleDollarSign },
      { label: "Containers", path: "/app/logistics?tab=containers", icon: Ship },
      { label: "Shipments", path: "/app/logistics?tab=shipments", icon: Route },
      { label: "Freight", path: "/app/logistics?tab=freight", icon: Truck },
    ],
  },
  {
    title: "Analytics",
    items: [
      { label: "Direction", path: "/app/analytics?dashboard=direction", icon: BarChart3 },
      { label: "CAPEX", path: "/app/analytics?dashboard=capex", icon: CircleDollarSign },
      { label: "Projet", path: "/app/analytics?dashboard=site", icon: Building2 },
      { label: "Procurement", path: "/app/analytics?dashboard=procurement", icon: PackageSearch },
      { label: "Risques", path: "/app/analytics?dashboard=risks", icon: Database },
    ],
  },
  {
    title: "Administration",
    items: [
      { label: "Parametres", path: "/app/analytics?dashboard=admin", icon: Settings },
    ],
  },
];
