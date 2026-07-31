import type { DefectListItem } from "../types/dashboard";
import type { SectionState } from "../hooks/useDashboardData";
import { formatShortDate, humanizeEnum } from "../utils/format";
import { Panel } from "./Panel";
import { SeverityPill } from "./StatusPill";
import {
  EmptyState,
  ErrorState,
  RestrictedState,
  SkeletonRows,
} from "./states";

/* Critical items first, then by most recently reported. */
function sortDefects(defects: DefectListItem[]): DefectListItem[] {
  const order: Record<string, number> = {
    CRITICAL: 0,
    HIGH: 1,
    MEDIUM: 2,
    LOW: 3,
  };
  return [...defects].sort((a, b) => {
    const bySeverity =
      (order[a.severity] ?? 9) - (order[b.severity] ?? 9);
    if (bySeverity !== 0) return bySeverity;
    return (
      new Date(b.created_at).getTime() -
      new Date(a.created_at).getTime()
    );
  });
}

function DefectRow({ defect }: { defect: DefectListItem }) {
  const critical = defect.severity === "CRITICAL";
  return (
    <div
      className={`grid grid-cols-[1fr_auto] items-center gap-4 border-b border-mc-border py-3 last:border-b-0 ${
        critical ? "-mx-2 rounded-md border-l-2 border-l-mc-error bg-mc-error/5 px-2" : ""
      }`}
    >
      <div className="min-w-0">
        <p className="truncate text-[13px] font-semibold text-mc-text">
          Drone #{defect.drone}
        </p>
        <p className="truncate font-mono text-[11px] text-mc-muted">
          {humanizeEnum(defect.defect_type)}
        </p>
      </div>
      <div className="flex items-center gap-4">
        <SeverityPill severity={defect.severity} />
        <span className="hidden w-14 text-right font-mono text-[10px] text-mc-muted sm:inline">
          {formatShortDate(defect.created_at)}
        </span>
      </div>
    </div>
  );
}

export function DefectsPanel({
  state,
}: {
  state: SectionState<DefectListItem[]>;
}) {
  return (
    <Panel title="Open Defects">
      {state.status === "loading" ? (
        <SkeletonRows rows={4} />
      ) : state.status === "restricted" ? (
        <RestrictedState description="Your role does not have permission to view defect data." />
      ) : state.status === "error" ? (
        <ErrorState />
      ) : !state.data || state.data.length === 0 ? (
        <EmptyState
          title="No open defects"
          description="Reported defects will appear here."
        />
      ) : (
        <div>
          {sortDefects(state.data).map((defect) => (
            <DefectRow key={defect.id} defect={defect} />
          ))}
        </div>
      )}
    </Panel>
  );
}
