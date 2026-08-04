import { apiRequest, withQuery } from "../../../shared/api/apiClient";
import type { Mission, MissionDTO, MissionCreateDTO, MissionUpdateDTO, Status, Result } from "../types";

function mapMissionDtoToUi(dto: MissionDTO): Mission {
  return {
    id: `MSN-${String(dto.id).padStart(3, "0")}`,
    rawId: dto.id,
    title: dto.title,
    status: (dto.status.charAt(0).toUpperCase() + dto.status.slice(1)) as Status,
    commander: dto.commander
      ? (dto.commander.first_name && dto.commander.last_name
          ? `${dto.commander.first_name} ${dto.commander.last_name}`
          : dto.commander.username)
      : "Unknown",
    commanderId: dto.commander ? dto.commander.id : null,
    location: dto.location_description || "Unknown Location",
    startedAt: dto.started_at ? new Date(dto.started_at).toISOString().replace("T", " ").slice(0, 16) : null,
    endedAt: dto.ended_at ? new Date(dto.ended_at).toISOString().replace("T", " ").slice(0, 16) : null,
    result: dto.result ? (dto.result.charAt(0).toUpperCase() + dto.result.slice(1)) as Result : null,
    droneCount: dto.drones ? dto.drones.length : 0,
    operatorCount: dto.drones ? new Set(dto.drones.map(d => d.operator_id).filter(Boolean)).size : 0,
    notes: dto.notes || "",
  };
}

export async function fetchMissions(): Promise<Mission[]> {
  const data = await apiRequest<{ results: MissionDTO[] }>("/api/missions/");
  return data.results.map(mapMissionDtoToUi);
}

export async function updateMissionStatus(rawId: number, status: Status): Promise<Mission> {
  const dto = await apiRequest<MissionDTO>(`/api/missions/${rawId}/status/`, {
    method: "PATCH",
    json: { status: status.toLowerCase() },
  });
  return mapMissionDtoToUi(dto);
}

export async function createMission(data: MissionCreateDTO): Promise<Mission> {
  const dto = await apiRequest<MissionDTO>("/api/missions/", {
    method: "POST",
    json: data,
  });
  return mapMissionDtoToUi(dto);
}

export async function updateMission(rawId: number, data: MissionUpdateDTO): Promise<Mission> {
  const dto = await apiRequest<MissionDTO>(`/api/missions/${rawId}/`, {
    method: "PATCH",
    json: data,
  });
  return mapMissionDtoToUi(dto);
}

/** Commander option for the mission form dropdown. */
export interface CommanderOption {
  id: number;
  name: string;
}

/**
 * Fetch available commanders.
 *
 * Tries the admin user list endpoint first (filtering by the COMMANDER role).
 * If that endpoint is not available yet (404), falls back to extracting unique
 * commanders from the currently loaded missions list.
 */
export async function fetchCommanders(): Promise<CommanderOption[]> {
  // Try the admin user-list endpoint with role filter for commanders.
  // The role id for COMMANDER may vary; we fetch roles first to find it.
  const rolesData = await apiRequest<{ results: { id: number; code: string; name: string }[] }>(
    withQuery("/api/roles/", { page_size: 50 }),
  );
  const commanderRole = rolesData.results.find(
    (r) => r.code === "COMMANDER" || r.name === "Commander",
  );
  if (!commanderRole) {
    throw new Error("Commander role not found");
  }

  const usersData = await apiRequest<{
    results: {
      id: number;
      username: string;
      first_name?: string;
      last_name?: string;
    }[];
  }>(
    withQuery("/api/accounts/users/", {
      page_size: 100,
      role: commanderRole.id,
      is_active: true,
    }),
  );

  return usersData.results
    .map((u) => ({
      id: u.id,
      name:
        u.first_name && u.last_name
          ? `${u.first_name} ${u.last_name}`
          : u.username,
    }))
    .sort((a, b) => a.name.localeCompare(b.name));
}
