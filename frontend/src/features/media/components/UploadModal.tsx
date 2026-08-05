import { useState, useEffect } from "react";
import { Upload, X, FileVideo, ChevronDown } from "lucide-react";
import { mediaApi } from "../api/mediaApi";

type UploadState = "idle" | "dragging" | "uploading" | "success" | "error";

interface UploadModalProps {
  onClose: () => void;
  onUpload: (file: File, metadata: { title: string; missionId: string; droneId: string }) => void;
  missionsList: { id: number; title?: string; callsign?: string }[];
}

export function UploadModal({ onClose, onUpload, missionsList }: UploadModalProps) {
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [selectedMission, setSelectedMission] = useState("");
  const [selectedDrone, setSelectedDrone] = useState("");
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [availableDrones, setAvailableDrones] = useState<{ id: number; inventory_number?: string }[]>([]);
  const [loadingDrones, setLoadingDrones] = useState(false);

  useEffect(() => {
    if (!selectedMission) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setAvailableDrones([]);
      return;
    }
    setLoadingDrones(true);
    mediaApi.fetchMissionAssignments(selectedMission)
      .then(res => {
        const drones = res.results.map(a => ({
          id: a.drone,
          inventory_number: a.drone_details?.inventory_number || String(a.drone)
        }));
        setAvailableDrones(drones);
      })
      .catch(() => setAvailableDrones([]))
      .finally(() => setLoadingDrones(false));
  }, [selectedMission]);

  const canSubmit = title.trim() && selectedMission && selectedDrone && file && uploadState === "idle";

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setUploadState("idle");
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.type.startsWith("video/")) {
      setFile(dropped);
      if (!title) setTitle(dropped.name);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
      if (!title) setTitle(selected.name);
    }
  };

  const startUpload = () => {
    if (!canSubmit || !file) return;
    
    // Fire and forget
    onUpload(file, { title, missionId: selectedMission, droneId: selectedDrone });
    
    // Close modal immediately so user sees the background upload in the grid
    onClose();
  };

  const isDragging = uploadState === "dragging";
  const showDropzone = uploadState === "idle" || uploadState === "dragging";

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/85 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md bg-[#161D26] border border-[#1E2733] rounded-xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#1E2733]">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-md bg-mc-accent/15 flex items-center justify-center">
              <Upload size={12} className="text-mc-accent" />
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
            <label
              onDragOver={(e) => { e.preventDefault(); setUploadState("dragging"); }}
              onDragLeave={() => setUploadState("idle")}
              onDrop={handleDrop}
              className={`block border-2 border-dashed rounded-xl py-8 flex flex-col items-center gap-3 transition-all cursor-pointer select-none relative overflow-hidden ${
                isDragging
                  ? "border-mc-accent bg-mc-accent/5"
                  : file
                  ? "border-mc-accent/50 bg-mc-accent/5"
                  : "border-[#1E2733] hover:border-[#2A3444] hover:bg-white/[0.01]"
              }`}
            >
              <input type="file" className="hidden" accept="video/*" onChange={handleFileChange} />
              
              {file ? (
                <>
                  <div className="w-12 h-12 rounded-full flex items-center justify-center transition-all bg-[#1A2232]">
                    <FileVideo size={22} className="text-mc-accent" />
                  </div>
                  <div className="text-center px-4 w-full">
                    <p className="text-sm font-medium text-[#E6EAF0] truncate">{file.name}</p>
                    <p className="text-xs text-[#8A94A6] mt-0.5">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                  </div>
                </>
              ) : (
                <>
                  <div
                    className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                      isDragging ? "bg-mc-accent/20 scale-110" : "bg-[#1A2232]"
                    }`}
                  >
                    <FileVideo size={22} className={isDragging ? "text-mc-accent" : "text-[#8A94A6]"} />
                  </div>
                  <div className="text-center">
                    <p className={`text-sm font-medium transition-colors ${isDragging ? "text-mc-accent" : "text-[#E6EAF0]"}`}>
                      {isDragging ? "Release to add file" : "Drag video file here"}
                    </p>
                    <p className="text-xs text-[#8A94A6] mt-0.5">MP4, MOV, AVI · max 20 GB</p>
                  </div>
                  {!isDragging && (
                    <div className="px-3.5 py-1.5 rounded-lg bg-[#1A2232] hover:bg-[#202D3E] text-sm text-[#E6EAF0] border border-[#1E2733] transition-colors">
                      Browse files
                    </div>
                  )}
                </>
              )}
            </label>
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
                placeholder="e.g. Sector 9 Night Sweep"
                className="w-full px-3 py-2 rounded-lg bg-[#0E141B] border border-[#1E2733] text-sm text-[#E6EAF0] placeholder:text-[#3A4558] focus:outline-none focus:border-mc-accent/50 transition-colors disabled:opacity-50"
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
                  className="w-full px-3 pr-8 py-2 rounded-lg bg-[#0E141B] border border-[#1E2733] text-sm text-[#E6EAF0] focus:outline-none focus:border-mc-accent/50 transition-colors appearance-none disabled:opacity-50"
                >
                  <option value="">Select mission…</option>
                  {missionsList.map((m) => (
                    <option key={m.id} value={String(m.id)}>Mission {m.id} {m.title ? `— ${m.title}` : ""}</option>
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
                  disabled={!selectedMission}
                  className="w-full px-3 pr-8 py-2 rounded-lg bg-[#0E141B] border border-[#1E2733] text-sm text-[#E6EAF0] focus:outline-none focus:border-mc-accent/50 transition-colors appearance-none disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <option value="">
                    {selectedMission 
                      ? (loadingDrones ? "Loading drones…" : availableDrones.length ? "Select drone…" : "No drones assigned") 
                      : "Select mission first"}
                  </option>
                  {availableDrones.map((d) => (
                    <option key={d.id} value={String(d.id)}>Drone {d.id} {d.inventory_number ? `— ${d.inventory_number}` : ""}</option>
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
            Cancel
          </button>
          <button
            onClick={startUpload}
            disabled={!canSubmit}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-mc-accent hover:bg-mc-accent-hover text-[#0B0F14] text-sm font-semibold transition-colors disabled:opacity-35 disabled:cursor-not-allowed"
          >
            <Upload size={13} /> Upload
          </button>
        </div>
      </div>
    </div>
  );
}
