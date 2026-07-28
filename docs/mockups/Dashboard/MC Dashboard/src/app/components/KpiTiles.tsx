import { cn } from "./ui/utils";
import { Target, Plane, AlertTriangle, Wrench, Activity, TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { Role } from "../types";

type TrendDir = "up" | "down" | "flat";

interface KpiTile {
  id: string;
  label: string;
  value: string | number;
  subtext?: string;
  trend?: { value: string; dir: TrendDir };
  alert?: boolean;
  icon: React.ComponentType<{ className?: string }>;
  iconColor: string;
  iconBg: string;
  allowedRoles: Role[];
  extra?: React.ReactNode;
}

const DRONE_BREAKDOWN = (
  <div className="flex items-center gap-2 mt-1.5 flex-wrap">
    <span className="flex items-center gap-1 font-mono text-[10px]">
      <span className="w-1.5 h-1.5 rounded-full bg-[#3FB950] inline-block" />
      <span className="text-[#8A94A6]">Active</span>
      <span className="text-[#E6EAF0] font-semibold ml-0.5">18</span>
    </span>
    <span className="flex items-center gap-1 font-mono text-[10px]">
      <span className="w-1.5 h-1.5 rounded-full bg-[#4C8DFF] inline-block" />
      <span className="text-[#8A94A6]">Mission</span>
      <span className="text-[#E6EAF0] font-semibold ml-0.5">7</span>
    </span>
    <span className="flex items-center gap-1 font-mono text-[10px]">
      <span className="w-1.5 h-1.5 rounded-full bg-[#C8A24A] inline-block" />
      <span className="text-[#8A94A6]">Maint.</span>
      <span className="text-[#E6EAF0] font-semibold ml-0.5">5</span>
    </span>
    <span className="flex items-center gap-1 font-mono text-[10px]">
      <span className="w-1.5 h-1.5 rounded-full bg-[#E5484D] inline-block" />
      <span className="text-[#8A94A6]">Dmg.</span>
      <span className="text-[#E6EAF0] font-semibold ml-0.5">3</span>
    </span>
  </div>
);

const DEFECTS_EXTRA = (
  <div className="flex items-center gap-2 mt-1.5">
    <span className="flex items-center gap-1 font-mono text-[10px]">
      <span className="text-[#8A94A6]">Critical</span>
      <span className="text-[#E5484D] font-semibold ml-0.5">4</span>
    </span>
    <span className="text-[#8A94A6] font-mono text-[10px]">·</span>
    <span className="flex items-center gap-1 font-mono text-[10px]">
      <span className="text-[#8A94A6]">High</span>
      <span className="text-[#F0883E] font-semibold ml-0.5">7</span>
    </span>
  </div>
);

const KPI_TILES: KpiTile[] = [
  {
    id: "active-missions",
    label: "Active Missions",
    value: 7,
    trend: { value: "+2 from yesterday", dir: "up" },
    icon: Target,
    iconColor: "text-[#4C8DFF]",
    iconBg: "bg-[#4C8DFF]/15",
    allowedRoles: ["Admin","Commander","Dispatcher","Operator","Viewer"],
  },
  {
    id: "fleet-total",
    label: "Fleet Drones",
    value: 34,
    subtext: "Total registered",
    icon: Plane,
    iconColor: "text-[#3FB950]",
    iconBg: "bg-[#3FB950]/15",
    allowedRoles: ["Admin","Commander","Dispatcher","Technician","Viewer"],
    extra: DRONE_BREAKDOWN,
  },
  {
    id: "open-defects",
    label: "Open Defects",
    value: 17,
    trend: { value: "+3 this week", dir: "up" },
    alert: true,
    icon: AlertTriangle,
    iconColor: "text-[#E5484D]",
    iconBg: "bg-[#E5484D]/15",
    allowedRoles: ["Admin","Commander","Technician"],
    extra: DEFECTS_EXTRA,
  },
  {
    id: "maintenance",
    label: "In Maintenance",
    value: 5,
    trend: { value: "-1 from last week", dir: "down" },
    icon: Wrench,
    iconColor: "text-[#C8A24A]",
    iconBg: "bg-[#C8A24A]/15",
    allowedRoles: ["Admin","Commander","Technician"],
  },
  {
    id: "system-health",
    label: "System Health",
    value: "Operational",
    subtext: "GET /api/health/",
    icon: Activity,
    iconColor: "text-[#3FB950]",
    iconBg: "bg-[#3FB950]/15",
    allowedRoles: ["Admin","Commander"],
  },
];

const TREND_ICONS: Record<TrendDir, React.ComponentType<{ className?: string }>> = {
  up: TrendingUp,
  down: TrendingDown,
  flat: Minus,
};

function SkeletonTile() {
  return (
    <div className="rounded-xl border border-border p-4 space-y-3 animate-pulse" style={{ background: "var(--card)" }}>
      <div className="flex items-center justify-between">
        <div className="h-3 w-24 bg-white/10 rounded" />
        <div className="w-8 h-8 rounded-lg bg-white/10" />
      </div>
      <div className="h-8 w-16 bg-white/10 rounded" />
      <div className="h-2.5 w-32 bg-white/10 rounded" />
    </div>
  );
}

interface KpiTilesProps {
  role: Role;
  loading?: boolean;
}

export function KpiTiles({ role, loading = false }: KpiTilesProps) {
  const visible = KPI_TILES.filter(t => t.allowedRoles.includes(role));

  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {[...Array(5)].map((_, i) => <SkeletonTile key={i} />)}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {visible.map((tile) => {
        const Icon = tile.icon;
        const isAlertTile = tile.id === "system-health" && tile.value === "Operational";
        const isDegraded = tile.id === "system-health" && tile.value !== "Operational";
        const TrendIcon = tile.trend ? TREND_ICONS[tile.trend.dir] : null;

        return (
          <div
            key={tile.id}
            className={cn(
              "rounded-xl border p-4 flex flex-col gap-1 transition-all duration-150 hover:border-white/15 group",
              tile.alert ? "border-[#E5484D]/30" : "border-border",
            )}
            style={{ background: "var(--card)" }}
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-[11px] font-medium text-[#8A94A6] uppercase tracking-wider leading-tight">{tile.label}</p>
              <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center shrink-0", tile.iconBg)}>
                <Icon className={cn("w-4 h-4", tile.iconColor)} />
              </div>
            </div>

            <div className="mt-0.5">
              {tile.id === "system-health" ? (
                <div className="flex items-center gap-2">
                  <span className={cn(
                    "inline-flex items-center gap-1.5 px-2 py-1 rounded-full font-mono text-[11px] font-semibold uppercase tracking-wide",
                    isAlertTile ? "bg-[#3FB950]/15 text-[#3FB950]" : "bg-[#E5484D]/15 text-[#E5484D]"
                  )}>
                    <span className={cn("w-1.5 h-1.5 rounded-full", isAlertTile ? "bg-[#3FB950]" : "bg-[#E5484D]")} />
                    {tile.value}
                  </span>
                </div>
              ) : (
                <span className={cn(
                  "font-mono font-semibold leading-none",
                  tile.alert ? "text-[#E5484D]" : "text-[#E6EAF0]",
                )}
                style={{ fontSize: "32px" }}>
                  {tile.value}
                </span>
              )}
            </div>

            {tile.extra && tile.extra}

            {tile.subtext && !tile.extra && (
              <p className="font-mono text-[10px] text-[#8A94A6] mt-0.5">{tile.subtext}</p>
            )}

            {tile.trend && TrendIcon && (
              <div className={cn(
                "flex items-center gap-1 mt-auto pt-1",
                tile.trend.dir === "up" && tile.alert ? "text-[#E5484D]" :
                tile.trend.dir === "up" ? "text-[#3FB950]" :
                tile.trend.dir === "down" ? "text-[#8A94A6]" :
                "text-[#8A94A6]"
              )}>
                <TrendIcon className="w-3 h-3" />
                <span className="font-mono text-[10px]">{tile.trend.value}</span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
