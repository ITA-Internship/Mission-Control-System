import { useState, useEffect, useCallback, useMemo } from "react";
import { mediaApi } from "../api/mediaApi";
import type { Video, AuditEntry, MissionBasic, DroneBasic, AuditAction, VideoStatus, MediaStats } from "../types/mediaTypes";

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60).toString().padStart(2, "0");
  const s = (seconds % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

export function useMediaLibrary() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditEntry[]>([]);
  const [loadingVideos, setLoadingVideos] = useState(false);
  const [loadingAuditLogs, setLoadingAuditLogs] = useState(false);
  const [errorVideos, setErrorVideos] = useState<string | null>(null);
  const [errorAuditLogs, setErrorAuditLogs] = useState<string | null>(null);

  // Background uploads
  const [activeUploads, setActiveUploads] = useState<Record<string, Video>>({});

  // New states for form dropdowns
  const [missionsList, setMissionsList] = useState<MissionBasic[]>([]);
  const [dronesList, setDronesList] = useState<DroneBasic[]>([]);
  const [stats, setStats] = useState<MediaStats | null>(null);

  const fetchDependencies = useCallback(async () => {
    try {
      const [missionsRes, dronesRes, statsRes] = await Promise.all([
        mediaApi.fetchMissions(),
        mediaApi.fetchDrones(),
        mediaApi.fetchMediaStats(),
      ]);
      setMissionsList(missionsRes.results || []);
      setDronesList(dronesRes.results || []);
      setStats(statsRes);
    } catch (err) {
      console.error("Failed to fetch dependencies", err);
    }
  }, []);

  const fetchVideos = useCallback(async () => {
    setLoadingVideos(true);
    setErrorVideos(null);
    try {
      const response = await mediaApi.fetchVideos();
      const mappedVideos: Video[] = response.results.map((raw) => ({
        id: String(raw.id),
        title: raw.file_name || `Video #${raw.id}`,
        status: raw.status as VideoStatus,
        duration: raw.duration_seconds != null ? formatDuration(raw.duration_seconds) : "--:--",
        missionId: String(raw.mission),
        missionName: `Mission ${raw.mission}`,
        droneId: String(raw.drone),
        droneName: `Drone ${raw.drone}`,
        uploadedBy: raw.uploaded_by_username || "Unknown",
        uploadedAt: new Date(raw.created_at).toLocaleString(),
        fileSize: formatBytes(raw.file_size),
        checksum: raw.checksum || "N/A",
        url: raw.url,
        fileName: raw.url ? raw.url.split('/').pop() || "Unknown" : "Unknown",
      }));
      setVideos(mappedVideos);
    } catch (err: unknown) {
      setErrorVideos(err instanceof Error ? err.message : "Failed to fetch videos.");
    } finally {
      setLoadingVideos(false);
    }
  }, []);

  const fetchAuditLogs = useCallback(async () => {
    setLoadingAuditLogs(true);
    setErrorAuditLogs(null);
    try {
      const response = await mediaApi.fetchAuditLogs();
      const mappedLogs: AuditEntry[] = response.results.map((raw) => {
        const actionStr = raw.action.charAt(0).toUpperCase() + raw.action.slice(1);

        let targetMedia = "Unknown Media";
        let targetId = "N/A";

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const changes: any = raw.changes || {};

        if (raw.artifact) {
            targetMedia = `Artifact #${raw.artifact}`;
            targetId = String(raw.artifact);
        } else if (changes.object_type === "VideoMetadata") {
            targetMedia = changes.file_name ? `${changes.file_name}` : "Unknown";
            targetId = changes.object_id ? String(changes.object_id) : "N/A";
        }

        return {
          id: String(raw.id),
          action: actionStr as AuditAction,
          actor: raw.user?.username || "System",
          targetMedia,
          targetId,
          mission: raw.mission ? `MSN-${raw.mission}` : "Global",
          timestamp: new Date(raw.created_at).toLocaleString(),
          result: raw.action === "denied" ? "Denied" : "Success",
        };
      });
      setAuditLogs(mappedLogs);
    } catch (err: unknown) {
      setErrorAuditLogs(err instanceof Error ? err.message : "Failed to fetch audit logs.");
    } finally {
      setLoadingAuditLogs(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchDependencies();
    void fetchVideos();
    void fetchAuditLogs();
  }, [fetchDependencies, fetchVideos, fetchAuditLogs]);

  // Polling for videos in uploading state
  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval>;
    const hasUploading = videos.some((v) => v.status === "uploading");

    if (hasUploading) {
      intervalId = setInterval(() => {
        void fetchVideos();
        void fetchDependencies();
        void fetchAuditLogs();
      }, 3000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [videos, fetchVideos, fetchDependencies, fetchAuditLogs]);

  const uploadVideo = async (
    file: File,
    metadata: { title: string; missionId: string; droneId: string }
  ) => {
    const tempId = `temp-${Date.now()}`;
    const tempVideo: Video = {
      id: tempId,
      title: metadata.title || file.name,
      status: "uploading",
      duration: "--:--",
      missionId: metadata.missionId,
      missionName: `Mission ${metadata.missionId}`,
      droneId: metadata.droneId,
      droneName: `Drone ${metadata.droneId}`,
      uploadedBy: "You",
      uploadedAt: new Date().toLocaleString(),
      fileSize: formatBytes(file.size),
      checksum: "N/A",
      url: "",
      fileName: file.name,
      progress: 0,
    };

    setActiveUploads((prev) => ({ ...prev, [tempId]: tempVideo }));

    // For the demo: Simulated gradual progress
    let currentProgress = 0;
    const progressInterval = setInterval(() => {
      currentProgress += Math.floor(Math.random() * 8) + 4; // Add 4-11% every 300ms
      if (currentProgress > 95) currentProgress = 95;

      setActiveUploads((prev) => {
        if (!prev[tempId]) return prev;
        return { ...prev, [tempId]: { ...prev[tempId], progress: currentProgress } };
      });

      if (currentProgress === 95) {
        clearInterval(progressInterval);
      }
    }, 300);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("mission", metadata.missionId);
    formData.append("drone", metadata.droneId);
    if (metadata.title) {
      formData.append("file_name", metadata.title);
    }

    try {
      await mediaApi.uploadVideo(formData);
    } finally {
      clearInterval(progressInterval);
      setActiveUploads((prev) => {
        const next = { ...prev };
        delete next[tempId];
        return next;
      });
      void fetchVideos();
      void fetchDependencies();
      void fetchAuditLogs();
    }
  };

  const deleteVideo = async (id: string) => {
    await mediaApi.deleteVideo(id);
  };



  const mergedVideos = useMemo(() => {
    return [...Object.values(activeUploads), ...videos];
  }, [activeUploads, videos]);

  return {
    videos: mergedVideos,
    auditLogs,
    loadingVideos,
    loadingAuditLogs,
    errorVideos,
    errorAuditLogs,
    fetchVideos,
    fetchAuditLogs,
    uploadVideo,
    deleteVideo,
    missionsList,
    dronesList,
    stats,
  };
}
