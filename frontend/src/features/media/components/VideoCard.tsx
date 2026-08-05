import { Play, Loader2, AlertTriangle } from "lucide-react";
import type { Video } from "../types/mediaTypes";
import { StatusPill } from "./ui/Pills";

interface VideoCardProps {
  video: Video;
  onClick: () => void;
}

export function VideoCard({ video, onClick }: VideoCardProps) {
  const isReady = video.status === "ready";
  const isUploading = video.status === "uploading";
  const isFailed = video.status === "failed";

  const displayProgress = Math.round(video.progress ?? 100);

  return (
    <div
      onClick={isReady ? onClick : undefined}
      className={`group bg-[#161D26] border rounded-xl overflow-hidden transition-all duration-200 ${
        isFailed
          ? "border-red-500/25 cursor-default"
          : isUploading
          ? "border-mc-accent/20 cursor-default"
          : "border-[#1E2733] hover:border-mc-accent/35 hover:shadow-xl hover:shadow-black/40 cursor-pointer"
      }`}
    >
      {/* Thumbnail */}
      <div className="relative aspect-video bg-[#0E141B] overflow-hidden">
        {!isUploading && video.url ? (
          <video
            src={`${video.url}#t=0.1`}
            className={`w-full h-full object-cover transition-all duration-300 pointer-events-none ${
              isFailed ? "opacity-15 grayscale" : "opacity-55 group-hover:opacity-75"
            }`}
            muted
            playsInline
            preload="metadata"
          />
        ) : (
          <div className="w-full h-full bg-[#1A2232] flex items-center justify-center opacity-50" />
        )}

        {/* Ready: play button on hover */}
        {isReady && (
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <div className="w-12 h-12 rounded-full bg-mc-accent/20 border border-mc-accent/50 backdrop-blur-sm flex items-center justify-center">
              <Play size={20} fill="currentColor" className="text-mc-accent ml-0.5" />
            </div>
          </div>
        )}

        {/* Uploading: spinner + real progress */}
        {isUploading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2.5 px-5">
            <Loader2 size={22} className="text-mc-accent animate-spin" />
            <div className="w-full h-1 bg-[#1E2733] rounded-full overflow-hidden relative">
              <div 
                className="h-full bg-mc-accent rounded-full transition-all duration-150" 
                style={{ width: `${displayProgress}%` }}
              />
            </div>
            <span className="text-xs text-mc-accent font-mono tabular-nums">{displayProgress}%</span>
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
        {isReady && video.duration && (
          <div className="absolute bottom-2 right-2 bg-black/75 backdrop-blur-sm px-1.5 py-0.5 rounded text-xs font-mono text-white">
            {video.duration}
          </div>
        )}

        {/* Uploading duration */}
        {isUploading && video.fileSize && (
          <div className="absolute top-2 right-2 bg-black/75 backdrop-blur-sm px-1.5 py-0.5 rounded text-xs font-mono text-mc-accent">
            {video.fileSize}
          </div>
        )}
      </div>

      {/* Body */}
      <div className="p-3.5 space-y-2.5">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-[13px] font-medium text-[#E6EAF0] leading-snug line-clamp-2 break-all flex-1">
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
            MSN-{video.missionId}
          </span>
          <span className="text-xs px-2 py-0.5 rounded-md bg-[#1A2232] text-[#8A94A6] border border-[#1E2733] font-mono">
            DRN-{video.droneId}
          </span>
        </div>

        <div className="flex items-center justify-between pt-0.5 border-t border-[#1E2733]/60">
          <span className="text-xs text-[#8A94A6] truncate">{video.uploadedBy}</span>
          <span className="text-xs text-[#8A94A6] font-mono flex-shrink-0 ml-2">
            {video.uploadedAt?.split(" ")[0].replace(",", "")}
          </span>
        </div>
      </div>
    </div>
  );
}
