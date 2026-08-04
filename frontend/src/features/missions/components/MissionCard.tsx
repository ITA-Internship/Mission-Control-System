import { Clock, MapPin, Navigation, Users } from "lucide-react";
import type { Mission } from "../types";
import { ResultPill, StatusPill } from "./Pills";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

export function MissionCard({ mission, onClick, isOverlay }: { mission: Mission; onClick?: () => void; isOverlay?: boolean }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: mission.id, data: { type: "Mission", mission } });

  const style = {
    transform: CSS.Translate.toString(transform),
    transition,
  };

  const dynamicClasses = isOverlay
    ? "bg-[#1A222C] border-[#C8A24A]/30 shadow-[0_12px_32px_rgba(0,0,0,0.4),0_0_0_1px_rgba(200,162,74,0.3)] z-[999]"
    : `border-white/[0.07] ${isDragging ? "bg-[#161D26] opacity-30" : "bg-[#161D26] hover:bg-[#1E2733] hover:border-[#C8A24A]/25 hover:shadow-[0_0_0_1px_rgba(200,162,74,0.1)] opacity-100"}`;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={onClick}
      className={`rounded-xl p-3.5 border cursor-grab active:cursor-grabbing transition-colors duration-150 select-none ${dynamicClasses}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2.5 pointer-events-none">
        <div>
          <div className="text-[11px] font-mono text-[#8A94A6] mb-0.5">{mission.id}</div>
          <div className="text-[13px] font-semibold text-[#E6EAF0] leading-snug tracking-wide">
            {mission.title}
          </div>
        </div>
        <StatusPill status={mission.status} />
      </div>

      {/* Meta */}
      <div className="flex flex-col gap-1.5 mb-3">
        <div className="flex items-center gap-1.5 text-[11px] text-[#8A94A6]">
          <Users size={10} className="shrink-0" />
          <span className="font-mono">{mission.commander}</span>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-[#8A94A6]">
          <MapPin size={10} className="shrink-0" />
          <span className="font-mono truncate">{mission.location}</span>
        </div>
        {mission.startedAt && (
          <div className="flex items-center gap-1.5 text-[11px] text-[#8A94A6]">
            <Clock size={10} className="shrink-0" />
            <span className="font-mono">{mission.startedAt}</span>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-2.5 border-t border-white/[0.06]">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 text-[11px] font-mono text-[#8A94A6]">
            <Navigation size={10} />
            {mission.droneCount}
          </span>
          <span className="flex items-center gap-1 text-[11px] font-mono text-[#8A94A6]">
            <Users size={10} />
            {mission.operatorCount}
          </span>
        </div>
        {mission.result && <ResultPill result={mission.result} />}
      </div>
    </div>
  );
}
