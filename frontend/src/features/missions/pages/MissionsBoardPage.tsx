import { useState, useMemo, useEffect, useCallback } from "react";
import { useNavigate } from "react-router";
import { LayoutGrid, List, Plus } from "lucide-react";
import { fetchMissions, createMission, updateMission, fetchCommanders, updateMissionStatus } from "../api/missionsApi";
import type { CommanderOption } from "../api/missionsApi";
import type { Mission, Status, View, MissionCreateDTO, MissionUpdateDTO } from "../types";
import { KanbanColumn } from "../components/KanbanColumn";
import { DataTable } from "../components/DataTable";
import { FilterBar } from "../components/FilterBar";

import type { Filters, Chip } from "../components/FilterBar";
import { MissionModal } from "../components/MissionModal";
import { getCurrentUser } from "../../auth/api/authApi";
import type { CurrentUser } from "../../../shared/types/accounts";

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

import { DndContext, DragOverlay, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors } from "@dnd-kit/core";
import type { DragStartEvent, DragOverEvent, DragEndEvent } from "@dnd-kit/core";
import { sortableKeyboardCoordinates, arrayMove } from "@dnd-kit/sortable";
import { MissionCard } from "../components/MissionCard";

export function MissionsBoardPage() {
  const [view, setView] = useState<View>("board");
  const [filters, setFilters] = useState<Filters>({ search: "", status: "", commander: "", result: "" });
  const [missions, setMissions] = useState<Mission[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);

  const navigate = useNavigate();
  const handleMissionClick = (m: Mission) => navigate("/missions/" + m.id);
  const [editingMission, setEditingMission] = useState<Mission | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const [activeMission, setActiveMission] = useState<Mission | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

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

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [data, user] = await Promise.all([fetchMissions(), getCurrentUser()]);
        // To maintain order across sessions without backend support, we could use localStorage here.
        // For now we will just use the backend order and allow local reordering.
        const localOrder = localStorage.getItem("mc_mission_order");
        let sortedData = data;
        if (localOrder) {
          try {
            const orderList = JSON.parse(localOrder) as string[];
            sortedData = [...data].sort((a, b) => {
              const idxA = orderList.indexOf(a.id);
              const idxB = orderList.indexOf(b.id);
              if (idxA === -1 && idxB === -1) return 0;
              if (idxA === -1) return 1;
              if (idxB === -1) return -1;
              return idxA - idxB;
            });
          } catch {
            // Suppress generic update errors silently since we might refresh anyway
          }
        }

        if (active) {
          setMissions(sortedData);
          setCurrentUser(user);
          setLoading(false);
        }
      } catch (err) {
        if (active) {
          console.error("Failed to fetch initial data", err);
          setLoading(false);
        }
      }
    }
    load();
    return () => { active = false; };
  }, []);

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

  function saveOrderToLocal(newMissions: Mission[]) {
    localStorage.setItem("mc_mission_order", JSON.stringify(newMissions.map(m => m.id)));
  }

  function handleDragStart(event: DragStartEvent) {
    const { active } = event;
    const mission = missions.find(m => m.id === active.id);
    if (mission) setActiveMission(mission);
  }

  function handleDragOver(event: DragOverEvent) {
    const { active, over } = event;
    if (!over) return;
    
    const activeId = active.id;
    const overId = over.id;

    if (activeId === overId) return;

    const isActiveAMission = active.data.current?.type === "Mission";
    const isOverAMission = over.data.current?.type === "Mission";
    const isOverAColumn = over.data.current?.type === "Column";

    if (!isActiveAMission) return;

    setMissions((prev) => {
      const activeIndex = prev.findIndex((m) => m.id === activeId);
      if (activeIndex === -1) return prev;
      const activeMissionItem = prev[activeIndex];

      if (isOverAMission) {
        const overIndex = prev.findIndex((m) => m.id === overId);
        if (overIndex === -1) return prev;
        const overMission = prev[overIndex];
        
        if (activeMissionItem.status !== overMission.status) {
          // Moving to a new column
          const newMissions = prev.filter((m) => m.id !== activeId);
          const newOverIndex = newMissions.findIndex((m) => m.id === overId);
          newMissions.splice(newOverIndex, 0, { ...activeMissionItem, status: overMission.status });
          return newMissions;
        } else {
          // Same column, check if index actually changed to prevent re-renders
          if (activeIndex === overIndex) return prev;
          return arrayMove(prev, activeIndex, overIndex);
        }
      }

      if (isOverAColumn) {
        const status = over.data.current?.status;
        if (status && activeMissionItem.status !== status) {
          // Move to the end of the new column by pushing to the end of the global array
          const newMissions = prev.filter((m) => m.id !== activeId);
          newMissions.push({ ...activeMissionItem, status });
          return newMissions;
        }
      }

      return prev;
    });
  }

  async function handleDragEnd(event: DragEndEvent) {
    const originalActiveMission = activeMission;
    setActiveMission(null);
    const { active, over } = event;
    if (!over) return;
    
    setMissions(currentMissions => {
      saveOrderToLocal(currentMissions);
      return currentMissions;
    });

    const currentMission = missions.find(m => m.id === active.id);
    if (currentMission && originalActiveMission && currentMission.status !== originalActiveMission.status) {
      try {
        await updateMissionStatus(currentMission.rawId, currentMission.status);
      } catch (err) {
        console.error("Failed to update status", err);
        setMissions(prev => {
          const reverted = prev.map(m => m.id === active.id ? { ...m, status: originalActiveMission.status } : m);
          saveOrderToLocal(reverted);
          return reverted;
        });
      }
    }
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
          <div
            className="flex items-center rounded-lg p-0.5"
            style={{ background: "#161D26", border: "1px solid rgba(255,255,255,0.08)" }}
          >
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
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[9px] font-mono font-semibold transition-all"
            style={{ background: "#C8A24A", color: "#0B0F14" }}
            onMouseEnter={e => ((e.currentTarget as HTMLElement).style.background = "#d4af5e")}
            onMouseLeave={e => ((e.currentTarget as HTMLElement).style.background = "#C8A24A")}
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
      {loading ? (
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
