/* Role codes as returned by `GET /api/accounts/users/me/` (`role_code`). */
export type RoleCode =
  | "ADMIN"
  | "COMMANDER"
  | "DISPATCHER"
  | "OPERATOR"
  | "TECHNICIAN"
  | "VIEWER";

export const ROLE_CODES: RoleCode[] = [
  "ADMIN",
  "COMMANDER",
  "DISPATCHER",
  "OPERATOR",
  "TECHNICIAN",
  "VIEWER",
];

/* Django REST Framework paginated list envelope. */
export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/* ---- Drones ---- */

/* Mirrors `Drone.STATUS_CHOICES` in `drones/models.py`. */
export type DroneStatus =
  | "ACTIVE"
  | "IN_MISSION"
  | "DAMAGED"
  | "LOST"
  | "MAINTENANCE"
  | "DECOMMISSIONED"
  | "SOLD"
  | "TRANSFERRED"
  | "WRITTEN_OFF";

export interface DroneListItem {
  id: number;
  serial_number: string;
  inventory_number: string;
  name: string;
  status: DroneStatus;
  status_label: string;
  status_category: string;
}

/* ---- Missions ---- */

/* Mirrors `missions.models.Status`. */
export type MissionStatus =
  | "planned"
  | "active"
  | "completed"
  | "aborted";

export interface UserBrief {
  id: number;
  username: string;
  first_name?: string;
  last_name?: string;
}

export interface MissionListItem {
  id: number;
  title: string;
  status: MissionStatus;
  location_description: string | null;
  commander: UserBrief | null;
  started_at: string | null;
  created_at: string | null;
}

/* ---- Defects ---- */

export type DefectSeverity =
  | "LOW"
  | "MEDIUM"
  | "HIGH"
  | "CRITICAL";

/* Mirrors `repairs.serializers.DefectReportListSerializer`. The list endpoint
 * exposes `drone` as an id only (no name) and has no `status` field/filter. */
export interface DefectListItem {
  id: number;
  drone: number;
  defect_type: string;
  severity: DefectSeverity;
  detected_at: string;
  reporter: number | null;
  created_at: string;
}

/* ---- Audit log ---- */

export interface AuditLogItem {
  id: number;
  actor: number | null;
  actor_username: string | null;
  target_user: number | null;
  target_user_username: string | null;
  action_type: string;
  result: string;
  description: string;
  created_at: string;
}

/* ---- Health ---- */

export interface HealthResponse {
  status: string;
  dependencies: Record<string, string>;
}

export type HealthState = "operational" | "degraded" | "unknown";

/* ---- Derived view models ---- */

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

/* ---- Per-section async state ----
 *
 * The terminal state of one dashboard section. `restricted` is distinct from
 * `error`: it is the UI's reaction to a backend 403 and is never retryable. */
export type SectionStatus =
  | "loading"
  | "success"
  | "error"
  | "restricted";

export interface SectionState<T> {
  status: SectionStatus;
  data: T | null;
}
