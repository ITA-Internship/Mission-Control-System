import { useEffect, useState } from "react";

import {
  ApiError,
  isAbortError,
} from "../../../shared/api/apiClient";
import {
  fetchActiveMissionsCount,
  fetchAuditFeed,
  fetchDefectsCount,
  fetchFleetBreakdown,
  fetchHealth,
  fetchInMaintenanceCount,
  fetchOpenDefects,
  fetchRecentMissions,
} from "../api/dashboardApi";
import {
  CAN_SEE_AUDIT,
  CAN_SEE_DEFECTS,
  CAN_SEE_FLEET_CHART,
  CAN_SEE_MISSIONS,
  KPI_ROLES,
} from "../rbac";
import type {
  AuditLogItem,
  DashboardSummary,
  DefectListItem,
  HealthState,
  MissionListItem,
  RoleCode,
  SectionState,
} from "../types/dashboard";

const loading = <T,>(): SectionState<T> => ({
  status: "loading",
  data: null,
});
const restricted = <T,>(): SectionState<T> => ({
  status: "restricted",
  data: null,
});

export interface DashboardData {
  summary: SectionState<DashboardSummary>;
  missions: SectionState<MissionListItem[]>;
  defects: SectionState<DefectListItem[]>;
  audit: SectionState<AuditLogItem[]>;
}

/* Run a request, but swallow non-abort failures into a fallback so one broken
 * endpoint never takes down the whole KPI summary. Abort must propagate. */
function guard<T>(promise: Promise<T>, fallback: T): Promise<T> {
  return promise.catch((error) => {
    if (isAbortError(error)) {
      throw error;
    }
    return fallback;
  });
}

async function loadSummary(
  role: RoleCode,
  signal: AbortSignal,
): Promise<DashboardSummary> {
  const canMissions = KPI_ROLES["active-missions"].has(role);
  const canFleet =
    KPI_ROLES["fleet-total"].has(role) ||
    CAN_SEE_FLEET_CHART.has(role);
  const canDefects = KPI_ROLES["open-defects"].has(role);
  const canMaint = KPI_ROLES["maintenance"].has(role);
  const canHealth = KPI_ROLES["system-health"].has(role);

  const [
    activeMissions,
    fleet,
    openDefects,
    criticalDefects,
    highDefects,
    inMaintenance,
    health,
  ] = await Promise.all([
    canMissions
      ? guard(fetchActiveMissionsCount(signal), 0)
      : Promise.resolve(0),
    canFleet
      ? guard(fetchFleetBreakdown(signal), [])
      : Promise.resolve([]),
    canDefects
      ? guard(fetchDefectsCount(null, signal), 0)
      : Promise.resolve(0),
    canDefects
      ? guard(fetchDefectsCount("CRITICAL", signal), 0)
      : Promise.resolve(0),
    canDefects
      ? guard(fetchDefectsCount("HIGH", signal), 0)
      : Promise.resolve(0),
    canMaint
      ? guard(fetchInMaintenanceCount(signal), 0)
      : Promise.resolve(0),
    canHealth
      ? guard(fetchHealth(signal), "unknown" as HealthState)
      : Promise.resolve("unknown" as HealthState),
  ]);

  return {
    activeMissions,
    fleet,
    fleetTotal: fleet.reduce((sum, slice) => sum + slice.count, 0),
    openDefects,
    criticalDefects,
    highDefects,
    inMaintenance,
    health,
  };
}

/* Map a rejected request to the right terminal section state: a backend 403
 * becomes "restricted"; anything else (including a network failure) is an
 * error the panel can retry from. Abort is silently ignored by the caller. */
function toErrorState<T>(error: unknown): SectionState<T> {
  if (error instanceof ApiError && error.status === 403) {
    return restricted<T>();
  }
  return { status: "error", data: null };
}

const initialSection = <T,>(visible: boolean): SectionState<T> =>
  visible ? loading<T>() : restricted<T>();

/*
 * Loads all dashboard sections in parallel, gated by the caller's role.
 *
 * `role` is fixed for the lifetime of a session (there is no in-app role
 * switch — re-authentication remounts the shell), so each section's initial
 * state is derived once via a `useState` initializer and the effect only ever
 * calls `setState` from async callbacks. This keeps the effect free of the
 * synchronous cascading-render pattern.
 */
export function useDashboardData(
  role: RoleCode | null,
): DashboardData {
  const [summary, setSummary] = useState<
    SectionState<DashboardSummary>
  >(() => initialSection(role !== null));
  const [missions, setMissions] = useState<
    SectionState<MissionListItem[]>
  >(() => initialSection(role !== null && CAN_SEE_MISSIONS.has(role)));
  const [defects, setDefects] = useState<
    SectionState<DefectListItem[]>
  >(() => initialSection(role !== null && CAN_SEE_DEFECTS.has(role)));
  const [audit, setAudit] = useState<
    SectionState<AuditLogItem[]>
  >(() => initialSection(role !== null && CAN_SEE_AUDIT.has(role)));

  useEffect(() => {
    if (!role) return;

    const controller = new AbortController();
    const { signal } = controller;

    loadSummary(role, signal)
      .then((data) => setSummary({ status: "success", data }))
      .catch((error) => {
        if (isAbortError(error)) return;
        setSummary(toErrorState(error));
      });

    if (CAN_SEE_MISSIONS.has(role)) {
      fetchRecentMissions(signal)
        .then((data) => setMissions({ status: "success", data }))
        .catch((error) => {
          if (isAbortError(error)) return;
          setMissions(toErrorState(error));
        });
    }

    if (CAN_SEE_DEFECTS.has(role)) {
      fetchOpenDefects(signal)
        .then((data) => setDefects({ status: "success", data }))
        .catch((error) => {
          if (isAbortError(error)) return;
          setDefects(toErrorState(error));
        });
    }

    if (CAN_SEE_AUDIT.has(role)) {
      fetchAuditFeed(signal)
        .then((data) => setAudit({ status: "success", data }))
        .catch((error) => {
          if (isAbortError(error)) return;
          setAudit(toErrorState(error));
        });
    }

    return () => controller.abort();
  }, [role]);

  return { summary, missions, defects, audit };
}
