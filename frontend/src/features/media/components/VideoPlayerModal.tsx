import { Link } from "react-router";
import { Film, X, Download, Trash2, ExternalLink } from "lucide-react";
import type { Video } from "../types/mediaTypes";
import { StatusPill } from "./ui/Pills";

export function VideoPlayerModal({
  video,
  onClose,
  onDelete
}: {
  video: Video;
  onClose: () => void;
  onDelete?: (id: string) => Promise<void>;
}) {
  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/85 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-5xl bg-[#161D26] border border-[#1E2733] rounded-xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#1E2733]">
          <div className="flex items-center gap-3 min-w-0">
            <Film size={15} className="text-mc-accent flex-shrink-0" />
            <span className="text-sm font-semibold text-[#E6EAF0] truncate">{video.title}</span>
            <StatusPill status={video.status} />
            <span className="text-xs text-[#8A94A6] font-mono flex-shrink-0 hidden sm:inline">#{video.id}</span>
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
          <div className="flex-1 min-w-0 bg-[#000000] flex flex-col justify-center">
            {/* Video area */}
            <div className="relative w-full aspect-video flex items-center justify-center">
              {video.url && video.status === "ready" ? (
                <video
                  src={video.url}
                  controls
                  autoPlay
                  className="w-full h-full object-contain"
                >
                  Your browser does not support the video tag.
                </video>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <div className="w-16 h-16 rounded-full bg-[#1A2232] flex items-center justify-center opacity-50">
                    <Film size={26} className="text-[#8A94A6]" />
                  </div>
                  <p className="text-sm text-[#8A94A6]">Video not available yet</p>
                </div>
              )}
            </div>
          </div>

          {/* Metadata panel */}
          <div className="lg:w-72 xl:w-80 flex-shrink-0 border-t lg:border-t-0 lg:border-l border-[#1E2733] flex flex-col">
            <div className="p-5 flex-1 overflow-y-auto space-y-5">
              {/* Metadata */}
              <section>
                <h4 className="text-[10px] font-semibold text-[#8A94A6] uppercase tracking-[0.12em] mb-3">
                  Basic Info
                </h4>
                <dl className="space-y-3">
                  <div>
                    <dt className="text-xs text-[#8A94A6] mb-0.5">Mission</dt>
                    <dd className="flex items-center gap-2">
                      <span className="text-sm font-medium text-[#E6EAF0]">{video.missionName}</span>
                      <span className="px-1.5 py-0.5 rounded-sm bg-[#1A2232] text-[#8A94A6] text-[10px] font-mono tracking-wider">MSN-{video.missionId}</span>
                      <Link
                        to={`/missions/${video.missionId}`}
                        className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-mc-accent/10 hover:bg-mc-accent/20 border border-mc-accent/20 text-mc-accent text-[9px] uppercase font-bold tracking-widest transition-colors ml-auto"
                        title="View Mission Details"
                        onClick={onClose}
                      >
                        View Detail <ExternalLink size={10} />
                      </Link>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-[#8A94A6] mb-0.5">Drone Asset</dt>
                    <dd className="flex items-center gap-2">
                      <span className="text-sm font-medium text-[#E6EAF0]">{video.droneName}</span>
                      <span className="px-1.5 py-0.5 rounded-sm bg-[#1A2232] text-[#8A94A6] text-[10px] font-mono tracking-wider">DRN-{video.droneId}</span>
                      <Link
                        to={`/drones/${video.droneId}`}
                        className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-mc-accent/10 hover:bg-mc-accent/20 border border-mc-accent/20 text-mc-accent text-[9px] uppercase font-bold tracking-widest transition-colors ml-auto"
                        title="View Drone Details"
                        onClick={onClose}
                      >
                        View Detail <ExternalLink size={10} />
                      </Link>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-[#8A94A6] mb-0.5">Uploaded By</dt>
                    <dd className="text-sm text-[#E6EAF0]">{video.uploadedBy}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-[#8A94A6] mb-0.5">Upload Date</dt>
                    <dd className="text-sm text-[#E6EAF0]">{video.uploadedAt}</dd>
                  </div>
                  <div>
                    <p className="text-[#8A94A6] text-xs">Duration</p>
                    <p className="text-[#E6EAF0] text-sm">{video.duration}</p>
                  </div>
                  <div>
                    <p className="text-[#8A94A6] text-xs">File Size</p>
                    <p className="text-[#E6EAF0] text-sm">{video.fileSize}</p>
                  </div>
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
              <a
                href={video.url}
                download={video.title}
                className="w-full flex items-center justify-center gap-2.5 px-3 py-2 rounded-lg bg-mc-accent/10 hover:bg-mc-accent/15 text-mc-accent text-sm font-medium transition-colors"
              >
                <Download size={14} /> Download Video
              </a>
              {onDelete && (
                <button
                  onClick={() => {
                    if (window.confirm("Are you sure you want to delete this video?")) {
                      onDelete(video.id).then(() => {
                        onClose();
                        window.location.reload();
                      }).catch(err => {
                        alert("Failed to delete: " + err.message);
                      });
                    }
                  }}
                  className="w-full flex items-center justify-center gap-2.5 px-3 py-2 rounded-lg hover:bg-red-500/8 text-[#8A94A6] hover:text-red-400 text-sm transition-colors"
                >
                  <Trash2 size={14} /> Delete
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
