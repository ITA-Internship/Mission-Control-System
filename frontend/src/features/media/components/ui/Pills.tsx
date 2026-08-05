import { Lock } from "lucide-react";
import type { VideoStatus, AuditAction, AuditEntry } from "../../types/mediaTypes";

export function StatusPill({ status }: { status: VideoStatus }) {
  const map = {
    ready: { label: "Ready", dot: "bg-emerald-400", wrap: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
    uploading: { label: "Uploading", dot: "bg-mc-accent", wrap: "bg-mc-accent/10 text-mc-accent border-mc-accent/20" },
    failed: { label: "Failed", dot: "bg-red-400", wrap: "bg-red-500/10 text-red-400 border-red-500/20" },
  }[status];

  if (!map) return null;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border ${map.wrap}`}>
      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${map.dot} ${status === "uploading" ? "animate-pulse" : ""}`} />
      {map.label}
    </span>
  );
}

export function AuditActionPill({ action }: { action: AuditAction }) {
  const map: Record<AuditAction, string> = {
    View: "bg-[#8A94A6]/10 text-[#8A94A6] border-[#8A94A6]/15",
    Download: "bg-[#8A94A6]/10 text-[#8A94A6] border-[#8A94A6]/15",
    Upload: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    Update: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    Delete: "bg-red-500/10 text-red-400 border-red-500/20",
    Denied: "bg-red-500/15 text-red-400 border-red-500/25 font-semibold",
  };
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${map[action]}`}>
      {action === "Denied" && <Lock size={9} />}
      {action}
    </span>
  );
}

export function ResultPill({ result }: { result: AuditEntry["result"] }) {
  const map = {
    Success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    Denied: "bg-red-500/15 text-red-400 border-red-500/25 font-semibold",
    Failed: "bg-red-500/15 text-red-400 border-red-500/25",
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${map[result]}`}>
      {result}
    </span>
  );
}
