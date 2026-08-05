import type { DroneStatus } from "../types";
import { STATUS_UI } from "../utils/constants";
import { StatusDot } from "../../../shared/components/StatusPill";

interface StatusBadgeProps {
  status: DroneStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const s = STATUS_UI[status] || STATUS_UI["LOST"];

  const hexMatch = s.color.match(/\[(.*?)\]/);
  const hexColor = hexMatch ? hexMatch[1] : "currentColor";

  return (
    <span className={`inline-flex items-center gap-1.5 text-[11px] font-medium ${s.color}`}>
      <StatusDot color={hexColor} />
      {s.label}
    </span>
  );
}
