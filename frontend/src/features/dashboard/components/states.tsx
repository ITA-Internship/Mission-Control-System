import type { ReactNode } from "react";
import { Inbox, ShieldAlert, TriangleAlert } from "lucide-react";

import { cn } from "../../../shared/utils/cn";

/* Generic skeleton block. */
export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "animate-pulse rounded bg-white/10",
        className,
      )}
    />
  );
}

export function SkeletonRows({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="flex items-center gap-3">
          <Skeleton className="h-9 w-9 rounded-lg" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-3 w-1/2" />
            <Skeleton className="h-2.5 w-1/3" />
          </div>
          <Skeleton className="h-4 w-14 rounded-full" />
        </div>
      ))}
    </div>
  );
}

interface MessageStateProps {
  icon: ReactNode;
  title: string;
  description?: string;
  tone?: "muted" | "danger";
}

function MessageState({
  icon,
  title,
  description,
  tone = "muted",
}: MessageStateProps) {
  return (
    <div className="flex h-full min-h-[160px] flex-col items-center justify-center gap-3 py-8 text-center">
      <div
        className={cn(
          "flex h-10 w-10 items-center justify-center rounded-xl",
          tone === "danger"
            ? "bg-mc-error/10 text-mc-error"
            : "bg-white/5 text-mc-muted",
        )}
      >
        {icon}
      </div>
      <div>
        <p className="text-[13px] font-semibold text-mc-text">
          {title}
        </p>
        {description && (
          <p className="mt-1 font-mono text-[11px] text-mc-muted">
            {description}
          </p>
        )}
      </div>
    </div>
  );
}

export function EmptyState({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <MessageState
      icon={<Inbox className="h-5 w-5" />}
      title={title}
      description={description}
    />
  );
}

export function ErrorState({
  title = "Couldn't load data",
  description = "The request failed. Try again shortly.",
}: {
  title?: string;
  description?: string;
}) {
  return (
    <MessageState
      icon={<TriangleAlert className="h-5 w-5" />}
      title={title}
      description={description}
      tone="danger"
    />
  );
}

export function RestrictedState({
  description,
}: {
  description?: string;
}) {
  return (
    <MessageState
      icon={<ShieldAlert className="h-5 w-5 text-mc-accent" />}
      title="Restricted access"
      description={
        description ??
        "Your role does not have permission to view this data."
      }
    />
  );
}
