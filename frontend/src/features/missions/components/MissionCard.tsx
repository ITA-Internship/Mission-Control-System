import { Clock, MapPin, Navigation, Users } from "lucide-react";
import type { Mission } from "../types";
import { ResultPill, StatusPill } from "./Pills";
import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

export function MissionCard({ mission, onClick, isOverlay }: { mission: Mission; onClick?: () => void; isOverlay?: boolean }) {
  const [hovered, setHovered] = useState(false);
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
    background: isOverlay ? "#1A222C" : hovered && !isDragging ? "#1E2733" : "#161D26",
    border: `1px solid ${isOverlay ? "rgba(200,162,74,0.3)" : hovered && !isDragging ? "rgba(200,162,74,0.25)" : "rgba(255,255,255,0.07)"}`,
    boxShadow: isOverlay
      ? "0 12px 32px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(200,162,74,0.3)"
      : hovered && !isDragging
        ? "0 0 0 1px rgba(200,162,74,0.1)"
        : "none",
    opacity: isDragging ? 0.3 : 1,
    zIndex: isOverlay ? 999 : "auto",
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="rounded-xl p-3.5 cursor-grab active:cursor-grabbing transition-colors duration-150 select-none"
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
      <div className="flex items-center justify-between pt-2.5 border-t" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
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
