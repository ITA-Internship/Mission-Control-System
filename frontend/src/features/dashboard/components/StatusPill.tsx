import { cn } from "../../../shared/utils/cn";
import type {
  DefectSeverity,
  MissionStatus,
} from "../types/dashboard";

interface PillStyle {
  label: string;
  color: string;
}

const MISSION_STATUS: Record<MissionStatus, PillStyle> = {
  active: { label: "Active", color: "#3FB950" },
  planned: { label: "Planned", color: "#4C8DFF" },
  completed: { label: "Completed", color: "#8A94A6" },
  aborted: { label: "Aborted", color: "#E5484D" },
};

const SEVERITY: Record<DefectSeverity, PillStyle> = {
  LOW: { label: "Low", color: "#8A94A6" },
  MEDIUM: { label: "Medium", color: "#C8A24A" },
  HIGH: { label: "High", color: "#F0883E" },
  CRITICAL: { label: "Critical", color: "#E5484D" },
};

function Pill({ label, color }: PillStyle) {
  return (
    <span
      className="inline-flex items-center rounded-full px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wide"
      style={{
        color,
        backgroundColor: `${color}26`,
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
      color: "#8A94A6",
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
      color: "#8A94A6",
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
