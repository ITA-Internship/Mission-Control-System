/* View models derived by the dashboard from several API endpoints. The raw API
 * shapes they build on live in `src/shared/types/`. */

import type { DroneStatus } from "../../../shared/types/drones";
import type { HealthState } from "../../../shared/types/health";

export interface FleetStatusSlice {
  status: DroneStatus;
  label: string;
  count: number;
  color: string;
}

export interface DashboardSummary {
  activeMissions: number;
  fleetTotal: number;
  fleet: FleetStatusSlice[];
  openDefects: number;
  criticalDefects: number;
  highDefects: number;
  inMaintenance: number;
  health: HealthState;
}

/* Identifier for each KPI stat tile. Keeping this a union (rather than a bare
 * string) makes the tile config, the RBAC visibility map and the content
 * switch exhaustive — a typo or a missing role set is a compile error. */
export type KpiTileId =
  | "active-missions"
  | "fleet-total"
  | "open-defects"
  | "maintenance"
  | "system-health";
