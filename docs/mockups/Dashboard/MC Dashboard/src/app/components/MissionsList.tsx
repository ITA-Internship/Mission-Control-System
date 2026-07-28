import { ArrowRight, Inbox } from "lucide-react";
import { StatusPill } from "./StatusPill";
import type { MissionStatus } from "./StatusPill";
import { cn } from "./ui/utils";

interface Mission {
  id: string;
  title: string;
  status: MissionStatus;
  commander: string;
  location: string;
  startedAt: string;
  priority: "FLASH" | "URGENT" | "ROUTINE";
}

const MISSIONS: Mission[] = [
  { id: "MSN-1047", title: "NIGHTFALL-3",   status: "Active",    commander: "Col. R. Vasquez",  location: "Zone Delta — Sector 7",  startedAt: "07:42 UTC",  priority: "FLASH" },
  { id: "MSN-1046", title: "IRONWATCH-2",   status: "Active",    commander: "Maj. T. Okonkwo",  location: "Perimeter Bravo",        startedAt: "05:18 UTC",  priority: "URGENT" },
  { id: "MSN-1045", title: "SENTINEL-11",   status: "Active",    commander: "Cpt. A. Rourke",   location: "Northern Ridge Alpha",   startedAt: "03:05 UTC",  priority: "ROUTINE" },
  { id: "MSN-1044", title: "HOLLOWPOINT-7", status: "Delayed",   commander: "Lt. S. Petrov",    location: "Grid 42-F Coastline",    startedAt: "01:30 UTC",  priority: "URGENT" },
  { id: "MSN-1043", title: "DUSTFALL-1",    status: "Planning",  commander: "Col. M. Henriksen", location: "Forward Base Echo",     startedAt: "TBD",        priority: "ROUTINE" },
  { id: "MSN-1042", title: "REDKITE-5",     status: "Completed", commander: "Maj. F. Alawi",    location: "Checkpoint Charlie",     startedAt: "22:10 UTC",  priority: "ROUTINE" },
];

const PRIORITY_STYLES = {
  FLASH:   "text-[#E5484D] font-semibold",
  URGENT:  "text-[#F0883E]",
  ROUTINE: "text-[#8A94A6]",
};

function SkeletonRow() {
  return (
    <div className="flex items-center gap-3 py-2.5 animate-pulse">
      <div className="w-20 h-3 bg-white/10 rounded" />
      <div className="flex-1 h-3 bg-white/10 rounded" />
      <div className="w-16 h-5 bg-white/10 rounded-full" />
      <div className="w-24 h-3 bg-white/10 rounded hidden sm:block" />
    </div>
  );
}

interface MissionsListProps {
  loading?: boolean;
}

export function MissionsList({ loading = false }: MissionsListProps) {
  return (
    <div className="rounded-xl border border-border p-5 flex flex-col h-full" style={{ background: "var(--card)" }}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[13px] font-semibold text-[#E6EAF0] uppercase tracking-wider">Active & Recent Missions</h3>
        <button className="flex items-center gap-1 font-mono text-[11px] text-[#C8A24A] hover:text-[#E6EAF0] transition-colors uppercase tracking-wide">
          View all <ArrowRight className="w-3 h-3" />
        </button>
      </div>

      {loading ? (
        <div className="divide-y divide-border">
          {[...Array(5)].map((_, i) => <SkeletonRow key={i} />)}
        </div>
      ) : MISSIONS.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center py-10 gap-3">
          <Inbox className="w-8 h-8 text-[#2E3A4A]" />
          <p className="text-[13px] text-[#8A94A6]">No active missions</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto -mx-1 px-1">
          {/* Table header */}
          <div className="grid grid-cols-[6rem_1fr_6rem_6rem_5rem] gap-x-3 mb-1 px-1">
            {["ID", "MISSION", "STATUS", "COMMANDER", "STARTED"].map(h => (
              <span key={h} className="font-mono text-[10px] text-[#8A94A6] uppercase tracking-wider">{h}</span>
            ))}
          </div>

          <div className="divide-y divide-border">
            {MISSIONS.map((m) => (
              <div
                key={m.id}
                className={cn(
                  "grid grid-cols-[6rem_1fr_6rem_6rem_5rem] gap-x-3 items-center py-2.5 px-1 -mx-1 rounded-lg",
                  "hover:bg-white/5 cursor-pointer transition-colors group"
                )}
              >
                <span className={cn("font-mono text-[11px]", PRIORITY_STYLES[m.priority])}>
                  {m.id}
                </span>
                <div className="min-w-0">
                  <div className="font-mono text-[12px] font-semibold text-[#E6EAF0] truncate group-hover:text-[#C8A24A] transition-colors">
                    {m.title}
                  </div>
                  <div className="font-mono text-[10px] text-[#8A94A6] truncate">{m.location}</div>
                </div>
                <StatusPill type="mission" value={m.status} />
                <span className="font-mono text-[11px] text-[#8A94A6] truncate">{m.commander.split(" ").pop()}</span>
                <span className="font-mono text-[11px] text-[#8A94A6]">{m.startedAt}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
