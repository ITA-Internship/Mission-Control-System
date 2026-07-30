import { useState, useRef } from "react";
import {
  LayoutDashboard, Map, Radio, Film, Users, BarChart3, Settings,
  Search, Upload, X, Play, AlertTriangle, CheckCircle, Loader2,
  ChevronDown, ChevronUp, ChevronLeft, ChevronRight,
  Download, Trash2, Pencil, Bell, LogOut, Shield,
  ArrowUpDown, FileVideo, RotateCw, Lock,
} from "lucide-react";

/* ──────────────────────────────────────────────────────
   Types
────────────────────────────────────────────────────── */
type VideoStatus = "ready" | "uploading" | "failed";
type AuditAction = "View" | "Download" | "Upload" | "Update" | "Delete" | "Denied";
type Tab = "videos" | "audit";
type UploadState = "idle" | "dragging" | "uploading" | "success" | "error";

/* ──────────────────────────────────────────────────────
   Data
────────────────────────────────────────────────────── */
const MISSIONS = [
  { id: "M-2401", name: "Operation Sandstorm" },
  { id: "M-2398", name: "Recon Delta" },
  { id: "M-2385", name: "Sentinel Watch" },
  { id: "M-2372", name: "Operation Ironclad" },
];

const DRONES = [
  { id: "DRN-047", name: "Falcon-7", missionId: "M-2401" },
  { id: "DRN-051", name: "Raptor-3", missionId: "M-2401" },
  { id: "DRN-039", name: "Shadow-12", missionId: "M-2398" },
  { id: "DRN-062", name: "Ghost-9", missionId: "M-2398" },
  { id: "DRN-028", name: "Eagle-4", missionId: "M-2385" },
];

interface Video {
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
  thumbnail: string;
  fileSize: string;
  checksum: string;
  progress?: number;
  errorMsg?: string;
}

const VIDEOS: Video[] = [
  {
    id: "VID-8841",
    title: "Perimeter Sweep — Sector 7 North",
    status: "ready",
    duration: "14:22",
    missionId: "M-2401",
    missionName: "Operation Sandstorm",
    droneId: "DRN-047",
    droneName: "Falcon-7",
    uploadedBy: "Sgt. R. Vance",
    uploadedAt: "2024-07-28 09:14",
    thumbnail: "https://images.unsplash.com/photo-1473968512647-3e447244af8f?w=480&h=270&fit=crop&auto=format",
    fileSize: "2.4 GB",
    checksum: "sha256:a3f1e9c4b2d876014e58",
  },
  {
    id: "VID-8839",
    title: "Grid Search Alpha — Eastern Ridge",
    status: "ready",
    duration: "08:47",
    missionId: "M-2401",
    missionName: "Operation Sandstorm",
    droneId: "DRN-051",
    droneName: "Raptor-3",
    uploadedBy: "Lt. K. Osei",
    uploadedAt: "2024-07-28 08:02",
    thumbnail: "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=480&h=270&fit=crop&auto=format",
    fileSize: "1.8 GB",
    checksum: "sha256:7cb29e4f81a30d526c91",
  },
  {
    id: "VID-8835",
    title: "Night Overwatch — FOB Alpha",
    status: "uploading",
    duration: "32:10",
    missionId: "M-2398",
    missionName: "Recon Delta",
    droneId: "DRN-039",
    droneName: "Shadow-12",
    uploadedBy: "Cpl. M. Adeyemi",
    uploadedAt: "2024-07-28 07:45",
    thumbnail: "https://images.unsplash.com/photo-1488229297570-58520851e868?w=480&h=270&fit=crop&auto=format",
    fileSize: "6.1 GB",
    checksum: "—",
    progress: 68,
  },
  {
    id: "VID-8831",
    title: "IED Route Assessment — Highway 9",
    status: "failed",
    duration: "—",
    missionId: "M-2398",
    missionName: "Recon Delta",
    droneId: "DRN-062",
    droneName: "Ghost-9",
    uploadedBy: "Sgt. T. Brandt",
    uploadedAt: "2024-07-27 23:58",
    thumbnail: "https://images.unsplash.com/photo-1516912481808-3406841bd33c?w=480&h=270&fit=crop&auto=format",
    fileSize: "—",
    checksum: "—",
    errorMsg: "Connection lost during transfer",
  },
  {
    id: "VID-8820",
    title: "Supply Route Reconnaissance",
    status: "ready",
    duration: "21:05",
    missionId: "M-2385",
    missionName: "Sentinel Watch",
    droneId: "DRN-028",
    droneName: "Eagle-4",
    uploadedBy: "Lt. K. Osei",
    uploadedAt: "2024-07-26 15:30",
    thumbnail: "https://images.unsplash.com/photo-1470770903676-69b98201ea1c?w=480&h=270&fit=crop&auto=format",
    fileSize: "3.9 GB",
    checksum: "sha256:e4a17c9b53f02d689c3a",
  },
  {
    id: "VID-8815",
    title: "Hostile Vehicle Tracking — Zone B",
    status: "ready",
    duration: "09:33",
    missionId: "M-2385",
    missionName: "Sentinel Watch",
    droneId: "DRN-028",
    droneName: "Eagle-4",
    uploadedBy: "Maj. S. Holbrook",
    uploadedAt: "2024-07-25 11:22",
    thumbnail: "https://images.unsplash.com/photo-1504333638930-c8787321eee0?w=480&h=270&fit=crop&auto=format",
    fileSize: "1.7 GB",
    checksum: "sha256:3dc85ae72b419f01f07b",
  },
  {
    id: "VID-8809",
    title: "Mountainous Terrain Mapping",
    status: "ready",
    duration: "44:17",
    missionId: "M-2372",
    missionName: "Operation Ironclad",
    droneId: "DRN-047",
    droneName: "Falcon-7",
    uploadedBy: "Sgt. R. Vance",
    uploadedAt: "2024-07-24 08:55",
    thumbnail: "https://images.unsplash.com/photo-1519583272095-6433daf26b6e?w=480&h=270&fit=crop&auto=format",
    fileSize: "8.2 GB",
    checksum: "sha256:9f2d1a4e7c583b20e1d4",
  },
];

interface AuditEntry {
  id: string;
  action: AuditAction;
  actor: string;
  targetMedia: string;
  targetId: string;
  mission: string;
  timestamp: string;
  result: "Success" | "Denied" | "Failed";
}

const AUDIT_LOG: AuditEntry[] = [
  { id: "AUD-4421", action: "View", actor: "Lt. K. Osei", targetMedia: "Perimeter Sweep — Sector 7 North", targetId: "VID-8841", mission: "Operation Sandstorm", timestamp: "2024-07-28 09:44:12", result: "Success" },
  { id: "AUD-4420", action: "Download", actor: "Maj. S. Holbrook", targetMedia: "Grid Search Alpha — Eastern Ridge", targetId: "VID-8839", mission: "Operation Sandstorm", timestamp: "2024-07-28 09:31:07", result: "Success" },
  { id: "AUD-4419", action: "Upload", actor: "Cpl. M. Adeyemi", targetMedia: "Night Overwatch — FOB Alpha", targetId: "VID-8835", mission: "Recon Delta", timestamp: "2024-07-28 07:45:00", result: "Success" },
  { id: "AUD-4418", action: "View", actor: "Pvt. D. Carver", targetMedia: "Hostile Vehicle Tracking — Zone B", targetId: "VID-8815", mission: "Sentinel Watch", timestamp: "2024-07-28 07:12:34", result: "Denied" },
  { id: "AUD-4417", action: "Delete", actor: "Maj. S. Holbrook", targetMedia: "IED Route Assessment — Highway 9", targetId: "VID-8831", mission: "Recon Delta", timestamp: "2024-07-28 01:08:19", result: "Success" },
  { id: "AUD-4416", action: "Download", actor: "Sgt. R. Vance", targetMedia: "Supply Route Reconnaissance", targetId: "VID-8820", mission: "Sentinel Watch", timestamp: "2024-07-27 22:40:55", result: "Success" },
  { id: "AUD-4415", action: "Update", actor: "Lt. K. Osei", targetMedia: "Mountainous Terrain Mapping", targetId: "VID-8809", mission: "Operation Ironclad", timestamp: "2024-07-27 18:22:01", result: "Success" },
  { id: "AUD-4414", action: "View", actor: "Sgt. T. Brandt", targetMedia: "Grid Search Alpha — Eastern Ridge", targetId: "VID-8839", mission: "Operation Sandstorm", timestamp: "2024-07-27 16:05:47", result: "Success" },
  { id: "AUD-4413", action: "Upload", actor: "Sgt. T. Brandt", targetMedia: "IED Route Assessment — Highway 9", targetId: "VID-8831", mission: "Recon Delta", timestamp: "2024-07-27 23:58:00", result: "Failed" },
  { id: "AUD-4412", action: "Denied", actor: "Pvt. D. Carver", targetMedia: "Night Overwatch — FOB Alpha", targetId: "VID-8835", mission: "Recon Delta", timestamp: "2024-07-27 14:33:20", result: "Denied" },
  { id: "AUD-4411", action: "View", actor: "Cpl. M. Adeyemi", targetMedia: "Supply Route Reconnaissance", targetId: "VID-8820", mission: "Sentinel Watch", timestamp: "2024-07-27 11:15:08", result: "Success" },
  { id: "AUD-4410", action: "Download", actor: "Maj. S. Holbrook", targetMedia: "Mountainous Terrain Mapping", targetId: "VID-8809", mission: "Operation Ironclad", timestamp: "2024-07-27 09:48:30", result: "Success" },
];

/* ──────────────────────────────────────────────────────
   Shared atoms
────────────────────────────────────────────────────── */
function StatusPill({ status }: { status: VideoStatus }) {
  const map = {
    ready: { label: "Ready", dot: "bg-emerald-400", wrap: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
    uploading: { label: "Uploading", dot: "bg-amber-400", wrap: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
    failed: { label: "Failed", dot: "bg-red-400", wrap: "bg-red-500/10 text-red-400 border-red-500/20" },
  }[status];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border ${map.wrap}`}>
      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${map.dot} ${status === "uploading" ? "animate-pulse" : ""}`} />
      {map.label}
    </span>
  );
}

function AuditActionPill({ action }: { action: AuditAction }) {
  const map: Record<AuditAction, string> = {
    View: "bg-[#8A94A6]/10 text-[#8A94A6] border-[#8A94A6]/15",
    Download: "bg-[#8A94A6]/10 text-[#8A94A6] border-[#8A94A6]/15",
    Upload: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    Update: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    Delete: "bg-red-500/10 text-red-400 border-red-500/20",
    Denied: "bg-red-500/15 text-red-400 border-red-500/25 font-semibold",
  };
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${map[action]}`}>
      {action === "Denied" && <Lock size={9} />}
      {action}
    </span>
  );
}

function ResultPill({ result }: { result: AuditEntry["result"] }) {
  const map = {
    Success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    Denied: "bg-red-500/15 text-red-400 border-red-500/25 font-semibold",
    Failed: "bg-red-500/15 text-red-400 border-red-500/25",
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${map[result]}`}>
      {result}
    </span>
  );
}

/* ──────────────────────────────────────────────────────
   Video Card
────────────────────────────────────────────────────── */
function VideoCard({ video, onClick }: { video: Video; onClick: () => void }) {
  const isReady = video.status === "ready";
  const isUploading = video.status === "uploading";
  const isFailed = video.status === "failed";

  return (
    <div
      onClick={isReady ? onClick : undefined}
      className={`group bg-[#161D26] border rounded-xl overflow-hidden transition-all duration-200 ${
        isFailed
          ? "border-red-500/25 cursor-default"
          : isUploading
          ? "border-amber-500/20 cursor-default"
          : "border-[#1E2733] hover:border-amber-400/35 hover:shadow-xl hover:shadow-black/40 cursor-pointer"
      }`}
    >
      {/* Thumbnail */}
      <div className="relative aspect-video bg-[#0E141B] overflow-hidden">
        <img
          src={video.thumbnail}
          alt={video.title}
          className={`w-full h-full object-cover transition-all duration-300 ${
            isFailed ? "opacity-15 grayscale" : isUploading ? "opacity-25" : "opacity-55 group-hover:opacity-75"
          }`}
        />

        {/* Ready: play button on hover */}
        {isReady && (
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <div className="w-12 h-12 rounded-full bg-amber-400/20 border border-amber-400/50 backdrop-blur-sm flex items-center justify-center">
              <Play size={20} fill="currentColor" className="text-amber-400 ml-0.5" />
            </div>
          </div>
        )}

        {/* Uploading: spinner + progress */}
        {isUploading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2.5 px-5">
            <Loader2 size={22} className="text-amber-400 animate-spin" />
            <div className="w-full h-1 bg-[#1E2733] rounded-full overflow-hidden">
              <div
                className="h-full bg-amber-400 rounded-full transition-all"
                style={{ width: `${video.progress}%` }}
              />
            </div>
            <span className="text-xs text-amber-400 font-mono tabular-nums">{video.progress}%</span>
          </div>
        )}

        {/* Failed: error overlay */}
        {isFailed && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
            <div className="w-10 h-10 rounded-full bg-red-500/15 border border-red-500/30 flex items-center justify-center">
              <AlertTriangle size={18} className="text-red-400" />
            </div>
            <span className="text-xs text-red-400 font-medium">Transfer Failed</span>
          </div>
        )}

        {/* Duration badge */}
        {isReady && (
          <div className="absolute bottom-2 right-2 bg-black/75 backdrop-blur-sm px-1.5 py-0.5 rounded text-xs font-mono text-white">
            {video.duration}
          </div>
        )}

        {/* Uploading duration */}
        {isUploading && (
          <div className="absolute top-2 right-2 bg-black/75 backdrop-blur-sm px-1.5 py-0.5 rounded text-xs font-mono text-amber-400">
            {video.fileSize}
          </div>
        )}
      </div>

      {/* Body */}
      <div className="p-3.5 space-y-2.5">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-[13px] font-medium text-[#E6EAF0] leading-snug line-clamp-2 flex-1">
            {video.title}
          </h3>
          <StatusPill status={video.status} />
        </div>

        {isFailed && video.errorMsg && (
          <p className="text-xs text-red-400 bg-red-500/8 border border-red-500/15 rounded-lg px-2.5 py-1.5">
            {video.errorMsg}
          </p>
        )}

        <div className="flex flex-wrap gap-1.5">
          <span className="text-xs px-2 py-0.5 rounded-md bg-[#1A2232] text-[#8A94A6] border border-[#1E2733] font-mono">
            {video.missionId}
          </span>
          <span className="text-xs px-2 py-0.5 rounded-md bg-[#1A2232] text-[#8A94A6] border border-[#1E2733] font-mono">
            {video.droneId}
          </span>
        </div>

        <div className="flex items-center justify-between pt-0.5 border-t border-[#1E2733]/60">
          <span className="text-xs text-[#8A94A6] truncate">{video.uploadedBy}</span>
          <span className="text-xs text-[#8A94A6] font-mono flex-shrink-0 ml-2">
            {video.uploadedAt.split(" ")[0]}
          </span>
        </div>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────────────
   Video Player Modal
────────────────────────────────────────────────────── */
function VideoPlayerModal({ video, onClose }: { video: Video; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-5xl bg-[#161D26] border border-[#1E2733] rounded-xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#1E2733]">
          <div className="flex items-center gap-3 min-w-0">
            <Film size={15} className="text-amber-400 flex-shrink-0" />
            <span className="text-sm font-semibold text-[#E6EAF0] truncate">{video.title}</span>
            <StatusPill status={video.status} />
            <span className="text-xs text-[#8A94A6] font-mono flex-shrink-0 hidden sm:inline">{video.id}</span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-white/5 text-[#8A94A6] hover:text-[#E6EAF0] transition-colors flex-shrink-0 ml-3"
          >
            <X size={15} />
          </button>
        </div>

        <div className="flex flex-col lg:flex-row">
          {/* Player column */}
          <div className="flex-1 min-w-0">
            {/* Video area */}
            <div className="relative aspect-video bg-[#0E141B] flex items-center justify-center group cursor-pointer">
              <img
                src={video.thumbnail}
                alt={video.title}
                className="w-full h-full object-cover opacity-60"
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-16 h-16 rounded-full bg-amber-400/20 border border-amber-400/40 backdrop-blur-sm flex items-center justify-center group-hover:bg-amber-400/30 group-hover:scale-105 transition-all duration-200">
                  <Play size={26} fill="currentColor" className="text-amber-400 ml-1" />
                </div>
              </div>
              <div className="absolute bottom-3 right-3 bg-black/75 backdrop-blur-sm px-2 py-0.5 rounded text-xs font-mono text-white">
                {video.duration}
              </div>
            </div>

            {/* Scrubber controls */}
            <div className="bg-[#0E141B] px-5 py-3.5 space-y-2">
              <div className="group/bar flex items-center gap-3">
                <span className="text-xs text-[#8A94A6] font-mono tabular-nums w-10 text-right flex-shrink-0">04:47</span>
                <div className="flex-1 h-1 bg-[#1E2733] rounded-full cursor-pointer relative">
                  <div className="h-full bg-amber-400 rounded-full" style={{ width: "33%" }} />
                  <div className="absolute left-[33%] top-1/2 -translate-y-1/2 -translate-x-1/2 w-2.5 h-2.5 rounded-full bg-amber-400 shadow-sm opacity-0 group-hover/bar:opacity-100 transition-opacity" />
                </div>
                <span className="text-xs text-[#8A94A6] font-mono tabular-nums w-10 flex-shrink-0">{video.duration}</span>
              </div>
            </div>
          </div>

          {/* Metadata panel */}
          <div className="lg:w-72 xl:w-80 flex-shrink-0 border-t lg:border-t-0 lg:border-l border-[#1E2733] flex flex-col">
            <div className="p-5 flex-1 overflow-y-auto space-y-5">
              {/* Metadata */}
              <section>
                <h4 className="text-[10px] font-semibold text-[#8A94A6] uppercase tracking-[0.12em] mb-3">
                  Mission Intelligence
                </h4>
                <dl className="space-y-3">
                  {[
                    { label: "Mission", value: `${video.missionId} — ${video.missionName}` },
                    { label: "Drone Asset", value: `${video.droneId} / ${video.droneName}` },
                    { label: "Uploaded By", value: video.uploadedBy },
                    { label: "Upload Date", value: video.uploadedAt },
                    { label: "Duration", value: video.duration },
                    { label: "File Size", value: video.fileSize },
                  ].map(({ label, value }) => (
                    <div key={label}>
                      <dt className="text-xs text-[#8A94A6] mb-0.5">{label}</dt>
                      <dd className="text-sm text-[#E6EAF0]">{value}</dd>
                    </div>
                  ))}
                </dl>
              </section>

              {/* Checksum */}
              <section className="border-t border-[#1E2733] pt-4">
                <h4 className="text-[10px] font-semibold text-[#8A94A6] uppercase tracking-[0.12em] mb-2">
                  Integrity
                </h4>
                <div className="bg-[#0E141B] rounded-lg px-3 py-2.5">
                  <p className="text-[10px] text-[#8A94A6] mb-1 uppercase tracking-wider">SHA-256</p>
                  <p className="text-xs text-[#8A94A6] font-mono break-all leading-relaxed">
                    {video.checksum}
                  </p>
                </div>
              </section>
            </div>

            {/* Actions */}
            <div className="p-4 border-t border-[#1E2733] space-y-1.5">
              <button className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg bg-amber-400/10 hover:bg-amber-400/15 text-amber-400 text-sm font-medium transition-colors">
                <Download size={14} /> Download Video
              </button>
              <button className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg hover:bg-white/[0.04] text-[#8A94A6] hover:text-[#E6EAF0] text-sm transition-colors">
                <Pencil size={14} /> Edit Metadata
              </button>
              <button className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg hover:bg-red-500/8 text-[#8A94A6] hover:text-red-400 text-sm transition-colors">
                <Trash2 size={14} /> Delete
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────────────
   Upload Modal
────────────────────────────────────────────────────── */
function UploadModal({ onClose }: { onClose: () => void }) {
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [progress, setProgress] = useState(0);
  const [selectedMission, setSelectedMission] = useState("");
  const [selectedDrone, setSelectedDrone] = useState("");
  const [title, setTitle] = useState("");
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const availableDrones = DRONES.filter((d) => d.missionId === selectedMission);
  const canSubmit = title.trim() && selectedMission && selectedDrone && uploadState === "idle";

  function simulateUpload() {
    if (!canSubmit) return;
    setUploadState("uploading");
    setProgress(0);
    intervalRef.current = setInterval(() => {
      setProgress((p) => {
        if (p >= 100) {
          clearInterval(intervalRef.current!);
          setUploadState("success");
          return 100;
        }
        return Math.min(100, p + 4);
      });
    }, 100);
  }

  function resetUpload() {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setUploadState("idle");
    setProgress(0);
  }

  const isDragging = uploadState === "dragging";
  const showDropzone = uploadState === "idle" || uploadState === "dragging";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md bg-[#161D26] border border-[#1E2733] rounded-xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#1E2733]">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-md bg-amber-400/15 flex items-center justify-center">
              <Upload size={12} className="text-amber-400" />
            </div>
            <span className="text-sm font-semibold text-[#E6EAF0]">Upload Video</span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-white/5 text-[#8A94A6] hover:text-[#E6EAF0] transition-colors"
          >
            <X size={14} />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* Dropzone / Upload state */}
          {showDropzone && (
            <div
              onDragOver={(e) => { e.preventDefault(); setUploadState("dragging"); }}
              onDragLeave={() => setUploadState("idle")}
              onDrop={(e) => { e.preventDefault(); setUploadState("idle"); }}
              className={`border-2 border-dashed rounded-xl py-8 flex flex-col items-center gap-3 transition-all cursor-pointer select-none ${
                isDragging
                  ? "border-amber-400 bg-amber-400/5"
                  : "border-[#1E2733] hover:border-[#2A3444] hover:bg-white/[0.01]"
              }`}
            >
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                  isDragging ? "bg-amber-400/20 scale-110" : "bg-[#1A2232]"
                }`}
              >
                <FileVideo size={22} className={isDragging ? "text-amber-400" : "text-[#8A94A6]"} />
              </div>
              <div className="text-center">
                <p className={`text-sm font-medium transition-colors ${isDragging ? "text-amber-400" : "text-[#E6EAF0]"}`}>
                  {isDragging ? "Release to add file" : "Drag video file here"}
                </p>
                <p className="text-xs text-[#8A94A6] mt-0.5">MP4, MOV, AVI · max 20 GB</p>
              </div>
              {!isDragging && (
                <button className="px-3.5 py-1.5 rounded-lg bg-[#1A2232] hover:bg-[#202D3E] text-sm text-[#E6EAF0] border border-[#1E2733] transition-colors">
                  Browse files
                </button>
              )}
            </div>
          )}

          {uploadState === "uploading" && (
            <div className="border border-amber-500/20 bg-amber-500/5 rounded-xl p-4 space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-amber-400/15 flex items-center justify-center flex-shrink-0">
                  <Loader2 size={16} className="text-amber-400 animate-spin" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[#E6EAF0] truncate">{title || "video-file.mp4"}</p>
                  <p className="text-xs text-[#8A94A6] font-mono">{progress}% · uploading…</p>
                </div>
              </div>
              <div className="space-y-1">
                <div className="h-1.5 bg-[#1A2232] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-amber-400 rounded-full transition-all duration-150"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            </div>
          )}

          {uploadState === "success" && (
            <div className="border border-emerald-500/20 bg-emerald-500/5 rounded-xl p-4 flex items-center gap-3">
              <CheckCircle size={20} className="text-emerald-400 flex-shrink-0" />
              <div>
                <p className="text-sm font-semibold text-emerald-400">Upload complete</p>
                <p className="text-xs text-[#8A94A6] mt-0.5">Processing — video will be ready shortly.</p>
              </div>
            </div>
          )}

          {uploadState === "error" && (
            <div className="border border-red-500/20 bg-red-500/5 rounded-xl p-4 flex items-center gap-3">
              <AlertTriangle size={18} className="text-red-400 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-red-400">Upload failed</p>
                <p className="text-xs text-[#8A94A6] mt-0.5">Connection lost. Check link and retry.</p>
              </div>
            </div>
          )}

          {/* Form */}
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-[#8A94A6] mb-1.5 uppercase tracking-wider">
                Title
              </label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={uploadState === "uploading" || uploadState === "success"}
                placeholder="e.g. Sector 9 Night Sweep"
                className="w-full px-3 py-2 rounded-lg bg-[#0E141B] border border-[#1E2733] text-sm text-[#E6EAF0] placeholder:text-[#3A4558] focus:outline-none focus:border-amber-400/50 transition-colors disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#8A94A6] mb-1.5 uppercase tracking-wider">
                Mission
              </label>
              <div className="relative">
                <select
                  value={selectedMission}
                  onChange={(e) => { setSelectedMission(e.target.value); setSelectedDrone(""); }}
                  disabled={uploadState === "uploading" || uploadState === "success"}
                  className="w-full px-3 pr-8 py-2 rounded-lg bg-[#0E141B] border border-[#1E2733] text-sm text-[#E6EAF0] focus:outline-none focus:border-amber-400/50 transition-colors appearance-none disabled:opacity-50"
                >
                  <option value="">Select mission…</option>
                  {MISSIONS.map((m) => (
                    <option key={m.id} value={m.id}>{m.id} — {m.name}</option>
                  ))}
                </select>
                <ChevronDown size={13} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#8A94A6] pointer-events-none" />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-[#8A94A6] mb-1.5 uppercase tracking-wider">
                Drone <span className="text-[#3A4558] normal-case tracking-normal">(must be assigned to mission)</span>
              </label>
              <div className="relative">
                <select
                  value={selectedDrone}
                  onChange={(e) => setSelectedDrone(e.target.value)}
                  disabled={!selectedMission || uploadState === "uploading" || uploadState === "success"}
                  className="w-full px-3 pr-8 py-2 rounded-lg bg-[#0E141B] border border-[#1E2733] text-sm text-[#E6EAF0] focus:outline-none focus:border-amber-400/50 transition-colors appearance-none disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <option value="">
                    {selectedMission ? (availableDrones.length ? "Select drone…" : "No drones assigned") : "Select mission first"}
                  </option>
                  {availableDrones.map((d) => (
                    <option key={d.id} value={d.id}>{d.id} — {d.name}</option>
                  ))}
                </select>
                <ChevronDown size={13} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#8A94A6] pointer-events-none" />
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 pb-5 flex items-center justify-end gap-2.5">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/5 transition-colors"
          >
            {uploadState === "success" ? "Close" : "Cancel"}
          </button>
          {uploadState === "success" ? null : uploadState === "error" ? (
            <button
              onClick={resetUpload}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-amber-400 hover:bg-amber-300 text-[#0B0F14] text-sm font-semibold transition-colors"
            >
              <RotateCw size={13} /> Retry
            </button>
          ) : (
            <button
              onClick={simulateUpload}
              disabled={!canSubmit}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-amber-400 hover:bg-amber-300 text-[#0B0F14] text-sm font-semibold transition-colors disabled:opacity-35 disabled:cursor-not-allowed"
            >
              <Upload size={13} /> Upload
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────────────
   Video Filter Bar
────────────────────────────────────────────────────── */
function VideoFilterBar({
  search, onSearch,
  mission, onMission,
  drone, onDrone,
  status, onStatus,
}: {
  search: string; onSearch: (v: string) => void;
  mission: string; onMission: (v: string) => void;
  drone: string; onDrone: (v: string) => void;
  status: string; onStatus: (v: string) => void;
}) {
  const chips = [
    mission && { label: mission, clear: () => onMission("") },
    drone && { label: drone, clear: () => onDrone("") },
    status && { label: status.charAt(0).toUpperCase() + status.slice(1), clear: () => onStatus("") },
  ].filter(Boolean) as { label: string; clear: () => void }[];

  return (
    <div className="space-y-2.5">
      <div className="flex flex-wrap items-center gap-2">
        {/* Search */}
        <div className="relative flex-1 min-w-[180px] max-w-xs">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8A94A6]" />
          <input
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            placeholder="Search videos…"
            className="w-full pl-8 pr-3 py-2 rounded-lg bg-[#161D26] border border-[#1E2733] text-sm text-[#E6EAF0] placeholder:text-[#3A4558] focus:outline-none focus:border-amber-400/40 transition-colors"
          />
        </div>

        {/* Mission filter */}
        <div className="relative">
          <select
            value={mission}
            onChange={(e) => onMission(e.target.value)}
            className="pl-3 pr-7 py-2 rounded-lg bg-[#161D26] border border-[#1E2733] text-sm text-[#8A94A6] focus:outline-none focus:border-amber-400/40 transition-colors appearance-none cursor-pointer"
          >
            <option value="">Mission</option>
            {MISSIONS.map((m) => <option key={m.id} value={m.id}>{m.id}</option>)}
          </select>
          <ChevronDown size={12} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#8A94A6] pointer-events-none" />
        </div>

        {/* Drone filter */}
        <div className="relative">
          <select
            value={drone}
            onChange={(e) => onDrone(e.target.value)}
            className="pl-3 pr-7 py-2 rounded-lg bg-[#161D26] border border-[#1E2733] text-sm text-[#8A94A6] focus:outline-none focus:border-amber-400/40 transition-colors appearance-none cursor-pointer"
          >
            <option value="">Drone</option>
            {DRONES.map((d) => <option key={d.id} value={d.id}>{d.id}</option>)}
          </select>
          <ChevronDown size={12} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#8A94A6] pointer-events-none" />
        </div>

        {/* Status filter */}
        <div className="relative">
          <select
            value={status}
            onChange={(e) => onStatus(e.target.value)}
            className="pl-3 pr-7 py-2 rounded-lg bg-[#161D26] border border-[#1E2733] text-sm text-[#8A94A6] focus:outline-none focus:border-amber-400/40 transition-colors appearance-none cursor-pointer"
          >
            <option value="">Status</option>
            {["ready", "uploading", "failed"].map((s) => (
              <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
            ))}
          </select>
          <ChevronDown size={12} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#8A94A6] pointer-events-none" />
        </div>
      </div>

      {/* Active filter chips */}
      {chips.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {chips.map((chip) => (
            <span
              key={chip.label}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-400/10 text-amber-400 text-xs border border-amber-400/20"
            >
              {chip.label}
              <button onClick={chip.clear} className="hover:text-amber-200 transition-colors">
                <X size={10} />
              </button>
            </span>
          ))}
          <button
            onClick={() => { onMission(""); onDrone(""); onStatus(""); onSearch(""); }}
            className="text-xs text-[#8A94A6] hover:text-[#E6EAF0] transition-colors"
          >
            Clear all
          </button>
        </div>
      )}
    </div>
  );
}

/* ──────────────────────────────────────────────────────
   Audit Log Tab
────────────────────────────────────────────────────── */
function AuditLogTab() {
  const [actionFilter, setActionFilter] = useState("");
  const [actorFilter, setActorFilter] = useState("");
  const [sortCol, setSortCol] = useState<keyof AuditEntry>("timestamp");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 8;

  function toggleSort(col: keyof AuditEntry) {
    if (sortCol === col) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortCol(col); setSortDir("desc"); }
    setPage(0);
  }

  const actors = Array.from(new Set(AUDIT_LOG.map((e) => e.actor))).sort();

  const filtered = AUDIT_LOG.filter(
    (e) =>
      (!actionFilter || e.action === actionFilter) &&
      (!actorFilter || e.actor === actorFilter)
  );

  const sorted = [...filtered].sort((a, b) => {
    const av = a[sortCol] as string;
    const bv = b[sortCol] as string;
    return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
  });

  const total = sorted.length;
  const paged = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const totalPages = Math.ceil(total / PAGE_SIZE);

  type ColDef = { key: keyof AuditEntry; label: string };
  const COLS: ColDef[] = [
    { key: "action", label: "Action" },
    { key: "actor", label: "Actor" },
    { key: "targetMedia", label: "Media" },
    { key: "mission", label: "Mission" },
    { key: "timestamp", label: "Timestamp" },
    { key: "result", label: "Result" },
  ];

  function SortIcon({ col }: { col: keyof AuditEntry }) {
    if (sortCol !== col) return <ArrowUpDown size={11} className="text-[#3A4558]" />;
    return sortDir === "asc"
      ? <ChevronUp size={11} className="text-amber-400" />
      : <ChevronDown size={11} className="text-amber-400" />;
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <select
            value={actionFilter}
            onChange={(e) => { setActionFilter(e.target.value); setPage(0); }}
            className="pl-3 pr-7 py-2 rounded-lg bg-[#161D26] border border-[#1E2733] text-sm text-[#8A94A6] focus:outline-none focus:border-amber-400/40 transition-colors appearance-none cursor-pointer"
          >
            <option value="">All actions</option>
            {(["View", "Download", "Upload", "Update", "Delete", "Denied"] as AuditAction[]).map((a) => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
          <ChevronDown size={12} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#8A94A6] pointer-events-none" />
        </div>

        <div className="relative">
          <select
            value={actorFilter}
            onChange={(e) => { setActorFilter(e.target.value); setPage(0); }}
            className="pl-3 pr-7 py-2 rounded-lg bg-[#161D26] border border-[#1E2733] text-sm text-[#8A94A6] focus:outline-none focus:border-amber-400/40 transition-colors appearance-none cursor-pointer"
          >
            <option value="">All actors</option>
            {actors.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
          <ChevronDown size={12} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#8A94A6] pointer-events-none" />
        </div>

        <span className="text-xs text-[#8A94A6] ml-auto">
          {total} {total === 1 ? "entry" : "entries"}
        </span>
      </div>

      {/* Table */}
      <div className="bg-[#161D26] border border-[#1E2733] rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[780px] text-sm">
            <thead>
              <tr className="border-b border-[#1E2733]">
                {COLS.map((col) => (
                  <th
                    key={col.key}
                    onClick={() => toggleSort(col.key)}
                    className="px-4 py-3 text-left text-[10px] font-semibold text-[#8A94A6] uppercase tracking-[0.1em] cursor-pointer hover:text-[#E6EAF0] select-none group transition-colors"
                  >
                    <div className="flex items-center gap-1.5">
                      {col.label}
                      <SortIcon col={col.key} />
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {paged.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-sm text-[#8A94A6]">
                    No audit entries match the current filters.
                  </td>
                </tr>
              ) : paged.map((entry) => {
                const flagged = entry.action === "Denied" || entry.result === "Denied";
                return (
                  <tr
                    key={entry.id}
                    className={`border-b border-[#1E2733]/40 transition-colors ${
                      flagged
                        ? "bg-red-500/5 hover:bg-red-500/8"
                        : "hover:bg-white/[0.018]"
                    }`}
                  >
                    <td className="px-4 py-3">
                      <AuditActionPill action={entry.action} />
                    </td>
                    <td className="px-4 py-3 text-[#E6EAF0] text-sm">{entry.actor}</td>
                    <td className="px-4 py-3">
                      <div className="max-w-[200px]">
                        <p className="text-[#E6EAF0] text-sm truncate">{entry.targetMedia}</p>
                        <p className="text-xs text-[#8A94A6] font-mono mt-0.5">{entry.targetId}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-[#8A94A6] whitespace-nowrap">{entry.mission}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-[#8A94A6] font-mono whitespace-nowrap">{entry.timestamp}</span>
                    </td>
                    <td className="px-4 py-3">
                      <ResultPill result={entry.result} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-4 py-3 border-t border-[#1E2733] flex items-center justify-between">
            <span className="text-xs text-[#8A94A6]">
              {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} of {total}
            </span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="p-1.5 rounded-lg hover:bg-white/5 text-[#8A94A6] hover:text-[#E6EAF0] disabled:opacity-25 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft size={14} />
              </button>
              {Array.from({ length: totalPages }, (_, i) => (
                <button
                  key={i}
                  onClick={() => setPage(i)}
                  className={`w-7 h-7 rounded-lg text-xs font-medium transition-colors ${
                    i === page
                      ? "bg-amber-400/15 text-amber-400"
                      : "text-[#8A94A6] hover:bg-white/5 hover:text-[#E6EAF0]"
                  }`}
                >
                  {i + 1}
                </button>
              ))}
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="p-1.5 rounded-lg hover:bg-white/5 text-[#8A94A6] hover:text-[#E6EAF0] disabled:opacity-25 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────────────
   App Shell Nav items
────────────────────────────────────────────────────── */
const NAV = [
  { icon: LayoutDashboard, label: "Dashboard", active: false },
  { icon: Map, label: "Missions", active: false, badge: "3" },
  { icon: Radio, label: "Drone Fleet", active: false },
  { icon: Film, label: "Media Library", active: true },
  { icon: Users, label: "Personnel", active: false },
  { icon: BarChart3, label: "Analytics", active: false },
];

/* ──────────────────────────────────────────────────────
   App
────────────────────────────────────────────────────── */
export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("videos");
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const [showUpload, setShowUpload] = useState(false);

  // Video filter state
  const [search, setSearch] = useState("");
  const [missionFilter, setMissionFilter] = useState("");
  const [droneFilter, setDroneFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const filteredVideos = VIDEOS.filter((v) => {
    if (search && !v.title.toLowerCase().includes(search.toLowerCase()) && !v.id.includes(search)) return false;
    if (missionFilter && v.missionId !== missionFilter) return false;
    if (droneFilter && v.droneId !== droneFilter) return false;
    if (statusFilter && v.status !== statusFilter) return false;
    return true;
  });

  return (
    <div className="dark min-h-screen bg-[#0B0F14] flex overflow-hidden" style={{ fontFamily: "'IBM Plex Sans', system-ui, sans-serif" }}>

      {/* ── Sidebar ───────────────────────────────────── */}
      <aside className="w-56 flex-shrink-0 bg-[#0D1219] border-r border-[#1E2733] flex flex-col h-screen sticky top-0">

        {/* Logo */}
        <div className="px-4 py-4 border-b border-[#1E2733]">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-amber-400/15 border border-amber-400/25 flex items-center justify-center flex-shrink-0">
              <Shield size={13} className="text-amber-400" />
            </div>
            <div className="leading-none">
              <p className="text-[11px] font-bold text-[#E6EAF0] uppercase tracking-[0.15em]">Mission</p>
              <p className="text-[11px] font-bold text-amber-400 uppercase tracking-[0.15em] mt-0.5">Control</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-2.5 py-3 space-y-0.5 overflow-y-auto">
          <p className="text-[9px] font-semibold text-[#3A4558] uppercase tracking-[0.15em] px-3 pb-1.5 pt-1">
            Operations
          </p>
          {NAV.map(({ icon: Icon, label, active, badge }: { icon: React.ElementType; label: string; active: boolean; badge?: string }) => (
            <button
              key={label}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all ${
                active
                  ? "bg-amber-400/10 text-amber-400 border border-amber-400/15"
                  : "text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/[0.035] border border-transparent"
              }`}
            >
              <Icon size={14} />
              <span className="flex-1 text-left">{label}</span>
              {badge && (
                <span className={`text-[10px] font-bold px-1.5 rounded-full ${active ? "bg-amber-400/20 text-amber-400" : "bg-[#1A2232] text-[#8A94A6]"}`}>
                  {badge}
                </span>
              )}
              {active && <span className="w-1 h-1 rounded-full bg-amber-400 flex-shrink-0" />}
            </button>
          ))}

          <div className="pt-2">
            <p className="text-[9px] font-semibold text-[#3A4558] uppercase tracking-[0.15em] px-3 pb-1.5 pt-1">
              System
            </p>
            <button className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/[0.035] border border-transparent transition-all">
              <Settings size={14} /> Settings
            </button>
          </div>
        </nav>

        {/* User */}
        <div className="px-3 py-3 border-t border-[#1E2733]">
          <div className="flex items-center gap-2.5 px-1">
            <div className="w-7 h-7 rounded-full bg-amber-400/15 border border-amber-400/20 flex items-center justify-center flex-shrink-0">
              <span className="text-[10px] font-bold text-amber-400">SH</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-[#E6EAF0] truncate">Maj. S. Holbrook</p>
              <p className="text-[10px] text-[#8A94A6]">Admin · Clearance L4</p>
            </div>
            <button className="text-[#8A94A6] hover:text-[#E6EAF0] transition-colors p-0.5">
              <LogOut size={12} />
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main area ─────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">

        {/* Top bar */}
        <header className="h-12 border-b border-[#1E2733] flex items-center px-5 gap-4 flex-shrink-0 bg-[#0B0F14]">
          <nav className="flex items-center gap-1.5 text-xs flex-1">
            <span className="text-[#3A4558]">Mission Control</span>
            <span className="text-[#2A3444]">/</span>
            <span className="text-[#8A94A6]">Media Library</span>
          </nav>

          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/8 border border-emerald-500/15 px-2.5 py-1 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              3 Active Missions
            </div>
            <div className="hidden sm:flex items-center gap-1.5 text-xs text-[#8A94A6] bg-[#161D26] border border-[#1E2733] px-2.5 py-1 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              1 Uploading
            </div>
            <button className="relative p-1.5 rounded-lg hover:bg-white/5 text-[#8A94A6] hover:text-[#E6EAF0] transition-colors">
              <Bell size={14} />
              <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-amber-400" />
            </button>
          </div>
        </header>

        {/* Scrollable content */}
        <main className="flex-1 overflow-y-auto">
          <div className="px-6 py-6 space-y-5 max-w-[1600px]">

            {/* Page header */}
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-2xl font-semibold text-[#E6EAF0] tracking-tight">Media Library</h1>
                <p className="text-sm text-[#8A94A6] mt-0.5">
                  Mission footage · evidence vault · media audit trail
                </p>
              </div>
              <button
                onClick={() => setShowUpload(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-400 hover:bg-amber-300 text-[#0B0F14] text-sm font-semibold transition-colors flex-shrink-0"
              >
                <Upload size={13} /> Upload Video
              </button>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: "Total Videos", value: "7", sub: "across 4 missions" },
                { label: "Storage Used", value: "24.1 GB", sub: "of 500 GB allotted" },
                { label: "Uploading", value: "1", sub: "in progress", accent: true },
                { label: "Failed", value: "1", sub: "requires retry", warn: true },
              ].map(({ label, value, sub, accent, warn }) => (
                <div key={label} className={`bg-[#161D26] border rounded-xl px-4 py-3 ${warn ? "border-red-500/20" : accent ? "border-amber-500/20" : "border-[#1E2733]"}`}>
                  <p className={`text-xl font-semibold tabular-nums ${warn ? "text-red-400" : accent ? "text-amber-400" : "text-[#E6EAF0]"}`}>{value}</p>
                  <p className="text-xs font-medium text-[#E6EAF0] mt-0.5">{label}</p>
                  <p className="text-xs text-[#8A94A6]">{sub}</p>
                </div>
              ))}
            </div>

            {/* Tab bar */}
            <div className="flex items-center border-b border-[#1E2733] gap-1">
              {(["videos", "audit"] as Tab[]).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`relative px-4 py-2.5 text-sm font-medium transition-colors ${
                    activeTab === tab ? "text-amber-400" : "text-[#8A94A6] hover:text-[#E6EAF0]"
                  }`}
                >
                  <span className="flex items-center gap-2">
                    {tab === "videos" ? (
                      <>
                        <Film size={13} /> Videos
                        <span className={`text-[10px] font-bold px-1.5 rounded-full ${activeTab === tab ? "bg-amber-400/20 text-amber-400" : "bg-[#1A2232] text-[#8A94A6]"}`}>
                          {VIDEOS.length}
                        </span>
                      </>
                    ) : (
                      <>
                        <Shield size={13} /> Audit Log
                        <span className={`text-[10px] font-bold px-1.5 rounded-full ${activeTab === tab ? "bg-amber-400/20 text-amber-400" : "bg-[#1A2232] text-[#8A94A6]"}`}>
                          {AUDIT_LOG.length}
                        </span>
                      </>
                    )}
                  </span>
                  {activeTab === tab && (
                    <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-400 rounded-t-full" />
                  )}
                </button>
              ))}
            </div>

            {/* Videos tab */}
            {activeTab === "videos" && (
              <div className="space-y-4">
                <VideoFilterBar
                  search={search} onSearch={setSearch}
                  mission={missionFilter} onMission={setMissionFilter}
                  drone={droneFilter} onDrone={setDroneFilter}
                  status={statusFilter} onStatus={setStatusFilter}
                />

                {filteredVideos.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-20 gap-3">
                    <div className="w-14 h-14 rounded-full bg-[#161D26] border border-[#1E2733] flex items-center justify-center">
                      <Film size={22} className="text-[#3A4558]" />
                    </div>
                    <p className="text-sm font-medium text-[#8A94A6]">No videos match your filters</p>
                    <button
                      onClick={() => { setSearch(""); setMissionFilter(""); setDroneFilter(""); setStatusFilter(""); }}
                      className="text-xs text-amber-400 hover:text-amber-300 transition-colors"
                    >
                      Clear filters
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {filteredVideos.map((v) => (
                      <VideoCard key={v.id} video={v} onClick={() => setSelectedVideo(v)} />
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Audit log tab */}
            {activeTab === "audit" && <AuditLogTab />}
          </div>
        </main>
      </div>

      {/* Modals */}
      {selectedVideo && (
        <VideoPlayerModal video={selectedVideo} onClose={() => setSelectedVideo(null)} />
      )}
      {showUpload && (
        <UploadModal onClose={() => setShowUpload(false)} />
      )}
    </div>
  );
}
