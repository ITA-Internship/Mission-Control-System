import { Activity, CheckCircle2, XCircle, AlertCircle, Info } from "lucide-react";
import { cn } from "./ui/utils";

type AuditResult = "success" | "failure" | "warning" | "info";

interface AuditEvent {
  id: string;
  actor: string;
  actorRole: string;
  action: string;
  target: string;
  targetType: string;
  timestamp: string;
  result: AuditResult;
}

const AUDIT_EVENTS: AuditEvent[] = [
  { id: "AUD-9901", actor: "Col. R. Vasquez",  actorRole: "Commander", action: "Activated",      target: "NIGHTFALL-3",    targetType: "Mission", timestamp: "07:42:03 UTC", result: "success" },
  { id: "AUD-9900", actor: "System",           actorRole: "Auto",      action: "Lost contact",   target: "DRONE-047",      targetType: "Drone",   timestamp: "07:38:11 UTC", result: "failure" },
  { id: "AUD-9899", actor: "Tech. M. Kwan",    actorRole: "Technician",action: "Reported defect",target: "DEF-441",         targetType: "Defect",  timestamp: "07:31:50 UTC", result: "warning" },
  { id: "AUD-9898", actor: "Lt. S. Petrov",    actorRole: "Operator",  action: "Reassigned",     target: "DRONE-022",      targetType: "Drone",   timestamp: "07:15:22 UTC", result: "success" },
  { id: "AUD-9897", actor: "Cpt. A. Rourke",   actorRole: "Commander", action: "Status updated", target: "SENTINEL-11",    targetType: "Mission", timestamp: "07:08:44 UTC", result: "info" },
  { id: "AUD-9896", actor: "Admin",            actorRole: "Admin",     action: "Role assigned",  target: "T. Okonkwo",     targetType: "User",    timestamp: "06:58:00 UTC", result: "success" },
  { id: "AUD-9895", actor: "System",           actorRole: "Auto",      action: "Battery warning",target: "DRONE-019",      targetType: "Drone",   timestamp: "06:12:09 UTC", result: "warning" },
  { id: "AUD-9894", actor: "Maj. T. Okonkwo",  actorRole: "Commander", action: "Authorized",     target: "IRONWATCH-2",    targetType: "Mission", timestamp: "05:17:38 UTC", result: "success" },
  { id: "AUD-9893", actor: "Dispatcher B.",    actorRole: "Dispatcher",action: "Dispatched",     target: "DRONE-008",      targetType: "Drone",   timestamp: "05:10:15 UTC", result: "success" },
  { id: "AUD-9892", actor: "System",           actorRole: "Auto",      action: "Auto-aborted",   target: "SANDFALL-4",     targetType: "Mission", timestamp: "04:45:01 UTC", result: "failure" },
];

const RESULT_CONFIG: Record<AuditResult, {
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bg: string;
}> = {
  success: { icon: CheckCircle2, color: "text-[#3FB950]", bg: "bg-[#3FB950]/15" },
  failure: { icon: XCircle,      color: "text-[#E5484D]", bg: "bg-[#E5484D]/15" },
  warning: { icon: AlertCircle,  color: "text-[#F0883E]", bg: "bg-[#F0883E]/15" },
  info:    { icon: Info,         color: "text-[#4C8DFF]", bg: "bg-[#4C8DFF]/15" },
};

const TARGET_TYPE_COLORS: Record<string, string> = {
  Mission: "text-[#4C8DFF]",
  Drone:   "text-[#3FB950]",
  Defect:  "text-[#E5484D]",
  User:    "text-[#C8A24A]",
};

function SkeletonEvent() {
  return (
    <div className="flex gap-3 py-2.5 animate-pulse">
      <div className="w-6 h-6 rounded-full bg-white/10 shrink-0 mt-0.5" />
      <div className="flex-1 space-y-1.5">
        <div className="flex items-center gap-2">
          <div className="h-3 w-28 bg-white/10 rounded" />
          <div className="h-3 w-16 bg-white/10 rounded" />
        </div>
        <div className="h-2.5 w-48 bg-white/10 rounded" />
      </div>
      <div className="h-2.5 w-16 bg-white/10 rounded" />
    </div>
  );
}

interface AuditFeedProps {
  loading?: boolean;
}

export function AuditFeed({ loading = false }: AuditFeedProps) {
  return (
    <div className="rounded-xl border border-border p-5 flex flex-col h-full" style={{ background: "var(--card)" }}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[13px] font-semibold text-[#E6EAF0] uppercase tracking-wider">Recent Activity</h3>
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-[#3FB950] animate-pulse" />
          <span className="font-mono text-[10px] text-[#8A94A6] uppercase tracking-wider">Live</span>
        </div>
      </div>

      {loading ? (
        <div className="divide-y divide-border">
          {[...Array(6)].map((_, i) => <SkeletonEvent key={i} />)}
        </div>
      ) : AUDIT_EVENTS.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center py-10 gap-3">
          <Activity className="w-8 h-8 text-[#2E3A4A]" />
          <p className="text-[13px] text-[#8A94A6]">No recent activity</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto divide-y divide-border -mx-1 px-1">
          {AUDIT_EVENTS.map((event) => {
            const ResultIcon = RESULT_CONFIG[event.result].icon;
            return (
              <div
                key={event.id}
                className="flex items-start gap-3 py-2.5 px-1 -mx-1 rounded-lg hover:bg-white/5 cursor-pointer transition-colors group"
              >
                {/* Icon */}
                <div className={cn(
                  "w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5",
                  RESULT_CONFIG[event.result].bg
                )}>
                  <ResultIcon className={cn("w-3 h-3", RESULT_CONFIG[event.result].color)} />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center flex-wrap gap-x-1 gap-y-0.5">
                    <span className="font-mono text-[11px] font-semibold text-[#E6EAF0] group-hover:text-[#C8A24A] transition-colors">
                      {event.actor}
                    </span>
                    <span className="font-mono text-[10px] text-[#8A94A6]">
                      [{event.actorRole}]
                    </span>
                    <span className="font-mono text-[11px] text-[#8A94A6]">{event.action}</span>
                    <span className={cn(
                      "font-mono text-[11px] font-medium",
                      TARGET_TYPE_COLORS[event.targetType] || "text-[#E6EAF0]"
                    )}>
                      {event.target}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="font-mono text-[10px] text-[#8A94A6]">{event.id}</span>
                    <span className="text-[#2E3A4A]">·</span>
                    <span className={cn(
                      "font-mono text-[10px] px-1.5 py-0.5 rounded uppercase tracking-wide",
                      RESULT_CONFIG[event.result].bg,
                      RESULT_CONFIG[event.result].color
                    )}>
                      {event.result}
                    </span>
                  </div>
                </div>

                {/* Timestamp */}
                <span className="font-mono text-[10px] text-[#8A94A6] shrink-0 mt-0.5">{event.timestamp}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
