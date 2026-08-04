export type Status = "Planned" | "Active" | "Completed" | "Aborted";
export type Result = "Success" | "Failure" | null;
export type View = "board" | "list";

export interface Mission {
  id: string;
  rawId: number;
  title: string;
  status: Status;
  commander: string;
  commanderId?: number | null;
  location: string;
  startedAt: string | null;
  endedAt: string | null;
  result: Result;
  droneCount: number;
  operatorCount: number;
  notes: string;
  lat?: string | null;
  lng?: string | null;
}

export interface MissionDTO {
  id: number;
  title: string;
  status: string;
  commander: {
    id: number;
    username: string;
    email: string;
    first_name?: string;
    last_name?: string;
  } | null;
  location_description: string | null;
  latitude: string | null;
  longitude: string | null;
  started_at: string | null;
  ended_at: string | null;
  result: string | null;
  notes: string;
  drones: {
    drone_id: number;
    operator_id: number | null;
  }[];
}

export interface MissionCreateDTO {
  title: string;
  commander_id?: number | null;
  unit_id: number; // Required by backend
  location_description?: string;
  latitude?: string;
  longitude?: string;
  started_at?: string;
  notes?: string;
}

export interface MissionUpdateDTO {
  title?: string;
  commander_id?: number | null;
  location_description?: string;
  latitude?: string;
  longitude?: string;
  started_at?: string;
  notes?: string;
}
