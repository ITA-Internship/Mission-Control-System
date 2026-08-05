export type VideoStatus = "ready" | "uploading" | "failed";

export interface Video {
  id: string;
  title: string;
  status: VideoStatus;
  duration: string;
  missionId: string;
  missionName: string;
  droneId: string;
  droneName: string;
  uploadedBy: string;
  uploadedAt: string;
  fileSize: string;
  checksum: string;
  url: string;
  fileName: string;
  progress?: number;
  errorMsg?: string;
}

export type AuditAction = "View" | "Download" | "Upload" | "Update" | "Delete" | "Denied";

export interface AuditEntry {
  id: string;
  action: AuditAction;
  actor: string;
  targetMedia: string;
  targetId: string;
  mission: string;
  timestamp: string;
  result: "Success" | "Denied" | "Failed";
}

export interface BackendVideo {
  id: number;
  mission: number;
  drone: number;
  uploaded_by: number;
  uploaded_by_username: string | null;
  file: string;
  file_name: string;
  file_size: number;
  content_type: string;
  status: "uploading" | "ready" | "failed";
  checksum: string;
  duration_seconds: number | null;
  recorded_at: string | null;
  created_at: string;
  updated_at: string;
  url: string;
}

export interface BackendAuditLog {
  id: number;
  action: "view" | "download" | "upload" | "update" | "delete" | "denied";
  artifact: number | null;
  mission: number | null;
  user: {
    id: number;
    username: string;
  } | null;
  changes: unknown;
  ip_address: string | null;
  created_at: string;
}

export interface PaginatedVideos {
  count: number;
  next: string | null;
  previous: string | null;
  results: BackendVideo[];
}

export interface PaginatedAuditLogs {
  count: number;
  next: string | null;
  previous: string | null;
  results: BackendAuditLog[];
}

export interface MissionBasic {
  id: number;
  title?: string;
  callsign?: string;
}

export interface DroneBasic {
  id: number;
  drone_model?: number;
  inventory_number?: string;
  mission_id?: number;
  status?: string;
}

export interface MediaStats {
  total_used_bytes: number;
  allotted_bytes: number;
}

