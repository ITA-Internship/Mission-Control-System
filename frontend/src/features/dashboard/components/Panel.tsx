import type { ReactNode } from "react";

import { cn } from "../../../shared/utils/cn";

interface PanelProps {
  title?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}

/* Shared card container for dashboard panels: rounded surface, subtle border,
 * optional header row with a title and a trailing action. */
export function Panel({
  title,
  action,
  children,
  className,
  bodyClassName,
}: PanelProps) {
  return (
    <div
      className={cn(
        "flex h-full flex-col rounded-xl border border-mc-border bg-mc-card p-5",
        className,
      )}
    >
      {(title || action) && (
        <div className="mb-4 flex items-center justify-between">
          {title && (
            <h3 className="text-[13px] font-semibold uppercase tracking-wider text-mc-text">
              {title}
            </h3>
          )}
          {action}
        </div>
      )}
      <div className={cn("min-h-0 flex-1", bodyClassName)}>
        {children}
      </div>
    </div>
  );
}
