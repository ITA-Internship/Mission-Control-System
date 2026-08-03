import { LogOut, Shield } from "lucide-react";
import { NavLink } from "react-router";

import { Avatar } from "../../../shared/components/Avatar";
import { NAV_ITEMS } from "../constants/navigation";
import { getUserDisplayName } from "../hooks/useCurrentUser";
import type { CurrentUser } from "../../auth/types/auth";

interface SidebarNavProps {
  currentUser: CurrentUser | null;
  onNavigate?: () => void;
}

const itemBaseClasses = [
  "flex w-full items-center gap-3 rounded-lg",
  "border-l-2 px-3 py-2.5",
  "text-left text-[13px] font-medium",
  "transition-colors duration-150",
].join(" ");

export function SidebarNav({
  currentUser,
  onNavigate,
}: SidebarNavProps) {
  return (
    <div className="flex h-full flex-col bg-mc-panel">
      <div className="flex items-center gap-2.5 border-b border-white/6 px-5 py-4">
        <span className="flex size-8 items-center justify-center rounded-lg border border-mc-accent/30 bg-mc-accent/15">
          <Shield
            size={16}
            className="text-mc-accent"
            aria-hidden="true"
          />
        </span>

        <span className="flex flex-col">
          <span className="text-xs font-bold tracking-[0.18em] text-mc-accent uppercase">
            MCS
          </span>

          <span className="text-[10px] tracking-[0.12em] text-mc-muted uppercase">
            Mission Control
          </span>
        </span>
      </div>

      <nav
        className="mc-scroll flex flex-1 flex-col gap-0.5 overflow-y-auto px-2 py-3"
        aria-label="Primary"
      >
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;

          if (!item.to) {
            return (
              <span
                key={item.label}
                className={`${itemBaseClasses} cursor-not-allowed border-transparent text-mc-subtle`}
                title="This page is not available yet."
                aria-disabled="true"
              >
                <Icon
                  size={16}
                  className="shrink-0"
                  aria-hidden="true"
                />

                {item.label}
              </span>
            );
          }

          return (
            <NavLink
              key={item.label}
              to={item.to}
              onClick={onNavigate}
              className={({ isActive }) =>
                [
                  itemBaseClasses,
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mc-accent/40",
                  isActive
                    ? "border-mc-accent bg-mc-accent/12 text-mc-accent"
                    : "border-transparent text-mc-muted hover:bg-white/4 hover:text-mc-text",
                ].join(" ")
              }
            >
              <Icon
                size={16}
                className="shrink-0"
                aria-hidden="true"
              />

              {item.label}
            </NavLink>
          );
        })}
      </nav>

      <div className="border-t border-white/6 px-3 py-3">
        <div className="flex items-center gap-2.5 rounded-lg px-2 py-2">
          <Avatar
            name={getUserDisplayName(
              currentUser,
            )}
          />

          <span className="flex min-w-0 flex-1 flex-col">
            <span className="truncate text-xs font-semibold text-mc-text">
              {getUserDisplayName(currentUser)}
            </span>

            <span className="truncate font-mono text-[10px] text-mc-muted">
              {currentUser?.email ?? "—"}
            </span>
          </span>

          <button
            type="button"
            disabled
            title="Sign out is unavailable — the API has no logout endpoint yet."
            className="rounded p-1 text-mc-subtle disabled:cursor-not-allowed"
          >
            <LogOut
              size={14}
              aria-hidden="true"
            />

            <span className="sr-only">
              Sign out
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
