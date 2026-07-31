import { useState } from "react";
import {
  Bell,
  ChevronDown,
  LogOut,
  Search,
  User as UserIcon,
} from "lucide-react";
import { useNavigate } from "react-router";

import { cn } from "../../../shared/utils/cn";
import type { CurrentUser } from "../../auth/types/auth";
import {
  displayName,
  initials,
  toRoleCode,
} from "../shellContext";
import type { RoleCode } from "../types/dashboard";

const ROLE_BADGE: Record<RoleCode, string> = {
  ADMIN: "text-mc-error bg-mc-error/15",
  COMMANDER: "text-status-mission bg-status-mission/15",
  DISPATCHER: "text-mc-accent bg-mc-accent/15",
  OPERATOR: "text-status-active bg-status-active/15",
  TECHNICIAN: "text-severity-high bg-severity-high/15",
  VIEWER: "text-mc-muted bg-mc-muted/15",
};

interface TopBarProps {
  pageTitle: string;
  collapsed: boolean;
  user: CurrentUser;
}

export function TopBar({
  pageTitle,
  collapsed,
  user,
}: TopBarProps) {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const role = toRoleCode(user.role_code);
  const roleBadge = role ? ROLE_BADGE[role] : "text-mc-muted bg-mc-muted/15";
  const roleLabel = user.role_name ?? role ?? "No role";

  function handleSignOut() {
    // No backend logout endpoint exists yet; clear client route state and
    // return to the sign-in screen. See the plan's "Open flags".
    setMenuOpen(false);
    navigate("/login", { replace: true });
  }

  return (
    <header
      className="fixed right-0 top-0 z-30 flex h-14 items-center border-b border-mc-border bg-mc-sidebar px-6 transition-all duration-200"
      style={{ left: collapsed ? "64px" : "240px" }}
    >
      <div className="min-w-0 flex-1">
        <h1 className="truncate text-[15px] font-semibold uppercase tracking-wide text-mc-text">
          {pageTitle}
        </h1>
      </div>

      <div className="flex items-center gap-3">
        {/* Search (stub — no backing endpoint) */}
        <div className="hidden items-center gap-2 rounded-lg border border-mc-border bg-mc-card px-3 py-1.5 md:flex">
          <Search className="h-3.5 w-3.5 shrink-0 text-mc-muted" />
          <input
            type="text"
            placeholder="Search..."
            aria-label="Search"
            className="w-40 bg-transparent text-[13px] text-mc-text outline-none placeholder:text-mc-muted"
          />
          <span className="rounded border border-mc-border px-1 font-mono text-[10px] text-mc-muted">
            ⌘K
          </span>
        </div>

        {/* Notifications (stub) */}
        <button
          type="button"
          aria-label="Notifications"
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-mc-border bg-mc-card text-mc-muted transition-colors hover:border-white/15 hover:text-mc-text"
        >
          <Bell className="h-4 w-4" />
        </button>

        {/* User menu */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            className={cn(
              "flex items-center gap-2.5 rounded-lg border px-2.5 py-1.5 transition-colors",
              menuOpen
                ? "border-mc-accent/40 bg-mc-accent/10"
                : "border-mc-border bg-mc-card hover:border-white/15",
            )}
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-full border border-mc-accent/40 bg-mc-accent/20 font-mono text-[11px] font-semibold text-mc-accent">
              {initials(user)}
            </span>
            <span className="hidden text-left sm:block">
              <span className="block text-[12px] font-semibold leading-none text-mc-text">
                {displayName(user)}
              </span>
              <span className="mt-0.5 block text-[10px] leading-none text-mc-muted">
                {user.rank ?? "—"}
              </span>
            </span>
            <span
              className={cn(
                "hidden rounded px-1.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wide sm:inline-flex",
                roleBadge,
              )}
            >
              {role ?? "—"}
            </span>
            <ChevronDown
              className={cn(
                "h-3 w-3 text-mc-muted transition-transform",
                menuOpen && "rotate-180",
              )}
            />
          </button>

          {menuOpen && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setMenuOpen(false)}
              />
              <div className="absolute right-0 top-11 z-50 w-52 overflow-hidden rounded-xl border border-mc-border bg-mc-card shadow-2xl">
                <div className="border-b border-mc-border px-4 py-3">
                  <p className="truncate text-[13px] font-semibold text-mc-text">
                    {displayName(user)}
                  </p>
                  <p className="truncate font-mono text-[10px] text-mc-muted">
                    {roleLabel}
                  </p>
                </div>
                <div className="p-1.5">
                  <button
                    type="button"
                    className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] text-mc-muted transition-colors hover:bg-white/5 hover:text-mc-text"
                  >
                    <UserIcon className="h-3.5 w-3.5" />
                    Profile
                  </button>
                  <button
                    type="button"
                    onClick={handleSignOut}
                    className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] text-mc-error transition-colors hover:bg-mc-error/10"
                  >
                    <LogOut className="h-3.5 w-3.5" />
                    Sign out
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
