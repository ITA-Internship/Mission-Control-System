export type DroneStatus = 
  | "ACTIVE" | "IN_MISSION" | "DAMAGED" | "LOST" 
  | "MAINTENANCE" | "DECOMMISSIONED" | "SOLD" 
  | "TRANSFERRED" | "WRITTEN_OFF";

export type Classification = 
  | "RECONNAISSANCE" | "COMBAT" | "TRANSPORT" | "SURVEILLANCE";

export type DrawerMode = "add" | "edit";
export type SortKey = "created_at" | "status" | "name" | "classification" | "serial_number";
export type SortDir = "asc" | "desc" | null;

export interface DroneModel {
  id: number;
  name: string;
  manufacturer: string;
  description?: string;
  supported_classifications: Classification[];
  is_active: boolean;
}

export interface MilitaryUnit {
  id: number;
  name: string;
  code: string;
  is_active: boolean;
}

export interface Drone {
  id: number;
  serial_number: string;
  inventory_number: string;
  name: string;
  drone_model: number | string;
  drone_model_name?: string;
  classification: Classification;
  status: DroneStatus;
  military_unit: number | string;
  military_unit_name?: string;
  acquired_at: string;
  notes: string;
  created_at: string;
  updated_at: string;
  status_label: string;
  status_indicator: string;
  status_category: string;
  max_speed_kmh?: number | null;
  max_range_km?: number | null;
  payload_capacity_g?: number | null;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}