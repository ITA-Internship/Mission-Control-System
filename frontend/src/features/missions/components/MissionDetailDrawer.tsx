import { Users, MapPin, Clock, Navigation, X } from "lucide-react";
import type { Mission } from "../types";
import { StatusPill, ResultPill, STATUS_META } from "./Pills";

interface MissionDetailDrawerProps {
  mission: Mission;
  onClose: () => void;
  onEdit: () => void;
}

export function MissionDetailDrawer({ mission, onClose, onEdit }: MissionDetailDrawerProps) {
  const statusM = STATUS_META[mission.status];
  
  return (
    <div
      className="fixed inset-0 z-40 flex"
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
      style={{ background: "rgba(0,0,0,0.5)" }}
    >
      <div
        className="ml-auto h-full w-full max-w-md flex flex-col animate-in slide-in-from-right duration-200"
        style={{
          background: "var(--color-mcs-bg)",
          borderLeft: "1px solid rgba(255,255,255,0.09)",
          boxShadow: "-16px 0 48px rgba(0,0,0,0.5)",
        }}
      >
        {/* Header */}
        <div
          className="px-6 py-5 border-b"
          style={{ borderColor: "rgba(255,255,255,0.07)", borderLeft: `3px solid ${statusM.color}` }}
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-[10px] font-mono text-[#8A94A6] tracking-widest mb-1">{mission.id}</div>
              <div className="text-[17px] font-bold text-[#E6EAF0] tracking-wide leading-tight">{mission.title}</div>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <button
                onClick={onEdit}
                className="px-3 py-1.5 rounded-lg text-[11px] font-mono hover:bg-[rgba(200,162,74,0.1)] transition-all"
                style={{ color: "var(--color-mcs-accent)", border: "1px solid rgba(200,162,74,0.3)" }}
              >
                Edit
              </button>
              <button
                onClick={onClose}
                className="w-7 h-7 rounded-lg flex items-center justify-center text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/5 transition-all"
              >
                <X size={14} />
              </button>
            </div>
          </div>
          <div className="flex items-center gap-2 mt-3">
            <StatusPill status={mission.status} />
            {mission.result && <ResultPill result={mission.result} />}
          </div>
        </div>

        {/* Details */}
        <div className="flex-1 overflow-y-auto px-6 py-5 flex flex-col gap-5">
          {[
            { label: "COMMANDER", value: mission.commander, icon: Users },
            { label: "LOCATION", value: mission.location, icon: MapPin },
            { label: "STARTED", value: mission.startedAt ?? "Not started", icon: Clock },
            { label: "ENDED", value: mission.endedAt ?? "Ongoing", icon: Clock },
          ].map(({ label, value, icon: Icon }) => (
            <div key={label}>
              <div className="text-[9px] font-mono tracking-widest text-[#8A94A6] mb-1">{label}</div>
              <div className="flex items-center gap-1.5 text-[13px] font-mono text-[#E6EAF0]">
                <Icon size={12} className="text-[#8A94A6]" />
                {value}
              </div>
            </div>
          ))}

          {/* Assets */}
          <div>
            <div className="text-[9px] font-mono tracking-widest text-[#8A94A6] mb-2">ASSETS</div>
            <div className="flex gap-3">
              <div
                className="flex-1 rounded-lg px-3 py-3 flex items-center gap-2"
                style={{ background: "#1A2230", border: "1px solid rgba(255,255,255,0.06)" }}
              >
                <Navigation size={14} style={{ color: "var(--color-mcs-accent)" }} />
                <div>
                  <div className="text-[18px] font-bold text-[#E6EAF0]">{mission.droneCount}</div>
                  <div className="text-[9px] font-mono text-[#8A94A6] tracking-widest">DRONES</div>
                </div>
              </div>
              <div
                className="flex-1 rounded-lg px-3 py-3 flex items-center gap-2"
                style={{ background: "#1A2230", border: "1px solid rgba(255,255,255,0.06)" }}
              >
                <Users size={14} style={{ color: "var(--color-mcs-accent)" }} />
                <div>
                  <div className="text-[18px] font-bold text-[#E6EAF0]">{mission.operatorCount}</div>
                  <div className="text-[9px] font-mono text-[#8A94A6] tracking-widest">OPERATORS</div>
                </div>
              </div>
            </div>
          </div>

          {/* Notes */}
          {mission.notes && (
            <div>
              <div className="text-[9px] font-mono tracking-widest text-[#8A94A6] mb-2">OPERATIONAL NOTES</div>
              <div
                className="rounded-lg px-4 py-3 text-[13px] font-mono text-[#8A94A6] leading-relaxed whitespace-pre-wrap"
                style={{ background: "#1A2230", border: "1px solid rgba(255,255,255,0.06)" }}
              >
                {mission.notes}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
