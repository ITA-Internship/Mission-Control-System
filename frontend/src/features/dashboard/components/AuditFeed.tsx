import { Panel } from "../../../shared/components/Panel";
import {
  EmptyState,
  ErrorState,
  RestrictedState,
  SkeletonRows,
} from "../../../shared/components/states";
import type { AuditLogItem } from "../../../shared/types/accounts";
import type { SectionState } from "../../../shared/types/api";
import { cn } from "../../../shared/utils/cn";
import { formatRelative, humanizeEnum } from "../../../shared/utils/format";

function resultColor(result: string): string {
  const normalized = result.toUpperCase();
  if (normalized === "SUCCESS") return "bg-status-active";
  if (normalized === "FAILURE" || normalized === "FAILED")
    return "bg-mc-error";
  return "bg-mc-muted";
}

function AuditRow({ entry }: { entry: AuditLogItem }) {
  const actor = entry.actor_username ?? "System";
  const target = entry.target_user_username;
  return (
    <div className="flex items-start gap-3 border-b border-mc-border py-3 last:border-b-0">
      <span
        role="img"
        aria-label={`Result: ${humanizeEnum(entry.result)}`}
        className={cn(
          "mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full",
          resultColor(entry.result),
        )}
      />
      <div className="min-w-0 flex-1">
        <p className="text-[12px] leading-snug text-mc-text">
          <span className="font-semibold">{actor}</span>{" "}
          <span className="text-mc-muted">
            {humanizeEnum(entry.action_type).toLowerCase()}
          </span>
          {target && (
            <>
              {" "}
              <span className="text-mc-muted">→</span>{" "}
              <span className="font-semibold">{target}</span>
            </>
          )}
        </p>
        {entry.description && (
          <p className="truncate font-mono text-[10px] text-mc-muted">
            {entry.description}
          </p>
        )}
      </div>
      <span className="shrink-0 font-mono text-[10px] text-mc-muted">
        {formatRelative(entry.created_at)}
      </span>
    </div>
  );
}

export function AuditFeed({
  state,
}: {
  state: SectionState<AuditLogItem[]>;
}) {
  return (
    <Panel title="Recent Activity">
      {state.status === "loading" ? (
        <SkeletonRows rows={5} />
      ) : state.status === "restricted" ? (
        <RestrictedState description="Your role does not have permission to view the audit feed." />
      ) : state.status === "error" ? (
        <ErrorState />
      ) : !state.data || state.data.length === 0 ? (
        <EmptyState
          title="No recent activity"
          description="Audit events will appear here."
        />
      ) : (
        <div>
          {state.data.map((entry) => (
            <AuditRow key={entry.id} entry={entry} />
          ))}
        </div>
      )}
    </Panel>
  );
}
