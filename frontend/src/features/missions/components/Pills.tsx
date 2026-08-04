import type { Status, Result } from "../types";

// eslint-disable-next-line react-refresh/only-export-components
export const STATUS_META: Record<Status, { color: string; bg: string; border: string; label: string }> = {
  Planned: { color: "var(--color-mc-muted)", bg: "color-mix(in srgb, var(--color-mc-muted) 15%, transparent)", border: "color-mix(in srgb, var(--color-mc-muted) 30%, transparent)", label: "PLANNED" },
  Active: { color: "var(--color-status-active)", bg: "color-mix(in srgb, var(--color-status-active) 15%, transparent)", border: "color-mix(in srgb, var(--color-status-active) 30%, transparent)", label: "ACTIVE" },
  Completed: { color: "var(--color-status-mission)", bg: "color-mix(in srgb, var(--color-status-mission) 15%, transparent)", border: "color-mix(in srgb, var(--color-status-mission) 30%, transparent)", label: "COMPLETED" },
  Aborted: { color: "var(--color-status-damaged)", bg: "color-mix(in srgb, var(--color-status-damaged) 15%, transparent)", border: "color-mix(in srgb, var(--color-status-damaged) 30%, transparent)", label: "ABORTED" },
};

const RESULT_META: Record<NonNullable<Result>, { color: string; bg: string; border: string }> = {
  Success: { color: "var(--color-status-active)", bg: "color-mix(in srgb, var(--color-status-active) 15%, transparent)", border: "color-mix(in srgb, var(--color-status-active) 30%, transparent)" },
  Failure: { color: "var(--color-status-damaged)", bg: "color-mix(in srgb, var(--color-status-damaged) 15%, transparent)", border: "color-mix(in srgb, var(--color-status-damaged) 30%, transparent)" },
};

export function StatusPill({ status }: { status: Status }) {
  const m = STATUS_META[status];
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium tracking-widest whitespace-nowrap w-max"
      style={{ color: m.color, background: m.bg, border: `1px solid ${m.border}` }}
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
      style={{ color: m.color, background: m.bg, border: `1px solid ${m.border}` }}
    >
      {result === "Success" ? "✓" : "✗"} {result.toUpperCase()}
    </span>
  );
}
