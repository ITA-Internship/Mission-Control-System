import {
  ApiError,
  apiRequest,
  isAbortError,
} from "../../../shared/api/apiClient";
import type { AuditLogItem } from "../../../shared/types/accounts";
import type { Paginated } from "../../../shared/types/api";
import type { DroneStatus } from "../../../shared/types/drones";
import type {
  HealthResponse,
  HealthState,
} from "../../../shared/types/health";
import type { MissionListItem } from "../../../shared/types/missions";
import type { DefectListItem } from "../../../shared/types/repairs";
import type { FleetStatusSlice } from "../types/dashboard";

/* Drone statuses shown in the fleet breakdown, with their display metadata.
 * Colors reference the CSS tokens added in globals.css (see dashboard.md). */
export const FLEET_STATUS_META: {
  status: DroneStatus;
  label: string;
  color: string;
}[] = [
  { status: "ACTIVE", label: "Active", color: "var(--color-status-active)" },
  { status: "IN_MISSION", label: "In Mission", color: "var(--color-status-mission)" },
  { status: "MAINTENANCE", label: "Maintenance", color: "var(--color-status-maintenance)" },
  { status: "DAMAGED", label: "Damaged", color: "var(--color-status-damaged)" },
  { status: "LOST", label: "Lost", color: "var(--color-status-lost)" },
  { status: "DECOMMISSIONED", label: "Decommissioned", color: "var(--color-status-decommissioned)" },
];

/* Read the `count` of a paginated endpoint without transferring the rows. */
async function fetchCount(
  path: string,
  params: Record<string, string>,
  signal?: AbortSignal,
): Promise<number> {
  const query = new URLSearchParams({
    ...params,
    page_size: "1",
  }).toString();

  const data = await apiRequest<Paginated<unknown>>(
    `${path}?${query}`,
    { signal },
  );

  return data.count;
}

export function fetchActiveMissionsCount(
  signal?: AbortSignal,
): Promise<number> {
  return fetchCount("/api/missions/", { status: "active" }, signal);
}

export function fetchDroneStatusCount(
  status: DroneStatus,
  signal?: AbortSignal,
): Promise<number> {
  return fetchCount("/api/drones/", { status }, signal);
}

export async function fetchFleetBreakdown(
  signal?: AbortSignal,
): Promise<FleetStatusSlice[]> {
  const counts = await Promise.all(
    FLEET_STATUS_META.map((meta) =>
      /* Degrade a single failed status count to 0 rather than letting
       * Promise.all reject and blank the entire breakdown — one bad request
       * should cost one slice, not the whole panel. Abort still propagates so
       * the caller can cancel cleanly. */
      fetchDroneStatusCount(meta.status, signal).catch((error) => {
        if (isAbortError(error)) {
          throw error;
        }
        return 0;
      }),
    ),
  );

  return FLEET_STATUS_META.map((meta, index) => ({
    ...meta,
    count: counts[index],
  }));
}

/* A defect is "open" until it has been fixed and verified; FIXED/VERIFIED are
 * resolved. The dashboard's Open Defects tile and panel count/show only these
 * states, sent as a comma-separated `status__in` filter. */
export const OPEN_DEFECT_STATUSES = "REPORTED,IN_PROGRESS";

export function fetchDefectsCount(
  severity: "CRITICAL" | "HIGH" | null,
  signal?: AbortSignal,
): Promise<number> {
  const params: Record<string, string> = {
    status__in: OPEN_DEFECT_STATUSES,
  };
  if (severity) {
    params.severity = severity;
  }
  return fetchCount("/api/repairs/defects/", params, signal);
}

export function fetchInMaintenanceCount(
  signal?: AbortSignal,
): Promise<number> {
  return fetchDroneStatusCount("MAINTENANCE", signal);
}

/* Health returns 200 when healthy and 503 when a dependency is down; both
 * carry a JSON body. Map either into a UI state, and network failure to
 * "unknown" rather than throwing. */
export async function fetchHealth(
  signal?: AbortSignal,
): Promise<HealthState> {
  try {
    const data = await apiRequest<HealthResponse>(
      "/api/health/",
      { signal },
    );
    return data.status === "healthy" ? "operational" : "degraded";
  } catch (error) {
    if (error instanceof ApiError) {
      const body = error.body as Partial<HealthResponse> | null;
      return body?.status === "healthy" ? "operational" : "degraded";
    }
    throw error;
  }
}

export async function fetchRecentMissions(
  signal?: AbortSignal,
  pageSize = 6,
): Promise<MissionListItem[]> {
  const data = await apiRequest<Paginated<MissionListItem>>(
    `/api/missions/?page_size=${pageSize}`,
    { signal },
  );
  return data.results;
}

export async function fetchOpenDefects(
  signal?: AbortSignal,
  pageSize = 6,
): Promise<DefectListItem[]> {
  const query = new URLSearchParams({
    page_size: String(pageSize),
    ordering: "-created_at",
    status__in: OPEN_DEFECT_STATUSES,
  }).toString();
  const data = await apiRequest<Paginated<DefectListItem>>(
    `/api/repairs/defects/?${query}`,
    { signal },
  );
  return data.results;
}

export async function fetchAuditFeed(
  signal?: AbortSignal,
  pageSize = 8,
): Promise<AuditLogItem[]> {
  const data = await apiRequest<Paginated<AuditLogItem>>(
    `/api/accounts/audit-log/?page_size=${pageSize}`,
    { signal },
  );
  return data.results;
}
