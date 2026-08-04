/* Mirrors `Drone.STATUS_CHOICES` in `drones/models.py`. */
export type DroneStatus =
  | "ACTIVE"
  | "IN_MISSION"
  | "DAMAGED"
  | "LOST"
  | "MAINTENANCE"
  | "DECOMMISSIONED"
  | "SOLD"
  | "TRANSFERRED"
  | "WRITTEN_OFF";

export interface DroneListItem {
  id: number;
  serial_number: string;
  inventory_number: string;
  name: string;
  status: DroneStatus;
  status_label: string;
  status_category: string;
}
