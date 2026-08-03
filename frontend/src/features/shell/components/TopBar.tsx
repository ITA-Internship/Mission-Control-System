import {
  PanelLeft,
  RefreshCw,
} from "lucide-react";

interface TopBarProps {
  breadcrumb: string;
  isOffline?: boolean;
  isRefreshing?: boolean;
  onOpenNav: () => void;
  onRefresh?: () => void;
}

export function TopBar({
  breadcrumb,
  isOffline = false,
  isRefreshing = false,
  onOpenNav,
  onRefresh,
}: TopBarProps) {
  return (
    <header className="flex h-12 shrink-0 items-center justify-between gap-3 border-b border-white/6 bg-mc-panel px-3 sm:px-6">
      <div className="flex min-w-0 items-center gap-2">
        <button
          type="button"
          onClick={onOpenNav}
          className="-ml-1 rounded p-2 text-mc-muted transition-colors hover:bg-white/5 hover:text-mc-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mc-accent/40 lg:hidden"
        >
          <PanelLeft
            size={16}
            aria-hidden="true"
          />

          <span className="sr-only">
            Open navigation
          </span>
        </button>

        <nav
          className="flex min-w-0 items-center gap-2 font-mono text-xs text-mc-muted"
          aria-label="Breadcrumb"
        >
          <span className="text-mc-accent">
            MCS
          </span>

          <span aria-hidden="true">/</span>

          <span className="truncate text-mc-muted">
            {breadcrumb}
          </span>
        </nav>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <p
          className={[
            "hidden items-center gap-1.5 rounded px-2.5 py-1",
            "font-mono text-[11px] tracking-wider sm:flex",
            isOffline
              ? "bg-mc-error/10 text-mc-error"
              : "bg-mc-success/10 text-mc-success",
          ].join(" ")}
          role="status"
        >
          <span
            className={[
              "size-1.5 rounded-full bg-current",
              isOffline ? "" : "animate-pulse",
            ].join(" ")}
            aria-hidden="true"
          />

          {isOffline
            ? "LINK DEGRADED"
            : "SYSTEM NOMINAL"}
        </p>

        {onRefresh ? (
          <button
            type="button"
            onClick={onRefresh}
            className="rounded p-2 text-mc-muted transition-colors hover:bg-white/5 hover:text-mc-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mc-accent/40"
          >
            <RefreshCw
              size={16}
              className={
                isRefreshing
                  ? "animate-spin"
                  : undefined
              }
              aria-hidden="true"
            />

            <span className="sr-only">
              Reload page data
            </span>
          </button>
        ) : null}
      </div>
    </header>
  );
}
