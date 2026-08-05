import { useEffect } from "react";
import type { ReactNode } from "react";
import { X } from "lucide-react";

interface SideDrawerProps {
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: ReactNode;
}

export function SideDrawer({
  title,
  subtitle,
  onClose,
  children,
}: SideDrawerProps) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60">
      <button
        type="button"
        className="flex-1 cursor-default"
        aria-label="Close drawer"
        onClick={onClose}
      />

      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby="repairs-drawer-title"
        className="flex h-full w-full max-w-lg flex-col border-l border-white/10 bg-mc-card shadow-2xl"
      >
        <div className="flex items-start justify-between gap-4 border-b border-white/8 px-5 py-4">
          <div>
            <h2
              id="repairs-drawer-title"
              className="text-base font-semibold text-mc-text"
            >
              {title}
            </h2>
            {subtitle ? (
              <p className="mt-0.5 font-mono text-xs text-mc-muted">
                {subtitle}
              </p>
            ) : null}
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-mc-muted transition-colors hover:bg-white/5 hover:text-mc-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mc-accent/40"
          >
            <X size={16} aria-hidden="true" />
            <span className="sr-only">Close</span>
          </button>
        </div>

        <div className="mc-scroll flex-1 overflow-y-auto px-5 py-4">
          {children}
        </div>
      </aside>
    </div>
  );
}
