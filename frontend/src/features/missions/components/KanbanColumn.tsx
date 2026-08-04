import { Target } from "lucide-react";
import type { Mission, Status } from "../types";
import { MissionCard } from "./MissionCard";
import { STATUS_META } from "./Pills";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { useDroppable } from "@dnd-kit/core";

export function KanbanColumn({
  status,
  missions,
  onCardClick,
}: {
  status: Status;
  missions: Mission[];
  onCardClick: (m: Mission) => void;
}) {
  const m = STATUS_META[status];

  const { setNodeRef, isOver } = useDroppable({
    id: status,
    data: { type: "Column", status },
  });

  return (
    <div
      ref={setNodeRef}
      className={`flex flex-col rounded-xl min-w-[280px] flex-1 transition-all duration-300 ease-in-out bg-[#0B0F14]/60 border border-white/[0.06] ${isOver ? 'ring-2 ring-[#C8A24A]/20 bg-[#C8A24A]/5 border-[#C8A24A]/40 shadow-[inset_0_0_20px_rgba(200,162,74,0.05)]' : ''}`}
    >
      {/* Column header */}
      <div className="px-3 py-3 border-b border-white/[0.04] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: m.color }} />
          <span className="text-[12px] font-mono font-medium tracking-widest" style={{ color: m.color }}>
            {m.label}
          </span>
        </div>
        <span
          className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded-full"
          style={{ background: m.bg, color: m.color }}
        >
          {missions.length}
        </span>
      </div>

      {/* Cards */}
      <div className="flex-1 flex flex-col gap-2.5 p-3 overflow-y-auto max-h-[calc(100vh-280px)]">
        {missions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 gap-2">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center bg-white/[0.04]"
            >
              <Target size={14} color="#8A94A6" />
            </div>
            <span className="text-[11px] font-mono text-[#8A94A6]">No missions</span>
          </div>
        ) : (
          <SortableContext items={missions.map(m => m.id)} strategy={verticalListSortingStrategy}>
            {missions.map(mission => (
              <MissionCard key={mission.id} mission={mission} onClick={() => onCardClick(mission)} />
            ))}
          </SortableContext>
        )}
      </div>
    </div>
  );
}
