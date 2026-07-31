import type {
  LucideIcon,
} from "lucide-react";
import {
  LayoutDashboard,
  Plane,
  Target,
  Wrench,
  Image,
  ShieldCheck,
} from "lucide-react";

import type { RoleCode } from "./types/dashboard";

/*
 * Frontend RBAC visibility matrix.
 *
 * This is a UX convenience mirroring the design brief so nav items and panels
 * only render for roles that can use them. It is NOT a security boundary — the
 * Django backend enforces real permissions (`accounts/rbac.py`) and returns 403
 * for unauthorized access, which the data layer degrades to a "restricted"
 * panel. Keep this aligned with `docs/rbac.md` where practical.
 */

export interface NavItem {
  id: string;
  label: string;
  path: string;
  icon: LucideIcon;
  allowedRoles: RoleCode[];
}

const ALL: RoleCode[] = [
  "ADMIN",
  "COMMANDER",
  "DISPATCHER",
  "OPERATOR",
  "TECHNICIAN",
  "VIEWER",
];

export const NAV_ITEMS: NavItem[] = [
  {
    id: "dashboard",
    label: "Dashboard",
    path: "/dashboard",
    icon: LayoutDashboard,
    allowedRoles: ALL,
  },
  {
    id: "drones",
    label: "Drones",
    path: "/drones",
    icon: Plane,
    allowedRoles: [
      "ADMIN",
      "COMMANDER",
      "DISPATCHER",
      "OPERATOR",
      "TECHNICIAN",
      "VIEWER",
    ],
  },
  {
    id: "missions",
    label: "Missions",
    path: "/missions",
    icon: Target,
    allowedRoles: [
      "ADMIN",
      "COMMANDER",
      "DISPATCHER",
      "OPERATOR",
      "VIEWER",
    ],
  },
  {
    id: "repairs",
    label: "Repairs",
    path: "/repairs",
    icon: Wrench,
    allowedRoles: ["ADMIN", "COMMANDER", "TECHNICIAN"],
  },
  {
    id: "media",
    label: "Media",
    path: "/media",
    icon: Image,
    allowedRoles: [
      "ADMIN",
      "COMMANDER",
      "DISPATCHER",
      "OPERATOR",
      "VIEWER",
    ],
  },
  {
    id: "administration",
    label: "Administration",
    path: "/administration",
    icon: ShieldCheck,
    allowedRoles: ["ADMIN"],
  },
];

/* Dashboard panel/KPI visibility sets. */
export const CAN_SEE_FLEET_CHART = new Set<RoleCode>([
  "ADMIN",
  "COMMANDER",
  "DISPATCHER",
  "TECHNICIAN",
  "VIEWER",
]);
export const CAN_SEE_MISSIONS = new Set<RoleCode>([
  "ADMIN",
  "COMMANDER",
  "DISPATCHER",
  "OPERATOR",
  "VIEWER",
]);
export const CAN_SEE_DEFECTS = new Set<RoleCode>([
  "ADMIN",
  "COMMANDER",
  "TECHNICIAN",
]);
export const CAN_SEE_AUDIT = new Set<RoleCode>([
  "ADMIN",
  "COMMANDER",
]);

/* KPI tile visibility, keyed by tile id. */
export const KPI_ROLES: Record<string, Set<RoleCode>> = {
  "active-missions": new Set([
    "ADMIN",
    "COMMANDER",
    "DISPATCHER",
    "OPERATOR",
    "VIEWER",
  ]),
  "fleet-total": new Set([
    "ADMIN",
    "COMMANDER",
    "DISPATCHER",
    "TECHNICIAN",
    "VIEWER",
  ]),
  "open-defects": new Set([
    "ADMIN",
    "COMMANDER",
    "TECHNICIAN",
  ]),
  maintenance: new Set([
    "ADMIN",
    "COMMANDER",
    "TECHNICIAN",
  ]),
  "system-health": new Set(["ADMIN", "COMMANDER"]),
};

export function visibleNavItems(role: RoleCode | null): NavItem[] {
  if (!role) {
    return NAV_ITEMS.filter((item) => item.id === "dashboard");
  }
  return NAV_ITEMS.filter((item) =>
    item.allowedRoles.includes(role),
  );
}
