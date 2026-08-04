import { useState } from "react";
import {
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import type { DragStartEvent, DragOverEvent, DragEndEvent } from "@dnd-kit/core";
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import { updateMissionStatus } from "../api/missionsApi";
import type { Mission } from "../types";

export function useMissionDnD(
  missions: Mission[],
  mutateMissions: (updater: Mission[] | ((prev: Mission[] | null) => Mission[])) => void
) {
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



  function handleDragStart(event: DragStartEvent) {
    const { active } = event;
    const mission = missions.find((m) => m.id === active.id);
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

    mutateMissions((prevOrNull) => {
      const prev = prevOrNull || [];
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
          newMissions.push({
            ...activeMissionItem,
            status: overMission.status,
          });
          return newMissions;
        } else {
          // Same column: no manual reordering allowed, sorting is deterministic
          return prev;
        }
      }

      if (isOverAColumn) {
        const status = over.data.current?.status;
        if (status && activeMissionItem.status !== status) {
          // Move to the end of the new column
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



    const currentMission = missions.find((m) => m.id === active.id);
    if (
      currentMission &&
      originalActiveMission &&
      currentMission.status !== originalActiveMission.status
    ) {
      try {
        await updateMissionStatus(currentMission.rawId, currentMission.status);
      } catch (err) {
        console.error("Failed to update status", err);
        mutateMissions((prevOrNull) => {
          const prev = prevOrNull || [];
          const reverted = prev.map((m) =>
            m.id === active.id ? { ...m, status: originalActiveMission.status } : m
          );
          return reverted;
        });
      }
    }
  }

  return {
    sensors,
    activeMission,
    handleDragStart,
    handleDragOver,
    handleDragEnd,
  };
}
