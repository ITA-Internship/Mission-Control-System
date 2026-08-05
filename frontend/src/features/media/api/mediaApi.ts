import { apiRequest, apiUpload } from "../../../shared/api/apiClient";
import type { PaginatedVideos, PaginatedAuditLogs, BackendVideo, MissionBasic, DroneBasic, MediaStats } from "../types/mediaTypes";

interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export const mediaApi = {
  fetchVideos: async (params?: Record<string, string | number | boolean | null | undefined>): Promise<PaginatedVideos> => {
    // We construct the query string manually or let apiClient's withQuery handle it if it was exposed.
    // For now we'll pass standard search params if they exist.
    let path = "/api/media/videos/";
    if (params) {
      const search = new URLSearchParams();
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null && value !== "") {
          search.set(key, String(value));
        }
      }
      const qs = search.toString();
      if (qs) path += `?${qs}`;
    }
    return apiRequest<PaginatedVideos>(path);
  },

  uploadVideo: async (formData: FormData, onProgress?: (progress: number) => void): Promise<BackendVideo> => {
    return apiUpload<BackendVideo>("/api/media/videos/", formData, onProgress);
  },

  deleteVideo: async (id: string | number): Promise<void> => {
    return apiRequest(`/api/media/videos/${id}/`, {
      method: "DELETE",
    });
  },

  updateVideo: async (id: string | number, data: { file_name?: string }): Promise<BackendVideo> => {
    return apiRequest<BackendVideo>(`/api/media/videos/${id}/`, {
      method: "PATCH",
      json: data,
    });
  },

  fetchAuditLogs: async (params?: Record<string, string | number | boolean | null | undefined>): Promise<PaginatedAuditLogs> => {
    let path = "/api/media/audit-logs/";
    if (params) {
      const search = new URLSearchParams();
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null && value !== "") {
          search.set(key, String(value));
        }
      }
      const qs = search.toString();
      if (qs) path += `?${qs}`;
    }
    return apiRequest<PaginatedAuditLogs>(path);
  },

  fetchMissions: async (): Promise<Paginated<MissionBasic>> => {
    return apiRequest<Paginated<MissionBasic>>("/api/missions/");
  },

  fetchDrones: async (): Promise<Paginated<DroneBasic>> => {
    return apiRequest<Paginated<DroneBasic>>("/api/drones/");
  },

  fetchMissionAssignments: async (missionId: string | number): Promise<Paginated<{ drone: number, drone_details: DroneBasic }>> => {
    return apiRequest(`/api/missions/${missionId}/assignments/`);
  },

  fetchMediaStats: async (): Promise<MediaStats> => {
    return apiRequest<MediaStats>("/api/media/stats/");
  },
};
