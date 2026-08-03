import {
  Activity,
  Cpu,
  House,
  Map,
  ScrollText,
  Settings,
  Shield,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface NavItem {
  label: string;
  icon: LucideIcon;
  /** Route path — omitted while the page is not implemented yet. */
  to?: string;
}

export const NAV_ITEMS: NavItem[] = [
  {
    label: "Dashboard",
    icon: House,
  },
  {
    label: "Mission Map",
    icon: Map,
  },
  {
    label: "Fleet Status",
    icon: Activity,
  },
  {
    label: "Drone Control",
    icon: Cpu,
  },
  {
    label: "Mission Logs",
    icon: ScrollText,
  },
  {
    label: "Administration",
    icon: Shield,
    to: "/administration",
  },
  {
    label: "Settings",
    icon: Settings,
  },
];
