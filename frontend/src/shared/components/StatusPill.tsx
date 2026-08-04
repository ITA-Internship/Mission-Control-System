import type { MissionStatus } from "../types/missions";
import type { DefectSeverity } from "../types/repairs";
import { cn } from "../utils/cn";

interface PillStyle {
  label: string;
  color: string;
}

/* Colors reference the shared CSS tokens in globals.css so the pills stay in
 * sync with the rest of the status palette instead of duplicating hex values. */
const MISSION_STATUS: Record<MissionStatus, PillStyle> = {
  active: { label: "Active", color: "var(--color-status-active)" },
  planned: { label: "Planned", color: "var(--color-status-mission)" },
  completed: { label: "Completed", color: "var(--color-mc-muted)" },
  aborted: { label: "Aborted", color: "var(--color-mc-error)" },
};

const SEVERITY: Record<DefectSeverity, PillStyle> = {
  LOW: { label: "Low", color: "var(--color-mc-muted)" },
  MEDIUM: { label: "Medium", color: "var(--color-status-maintenance)" },
  HIGH: { label: "High", color: "var(--color-severity-high)" },
  CRITICAL: { label: "Critical", color: "var(--color-mc-error)" },
};

function Pill({ label, color }: PillStyle) {
  return (
    <span
      className="inline-flex items-center rounded-full px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wide"
      style={{
        color,
        backgroundColor: `color-mix(in srgb, ${color} 15%, transparent)`,
      }}
    >
      {label}
    </span>
  );
}

export function MissionStatusPill({
  status,
}: {
  status: MissionStatus;
}) {
  const style =
    MISSION_STATUS[status] ?? {
      label: status,
      color: "var(--color-mc-muted)",
    };
  return <Pill {...style} />;
}

export function SeverityPill({
  severity,
}: {
  severity: DefectSeverity;
}) {
  const style =
    SEVERITY[severity] ?? {
      label: severity,
      color: "var(--color-mc-muted)",
    };
  return <Pill {...style} />;
}

/* A small coloured status dot with an optional label — used in breakdowns. */
export function StatusDot({
  color,
  className,
}: {
  color: string;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-block h-1.5 w-1.5 shrink-0 rounded-full",
        className,
      )}
      style={{ background: color }}
    />
  );
}
