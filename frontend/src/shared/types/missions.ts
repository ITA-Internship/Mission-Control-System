import type { UserBrief } from "./accounts";

/* Mirrors `missions.models.Status`. */
export type MissionStatus =
  | "planned"
  | "active"
  | "completed"
  | "aborted";

export interface MissionListItem {
  id: number;
  title: string;
  status: MissionStatus;
  location_description: string | null;
  commander: UserBrief | null;
  started_at: string | null;
  created_at: string | null;
}
