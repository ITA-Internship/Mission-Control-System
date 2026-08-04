import type { DroneStatus } from "../types";
import { STATUS_UI } from "../utils/constants";

interface StatusBadgeProps {
  status: DroneStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const s = STATUS_UI[status] || STATUS_UI["LOST"];

  return (
    <span className={`inline-flex items-center gap-1.5 text-[11px] font-medium ${s.color}`}>
      <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${s.dot}`} />
      {s.label}
    </span>
  );
}