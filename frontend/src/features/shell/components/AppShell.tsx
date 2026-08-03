import {
  useEffect,
  useState,
} from "react";
import type { ReactNode } from "react";
import { X } from "lucide-react";

import { SidebarNav } from "./SidebarNav";
import { TopBar } from "./TopBar";
import { useCurrentUser } from "../hooks/useCurrentUser";

interface AppShellProps {
  breadcrumb: string;
  isOffline?: boolean;
  isRefreshing?: boolean;
  onRefresh?: () => void;
  children: ReactNode;
}

export function AppShell({
  breadcrumb,
  isOffline,
  isRefreshing,
  onRefresh,
  children,
}: AppShellProps) {
  const [isNavOpen, setIsNavOpen] =
    useState(false);

  const { data: currentUser } =
    useCurrentUser();

  useEffect(() => {
    if (!isNavOpen) {
      return;
    }

    function handleKeyDown(
      event: KeyboardEvent,
    ) {
      if (event.key === "Escape") {
        setIsNavOpen(false);
      }
    }

    document.addEventListener(
      "keydown",
      handleKeyDown,
    );

    return () => {
      document.removeEventListener(
        "keydown",
        handleKeyDown,
      );
    };
  }, [isNavOpen]);

  return (
    <div className="flex h-dvh w-full overflow-hidden bg-mc-bg text-mc-text">
      <div className="hidden w-55 shrink-0 border-r border-white/6 lg:block">
        <SidebarNav currentUser={currentUser} />
      </div>

      {isNavOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/70"
            onClick={() =>
              setIsNavOpen(false)
            }
          >
            <span className="sr-only">
              Close navigation
            </span>
          </button>

          <div
            className="absolute inset-y-0 left-0 w-64 border-r border-white/8 shadow-2xl"
            role="dialog"
            aria-modal="true"
            aria-label="Navigation"
          >
            <button
              type="button"
              onClick={() =>
                setIsNavOpen(false)
              }
              className="absolute top-3.5 right-3 rounded p-1 text-mc-muted transition-colors hover:bg-white/5 hover:text-mc-text"
            >
              <X
                size={16}
                aria-hidden="true"
              />

              <span className="sr-only">
                Close navigation
              </span>
            </button>

            <SidebarNav
              currentUser={currentUser}
              onNavigate={() =>
                setIsNavOpen(false)
              }
            />
          </div>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar
          breadcrumb={breadcrumb}
          isOffline={isOffline}
          isRefreshing={isRefreshing}
          onOpenNav={() => setIsNavOpen(true)}
          onRefresh={onRefresh}
        />

        <main className="mc-scroll flex-1 overflow-y-auto p-4 sm:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
