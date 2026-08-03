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

import type { RoleCode } from "../types/accounts";

/*
 * Primary navigation for the app shell, with per-role visibility.
 *
 * The role filter is a UX convenience mirroring the design brief so nav items
 * only render for roles that can use them. It is NOT a security boundary — the
 * Django backend enforces real permissions (`accounts/rbac.py`) and returns 403
 * for unauthorized access. Keep this aligned with `docs/rbac.md` where
 * practical. Feature-local visibility rules (panels, tiles) live with their
 * feature, e.g. `features/dashboard/rbac.ts`.
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

export function visibleNavItems(role: RoleCode | null): NavItem[] {
  if (!role) {
    return NAV_ITEMS.filter((item) => item.id === "dashboard");
  }
  return NAV_ITEMS.filter((item) =>
    item.allowedRoles.includes(role),
  );
}

/* Label of the nav entry owning `pathname`, for the shell page title. */
export function navTitleFor(pathname: string): string {
  const match = NAV_ITEMS.find((item) =>
    pathname.startsWith(item.path),
  );
  return match?.label ?? "Mission Control";
}
