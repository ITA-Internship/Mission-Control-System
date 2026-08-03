import type { RoleCode } from "../../shared/types/accounts";
import type { KpiTileId } from "./types/dashboard";

/*
 * Dashboard panel and KPI visibility by role.
 *
 * Like the shared nav matrix in `shared/layout/navigation.ts`, this is a UX
 * convenience only — the Django backend enforces real permissions
 * (`accounts/rbac.py`) and returns 403 for unauthorized access, which the data
 * layer degrades to a "restricted" panel. Keep this aligned with
 * `docs/rbac.md` where practical.
 */

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
export const KPI_ROLES: Record<KpiTileId, Set<RoleCode>> = {
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
