import { ArrowRight } from "lucide-react";
import { Link } from "react-router";

import { Panel } from "../../../shared/components/Panel";
import {
  EmptyState,
  ErrorState,
  SkeletonRows,
} from "../../../shared/components/states";
import { MissionStatusPill } from "../../../shared/components/StatusPill";
import type { SectionState } from "../../../shared/types/api";
import type { MissionListItem } from "../../../shared/types/missions";
import {
  formatUtcTime,
} from "../../../shared/utils/format";

function commanderName(mission: MissionListItem): string {
  const commander = mission.commander;
  if (!commander) return "Unassigned";
  return commander.username;
}

function MissionRow({ mission }: { mission: MissionListItem }) {
  return (
    <div className="grid grid-cols-[auto_1fr_auto] items-center gap-4 border-b border-mc-border py-3 last:border-b-0">
      <span className="font-mono text-[11px] font-semibold text-mc-accent">
        MSN-{mission.id}
      </span>
      <div className="min-w-0">
        <p className="truncate text-[13px] font-semibold text-mc-text">
          {mission.title}
        </p>
        <p className="truncate font-mono text-[11px] text-mc-muted">
          {mission.location_description || "Location TBD"}
        </p>
      </div>
      <div className="flex items-center gap-4">
        <MissionStatusPill status={mission.status} />
        <div className="hidden text-right sm:block">
          <p className="text-[12px] text-mc-text">
            {commanderName(mission)}
          </p>
          <p className="font-mono text-[10px] text-mc-muted">
            {formatUtcTime(mission.started_at)}
          </p>
        </div>
      </div>
    </div>
  );
}

export function MissionsList({
  state,
}: {
  state: SectionState<MissionListItem[]>;
}) {
  return (
    <Panel
      title="Active & Recent Missions"
      action={
        <Link
          to="/missions"
          className="flex items-center gap-1 font-mono text-[11px] font-semibold uppercase tracking-wide text-mc-accent hover:text-mc-accent-hover"
        >
          View all
          <ArrowRight className="h-3 w-3" />
        </Link>
      }
    >
      {state.status === "loading" ? (
        <SkeletonRows rows={5} />
      ) : state.status === "error" ? (
        <ErrorState />
      ) : !state.data || state.data.length === 0 ? (
        <EmptyState
          title="No active missions"
          description="Missions will appear here once created."
        />
      ) : (
        <div>
          {state.data.map((mission) => (
            <MissionRow key={mission.id} mission={mission} />
          ))}
        </div>
      )}
    </Panel>
  );
}
