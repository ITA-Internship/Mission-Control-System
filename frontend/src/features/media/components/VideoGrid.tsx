import { Loader2 } from "lucide-react";
import type { Video } from "../types/mediaTypes";
import { VideoCard } from "./VideoCard";

interface VideoGridProps {
  videos: Video[];
  isLoading: boolean;
  onVideoClick: (video: Video) => void;
}

export function VideoGrid({ videos, isLoading, onVideoClick }: VideoGridProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-[#8A94A6]">
        <Loader2 className="animate-spin mb-4" size={32} />
        <p>Loading videos...</p>
      </div>
    );
  }

  if (videos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-[#8A94A6]">
        <p>No videos found.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
      {videos.map((video) => (
        <VideoCard
          key={video.id}
          video={video}
          onClick={() => onVideoClick(video)}
        />
      ))}
    </div>
  );
}
