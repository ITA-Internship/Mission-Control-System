import type { LucideIcon } from "lucide-react";
import {
  Activity,
  AlertTriangle,
  Plane,
  Target,
  Wrench,
} from "lucide-react";

import { Skeleton } from "../../../shared/components/states";
import type { RoleCode } from "../../../shared/types/accounts";
import type { SectionState } from "../../../shared/types/api";
import type { HealthState } from "../../../shared/types/health";
import { cn } from "../../../shared/utils/cn";
import { KPI_ROLES } from "../rbac";
import type {
  DashboardSummary,
  KpiTileId,
} from "../types/dashboard";

interface TileConfig {
  id: KpiTileId;
  label: string;
  icon: LucideIcon;
  iconColor: string;
  iconBg: string;
}

const TILES: TileConfig[] = [
  {
    id: "active-missions",
    label: "Active Missions",
    icon: Target,
    iconColor: "text-status-mission",
    iconBg: "bg-status-mission/15",
  },
  {
    id: "fleet-total",
    label: "Fleet Drones",
    icon: Plane,
    iconColor: "text-status-active",
    iconBg: "bg-status-active/15",
  },
  {
    id: "open-defects",
    label: "Open Defects",
    icon: AlertTriangle,
    iconColor: "text-mc-error",
    iconBg: "bg-mc-error/15",
  },
  {
    id: "maintenance",
    label: "In Maintenance",
    icon: Wrench,
    iconColor: "text-status-maintenance",
    iconBg: "bg-status-maintenance/15",
  },
  {
    id: "system-health",
    label: "System Health",
    icon: Activity,
    iconColor: "text-status-active",
    iconBg: "bg-status-active/15",
  },
];

const HEALTH_LABEL: Record<HealthState, string> = {
  operational: "Operational",
  degraded: "Degraded",
  unknown: "Unknown",
};

function TileShell({
  config,
  alert,
  children,
}: {
  config: TileConfig;
  alert?: boolean;
  children: React.ReactNode;
}) {
  const Icon = config.icon;
  return (
    <div
      className={cn(
        "flex min-w-0 flex-col gap-1 overflow-hidden rounded-xl border bg-mc-card p-4 transition-colors",
        alert ? "border-mc-error/30" : "border-mc-border",
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="min-w-0 truncate text-[11px] font-medium uppercase leading-tight tracking-wider text-mc-muted">
          {config.label}
        </p>
        <div
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
            config.iconBg,
          )}
        >
          <Icon className={cn("h-4 w-4", config.iconColor)} />
        </div>
      </div>
      {children}
    </div>
  );
}

function BreakdownDot({
  color,
  label,
  value,
}: {
  color: string;
  label: string;
  value: number;
}) {
  return (
    <span className="flex items-center gap-1 font-mono text-[10px]">
      <span
        className="inline-block h-1.5 w-1.5 rounded-full"
        style={{ background: color }}
      />
      <span className="text-mc-muted">{label}</span>
      <span className="ml-0.5 font-semibold text-mc-text">
        {value}
      </span>
    </span>
  );
}

function TileValue({
  value,
  alert,
}: {
  value: number | string;
  alert?: boolean;
}) {
  return (
    <span
      className={cn(
        "font-mono font-semibold leading-none",
        alert ? "text-mc-error" : "text-mc-text",
      )}
      style={{ fontSize: "32px" }}
    >
      {value}
    </span>
  );
}

function SkeletonTile() {
  return (
    <div className="space-y-3 rounded-xl border border-mc-border bg-mc-card p-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-8 w-8 rounded-lg" />
      </div>
      <Skeleton className="h-8 w-16" />
      <Skeleton className="h-2.5 w-32" />
    </div>
  );
}

function tileContent(
  id: KpiTileId,
  summary: DashboardSummary,
): React.ReactNode {
  switch (id) {
    case "active-missions":
      return <TileValue value={summary.activeMissions} />;
    case "fleet-total":
      return (
        <>
          <TileValue value={summary.fleetTotal} />
          <div className="mt-1.5 flex flex-wrap items-center gap-2">
            {summary.fleet
              .filter((slice) =>
                ["ACTIVE", "IN_MISSION", "MAINTENANCE", "DAMAGED"].includes(
                  slice.status,
                ),
              )
              .map((slice) => (
                <BreakdownDot
                  key={slice.status}
                  color={slice.color}
                  label={slice.label}
                  value={slice.count}
                />
              ))}
          </div>
        </>
      );
    case "open-defects":
      return (
        <>
          <TileValue
            value={summary.openDefects}
            alert={summary.criticalDefects > 0}
          />
          <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[10px]">
            <span className="text-mc-muted">Critical</span>
            <span className="font-semibold text-mc-error">
              {summary.criticalDefects}
            </span>
            <span className="text-mc-muted">·</span>
            <span className="text-mc-muted">High</span>
            <span className="font-semibold text-severity-high">
              {summary.highDefects}
            </span>
          </div>
        </>
      );
    case "maintenance":
      return <TileValue value={summary.inMaintenance} />;
    case "system-health": {
      const operational = summary.health === "operational";
      return (
        <div className="mt-0.5">
          <span
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full px-2 py-1 font-mono text-[11px] font-semibold uppercase tracking-wide",
              operational
                ? "bg-status-active/15 text-status-active"
                : "bg-mc-error/15 text-mc-error",
            )}
          >
            <span
              className={cn(
                "h-1.5 w-1.5 rounded-full",
                operational ? "bg-status-active" : "bg-mc-error",
              )}
            />
            {HEALTH_LABEL[summary.health]}
          </span>
          <p className="mt-1 font-mono text-[10px] text-mc-muted">
            GET /api/health/
          </p>
        </div>
      );
    }
    default:
      return null;
  }
}

interface KpiTilesProps {
  role: RoleCode;
  summary: SectionState<DashboardSummary>;
}

export function KpiTiles({ role, summary }: KpiTilesProps) {
  const visible = TILES.filter((tile) =>
    KPI_ROLES[tile.id]?.has(role),
  );

  if (visible.length === 0) return null;

  const gridClass =
    "grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5";

  if (summary.status === "loading") {
    return (
      <div className={gridClass}>
        {visible.map((tile) => (
          <SkeletonTile key={tile.id} />
        ))}
      </div>
    );
  }

  const data = summary.data;

  // The Open Defects tile only escalates to its red "alert" treatment when
  // there is actually a critical defect — a permanently-red KPI trains
  // operators to ignore it.
  const defectsAlert = !!data && data.criticalDefects > 0;

  return (
    <div className={gridClass}>
      {visible.map((tile) => (
        <TileShell
          key={tile.id}
          config={tile}
          alert={tile.id === "open-defects" && defectsAlert}
        >
          {data ? (
            tileContent(tile.id, data)
          ) : (
            <TileValue value="—" />
          )}
        </TileShell>
      ))}
    </div>
  );
}
