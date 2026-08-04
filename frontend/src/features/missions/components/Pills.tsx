import type { Status, Result } from "../types";

// eslint-disable-next-line react-refresh/only-export-components
export const STATUS_META: Record<Status, { color: string; bg: string; label: string }> = {
  Planned: { color: "#8A94A6", bg: "rgba(138,148,166,0.15)", label: "PLANNED" },
  Active: { color: "#3FB950", bg: "rgba(63,185,80,0.15)", label: "ACTIVE" },
  Completed: { color: "#4C8DFF", bg: "rgba(76,141,255,0.15)", label: "COMPLETED" },
  Aborted: { color: "#E5484D", bg: "rgba(229,72,77,0.15)", label: "ABORTED" },
};

const RESULT_META: Record<NonNullable<Result>, { color: string; bg: string }> = {
  Success: { color: "#3FB950", bg: "rgba(63,185,80,0.15)" },
  Failure: { color: "#E5484D", bg: "rgba(229,72,77,0.15)" },
};

export function StatusPill({ status }: { status: Status }) {
  const m = STATUS_META[status];
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium tracking-widest whitespace-nowrap w-max"
      style={{ color: m.color, background: m.bg, border: `1px solid ${m.color}30` }}
    >
      <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ background: m.color }} />
      {m.label}
    </span>
  );
}

export function ResultPill({ result }: { result: Result }) {
  if (!result) return <span className="text-[#8A94A6] text-[11px] font-mono">—</span>;
  const m = RESULT_META[result];
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium tracking-widest whitespace-nowrap w-max"
      style={{ color: m.color, background: m.bg, border: `1px solid ${m.color}30` }}
    >
      {result === "Success" ? "✓" : "✗"} {result.toUpperCase()}
    </span>
  );
}
