import { useState } from "react";
import { Upload, Film, Shield, ChevronDown, Search, X } from "lucide-react";
import { useMediaLibrary, formatBytes } from "../hooks/useMediaLibrary";
import { VideoGrid } from "../components/VideoGrid";
import { AuditLogTable } from "../components/AuditLogTable";
import { VideoPlayerModal } from "../components/VideoPlayerModal";
import { UploadModal } from "../components/UploadModal";
import type { Video } from "../types/mediaTypes";

type Tab = "videos" | "audit";

function VideoFilterBar({
  search, onSearch,
  mission, onMission,
  drone, onDrone,
  status, onStatus,
  missionsList,
  dronesList
}: {
  search: string; onSearch: (v: string) => void;
  mission: string; onMission: (v: string) => void;
  drone: string; onDrone: (v: string) => void;
  status: string; onStatus: (v: string) => void;
  missionsList: { id: string; label: string }[];
  dronesList: { id: string; label: string }[];
}) {
  const getMissionLabel = () => missionsList.find(m => m.id === mission)?.label || mission;
  const getDroneLabel = () => dronesList.find(d => d.id === drone)?.label || drone;

  const chips = [
    mission && { label: getMissionLabel(), clear: () => onMission("") },
    drone && { label: getDroneLabel(), clear: () => onDrone("") },
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
            className="w-full pl-8 pr-3 py-2 rounded-lg bg-[#161D26] border border-[#1E2733] text-sm text-[#E6EAF0] placeholder:text-[#3A4558] focus:outline-none focus:border-mc-accent/40 transition-colors"
          />
        </div>

        {/* Mission filter */}
        <div className="relative">
          <select
            value={mission}
            onChange={(e) => onMission(e.target.value)}
            className="pl-3 pr-7 py-2 rounded-lg bg-[#161D26] border border-[#1E2733] text-sm text-[#8A94A6] focus:outline-none focus:border-mc-accent/40 transition-colors appearance-none cursor-pointer"
          >
            <option value="">Mission</option>
            {missionsList.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
          </select>
          <ChevronDown size={12} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#8A94A6] pointer-events-none" />
        </div>

        {/* Drone filter */}
        <div className="relative">
          <select
            value={drone}
            onChange={(e) => onDrone(e.target.value)}
            className="pl-3 pr-7 py-2 rounded-lg bg-[#161D26] border border-[#1E2733] text-sm text-[#8A94A6] focus:outline-none focus:border-mc-accent/40 transition-colors appearance-none cursor-pointer"
          >
            <option value="">Drone</option>
            {dronesList.map((d) => <option key={d.id} value={d.id}>{d.label}</option>)}
          </select>
          <ChevronDown size={12} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#8A94A6] pointer-events-none" />
        </div>

        {/* Status filter */}
        <div className="relative">
          <select
            value={status}
            onChange={(e) => onStatus(e.target.value)}
            className="pl-3 pr-7 py-2 rounded-lg bg-[#161D26] border border-[#1E2733] text-sm text-[#8A94A6] focus:outline-none focus:border-mc-accent/40 transition-colors appearance-none cursor-pointer"
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
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-mc-accent/10 text-mc-accent text-xs border border-mc-accent/20"
            >
              {chip.label}
              <button onClick={chip.clear} className="hover:text-mc-accent-hover transition-colors">
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

export function MediaLibraryPage() {
  const { videos, auditLogs, loadingVideos, loadingAuditLogs, uploadVideo, deleteVideo, missionsList, stats } = useMediaLibrary();
  const [activeTab, setActiveTab] = useState<Tab>("videos");
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const [showUpload, setShowUpload] = useState(false);

  // Video filter state
  const [search, setSearch] = useState("");
  const [missionFilter, setMissionFilter] = useState("");
  const [droneFilter, setDroneFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const filteredVideos = videos.filter((v) => {
    if (search && !v.title.toLowerCase().includes(search.toLowerCase()) && !v.id.includes(search)) return false;
    if (missionFilter && v.missionId !== missionFilter) return false;
    if (droneFilter && v.droneId !== droneFilter) return false;
    if (statusFilter && v.status !== statusFilter) return false;
    return true;
  });

  const uniqueMissions = Array.from(new Set(videos.map(v => v.missionId))).sort().map(id => {
    return { id, label: `MSN-${id}` };
  });

  const uniqueDrones = Array.from(new Set(videos.map(v => v.droneId))).sort().map(id => {
    return { id, label: `DRN-${id}` };
  });

  return (
    <main className="flex-1 overflow-y-auto w-full h-full text-[#E6EAF0]" style={{ fontFamily: "'IBM Plex Sans', system-ui, sans-serif" }}>
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
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-mc-accent hover:bg-mc-accent-hover text-[#0B0F14] text-sm font-semibold transition-colors flex-shrink-0"
          >
            <Upload size={13} /> Upload Video
          </button>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Total Videos", value: videos.length.toString(), sub: `across ${uniqueMissions.length} missions` },
            { 
              label: "Storage Used", 
              value: stats ? formatBytes(stats.total_used_bytes) : "...", 
              sub: stats ? `of ${formatBytes(stats.allotted_bytes)} allotted` : "calculating..." 
            },
            { label: "Uploading", value: videos.filter(v => v.status === "uploading").length.toString(), sub: "in progress", accent: true },
            { label: "Failed", value: videos.filter(v => v.status === "failed").length.toString(), sub: "requires retry", warn: true },
          ].map(({ label, value, sub, accent, warn }) => (
            <div key={label} className={`bg-[#161D26] border rounded-xl px-4 py-3 ${warn ? "border-red-500/20" : accent ? "border-mc-accent/20" : "border-[#1E2733]"}`}>
              <p className={`text-xl font-semibold tabular-nums ${warn ? "text-red-400" : accent ? "text-mc-accent" : "text-[#E6EAF0]"}`}>{value}</p>
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
              className={`relative px-4 py-2.5 text-sm font-medium transition-colors cursor-pointer ${
                activeTab === tab ? "text-mc-accent" : "text-[#8A94A6] hover:text-[#E6EAF0]"
              }`}
            >
              <span className="flex items-center gap-2">
                {tab === "videos" ? (
                  <>
                    <Film size={13} /> Videos
                    <span className={`text-[10px] font-bold px-1.5 rounded-full ${activeTab === tab ? "bg-mc-accent/20 text-mc-accent" : "bg-[#1A2232] text-[#8A94A6]"}`}>
                      {videos.length}
                    </span>
                  </>
                ) : (
                  <>
                    <Shield size={13} /> Audit Log
                    <span className={`text-[10px] font-bold px-1.5 rounded-full ${activeTab === tab ? "bg-mc-accent/20 text-mc-accent" : "bg-[#1A2232] text-[#8A94A6]"}`}>
                      {auditLogs.length}
                    </span>
                  </>
                )}
              </span>
              {activeTab === tab && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-mc-accent rounded-t-full" />
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
              missionsList={uniqueMissions}
              dronesList={uniqueDrones}
            />

            {filteredVideos.length === 0 && !loadingVideos ? (
              <div className="flex flex-col items-center justify-center py-20 gap-3">
                <div className="w-14 h-14 rounded-full bg-[#161D26] border border-[#1E2733] flex items-center justify-center">
                  <Film size={22} className="text-[#3A4558]" />
                </div>
                <p className="text-sm font-medium text-[#8A94A6]">No videos match your filters</p>
                <button
                  onClick={() => { setSearch(""); setMissionFilter(""); setDroneFilter(""); setStatusFilter(""); }}
                  className="text-xs text-mc-accent hover:text-mc-accent-hover transition-colors cursor-pointer"
                >
                  Clear filters
                </button>
              </div>
            ) : (
              <VideoGrid videos={filteredVideos} isLoading={loadingVideos} onVideoClick={setSelectedVideo} />
            )}
          </div>
        )}

        {/* Audit log tab */}
        {activeTab === "audit" && <AuditLogTable logs={auditLogs} isLoading={loadingAuditLogs} />}
      </div>

      {/* Modals */}
      {selectedVideo && (
        <VideoPlayerModal 
          video={selectedVideo} 
          onClose={() => setSelectedVideo(null)} 
          onDelete={deleteVideo}
        />
      )}
      {showUpload && (
        <UploadModal 
          onClose={() => setShowUpload(false)} 
          onUpload={(file, metadata) => {
            uploadVideo(file, metadata);
          }} 
          missionsList={missionsList}
        />
      )}
    </main>
  );
}
