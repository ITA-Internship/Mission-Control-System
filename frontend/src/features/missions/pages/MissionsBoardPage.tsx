import { useState, useMemo, useEffect, useCallback } from "react";
import { useNavigate, useOutletContext } from "react-router";
import { LayoutGrid, List, Plus } from "lucide-react";
import { fetchMissions, createMission, updateMission, fetchCommanders } from "../api/missionsApi";
import type { CommanderOption } from "../api/missionsApi";
import type { Mission, Status, View, MissionCreateDTO, MissionUpdateDTO } from "../types";
import { KanbanColumn } from "../components/KanbanColumn";
import { DataTable } from "../components/DataTable";
import { FilterBar } from "../components/FilterBar";

import type { Filters, Chip } from "../components/FilterBar";
import type { ShellContext } from "../../../shared/layout/shellContext";
import { MissionModal } from "../components/MissionModal";
import { useAsyncData } from "../../../shared/hooks/useAsyncData";

const STATUSES: Status[] = ["Planned", "Active", "Completed", "Aborted"];

function Skeleton() {
  return (
    <div className="animate-pulse flex flex-col gap-3">
      {[1, 2, 3].map(i => (
        <div key={i} className="rounded-xl p-4" style={{ background: "#161D26", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="flex justify-between mb-3">
            <div className="h-2 w-16 rounded" style={{ background: "rgba(255,255,255,0.07)" }} />
            <div className="h-4 w-16 rounded-full" style={{ background: "rgba(255,255,255,0.07)" }} />
          </div>
          <div className="h-3 w-3/4 rounded mb-2" style={{ background: "rgba(255,255,255,0.07)" }} />
          <div className="h-2 w-1/2 rounded" style={{ background: "rgba(255,255,255,0.05)" }} />
        </div>
      ))}
    </div>
  );
}

import { DndContext, DragOverlay, closestCenter } from "@dnd-kit/core";
import { MissionCard } from "../components/MissionCard";
import { useMissionDnD } from "../hooks/useMissionDnD";

export function MissionsBoardPage() {
  const { user: currentUser } = useOutletContext<ShellContext>();
  const [view, setView] = useState<View>("board");
  const [filters, setFilters] = useState<Filters>({ search: "", status: "", commander: "", result: "" });
  const [missions, setMissions] = useState<Mission[]>([]);

  const navigate = useNavigate();
  const handleMissionClick = (m: Mission) => navigate("/missions/" + m.id);
  const [editingMission, setEditingMission] = useState<Mission | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { sensors, activeMission, handleDragStart, handleDragOver, handleDragEnd } = useMissionDnD(missions, setMissions);

  // Derive active filter chips
  const chips: Chip[] = useMemo(() => {
    const c: Chip[] = [];
    if (filters.search) c.push({ key: "search", label: `"${filters.search}"` });
    if (filters.status) c.push({ key: "status", label: `Status: ${filters.status}` });
    if (filters.commander) c.push({ key: "commander", label: `Cmdr: ${filters.commander.split(" ").slice(-1)[0]}` });
    if (filters.result) c.push({ key: "result", label: `Result: ${filters.result}` });
    return c;
  }, [filters]);

  function removeChip(key: string) {
    setFilters(f => ({ ...f, [key]: "" }));
  }

  const loadData = useCallback(async (signal: AbortSignal) => {
    const fetchedMissions = await fetchMissions(signal);

    const sortedData = [...fetchedMissions].sort((a, b) => {
      if (a.status !== b.status) return 0;

      const timeA = (a.status === "Completed" || a.status === "Aborted") ? (a.endedAt || a.startedAt || "") : (a.startedAt || "");
      const timeB = (b.status === "Completed" || b.status === "Aborted") ? (b.endedAt || b.startedAt || "") : (b.startedAt || "");

      if (a.status === "Planned") {
        return timeA.localeCompare(timeB);
      } else {
        return timeB.localeCompare(timeA);
      }
    });

    return sortedData;
  }, []);

  const { data, isLoading: loading, error, reload } = useAsyncData(loadData);

  useEffect(() => {
    if (data) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setMissions(data);
    }
  }, [data]);

  const filtered = useMemo(() => {
    return missions.filter(m => {
      const q = filters.search.toLowerCase();
      if (q && !m.title.toLowerCase().includes(q) && !m.location.toLowerCase().includes(q)) return false;
      if (filters.status && m.status !== filters.status) return false;
      if (filters.commander && m.commander !== filters.commander) return false;
      if (filters.result && m.result !== filters.result) return false;
      return true;
    });
  }, [missions, filters]);

  const totalCount = missions.length;

  const filterCommanders = useMemo(() => {
    const cmds = new Set(missions.map(m => m.commander).filter(c => c && c !== "Unknown"));
    return Array.from(cmds).sort();
  }, [missions]);

  const [modalCommanders, setModalCommanders] = useState<CommanderOption[]>([]);

  // Load commanders: try the admin API
  const loadCommanders = useCallback(async () => {
    try {
      const cmds = await fetchCommanders();
      setModalCommanders(cmds);
    } catch (e) {
      console.error("Failed to fetch commanders", e);
      setModalCommanders([]);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadCommanders();
  }, [loadCommanders]);

  async function handleSaveMission(data: MissionCreateDTO | MissionUpdateDTO) {
    if (editingMission) {
      const updated = await updateMission(editingMission.rawId, data);
      setMissions(prev => prev.map(m => (m.id === updated.id ? updated : m)));
    } else {
      if (!currentUser?.unit) {
        alert("You must be assigned to a military unit to create a mission.");
        return;
      }
      const payload = { ...data, unit_id: currentUser.unit };
      const created = await createMission(payload as MissionCreateDTO);
      setMissions(prev => [created, ...prev]);
    }
    setIsModalOpen(false);
    setEditingMission(null);
  }

  function openNewModal() {
    setEditingMission(null);
    setIsModalOpen(true);
  }

  return (
    <div className="flex flex-col h-full font-[Inter,sans-serif]" style={{ color: "#E6EAF0" }}>
      {/* Page header */}
      <div className="flex items-center justify-between mb-5 gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-[22px] font-bold tracking-wide leading-none">
              Missions
            </h1>
            <div className="text-[11px] font-mono text-[#8A94A6] mt-1 tracking-wide">
              {totalCount} total · {missions.filter(m => m.status === "Active").length} active
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* View toggle */}
          <div className="flex items-center rounded-lg p-0.5 bg-[#161D26] border border-white/10">
            {(["board", "list"] as const).map(v => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`flex items-center gap-1.5 px-2 py-1 rounded-md transition-colors text-[9px] font-mono ${
                  view === v
                    ? "bg-[#C8A24A]/10 text-[#C8A24A] border border-[#C8A24A]/20"
                    : "text-[#8A94A6] hover:text-[#E6EAF0] border border-transparent"
                }`}
              >
                {v === "board" ? <LayoutGrid size={11} /> : <List size={11} />}
                {v === "board" ? "Board" : "List"}
              </button>
            ))}
          </div>

          {/* New Mission */}
          <button
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[9px] font-mono font-semibold transition-all bg-[#C8A24A] text-[#0B0F14] hover:bg-[#d4af5e]"
            onClick={openNewModal}
          >
            <Plus size={12} strokeWidth={2.5} />
            New Mission
          </button>
        </div>
      </div>

      <div className="mb-5">
        <FilterBar filters={filters} setFilters={setFilters} chips={chips} removeChip={removeChip} availableCommanders={filterCommanders} />
      </div>

      {/* Content */}
      {error ? (
        <div className="flex flex-col items-center justify-center py-20 text-[#8A94A6]">
          <div className="text-[13px] font-mono mb-3 text-[#E5484D]">Failed to load missions.</div>
          <button onClick={reload} className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-[11px] font-mono transition-colors">
            Try Again
          </button>
        </div>
      ) : loading ? (
        <div className="grid grid-cols-4 gap-4">
          {STATUSES.map(s => <Skeleton key={s} />)}
        </div>
      ) : view === "board" ? (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
        >
          <div className="flex gap-4 overflow-x-auto pb-4">
            {STATUSES.map(status => (
              <KanbanColumn
                key={status}
                status={status}
                missions={filtered.filter(m => m.status === status)}
                onCardClick={handleMissionClick}
              />
            ))}
          </div>
          <DragOverlay>
            {activeMission ? <MissionCard mission={activeMission} isOverlay /> : null}
          </DragOverlay>
        </DndContext>
      ) : (
        <DataTable
          missions={filtered}
          onOpen={handleMissionClick}
        />
      )}

      {/* Modal */}
      {isModalOpen && (
        <MissionModal
          mission={editingMission}
          onClose={() => { setIsModalOpen(false); setEditingMission(null); }}
          onSave={handleSaveMission}
          availableCommanders={modalCommanders}
        />
      )}
    </div>
  );
}
