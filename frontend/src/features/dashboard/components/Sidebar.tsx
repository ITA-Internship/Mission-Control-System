import { useEffect } from "react";
import {
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { NavLink } from "react-router";

import { cn } from "../../../shared/utils/cn";
import { MissionControlLogo } from "../../auth/components/MissionControlLogo";
import { visibleNavItems } from "../rbac";
import { sidebarWidthClass } from "../shellLayout";
import type { RoleCode } from "../types/dashboard";

interface SidebarProps {
  role: RoleCode | null;
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function Sidebar({
  role,
  collapsed,
  onToggle,
  mobileOpen,
  onMobileClose,
}: SidebarProps) {
  const items = visibleNavItems(role);

  // Close the drawer on Escape while it's open (mobile only).
  useEffect(() => {
    if (!mobileOpen) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onMobileClose();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [mobileOpen, onMobileClose]);

  return (
    <>
      {/* Backdrop — only rendered while the mobile drawer is open. */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          onClick={onMobileClose}
          aria-hidden="true"
        />
      )}

      <aside
        aria-label="Primary"
        className={cn(
          "fixed left-0 top-0 z-50 flex h-screen w-60 flex-col border-r border-mc-border bg-mc-sidebar",
          "transition-transform duration-200 lg:transition-[width]",
          sidebarWidthClass(collapsed),
          // Below `lg` the sidebar is an overlay drawer that slides off-screen
          // when closed; from `lg` up it is always pinned in the layout.
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
        )}
      >
        {/* Logo / wordmark */}
        <div
          className={cn(
            "flex h-14 shrink-0 items-center border-b border-mc-border px-4",
            collapsed ? "lg:justify-center" : "gap-2.5",
          )}
        >
          <MissionControlLogo className="h-7 w-7 text-mc-accent" />
          <div className={cn(collapsed && "lg:hidden")}>
            <div className="font-mono text-[11px] font-semibold uppercase tracking-widest text-mc-accent">
              Mission
            </div>
            <div className="font-mono text-[11px] font-semibold uppercase tracking-widest text-mc-text">
              Control
            </div>
          </div>
        </div>

        {/* Nav items */}
        <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 py-3">
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.id}
                to={item.path}
                onClick={onMobileClose}
                title={collapsed ? item.label : undefined}
                className={({ isActive }) =>
                  cn(
                    "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors",
                    isActive
                      ? "bg-mc-accent/10 text-mc-accent"
                      : "text-mc-muted hover:bg-white/5 hover:text-mc-text",
                    collapsed && "lg:justify-center lg:px-2",
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    {isActive && (
                      <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-r bg-mc-accent" />
                    )}
                    <Icon
                      className={cn(
                        "h-4 w-4 shrink-0",
                        collapsed && "lg:h-5 lg:w-5",
                      )}
                    />
                    <span
                      className={cn(
                        "text-[13px] font-medium tracking-wide",
                        collapsed && "lg:hidden",
                      )}
                    >
                      {item.label}
                    </span>
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Collapse toggle — desktop only; the drawer is dismissed via backdrop/Escape. */}
        <div className="hidden shrink-0 border-t border-mc-border px-2 py-3 lg:block">
          <button
            type="button"
            onClick={onToggle}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className={cn(
              "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-mc-muted transition-colors hover:bg-white/5 hover:text-mc-text",
              collapsed && "justify-center",
            )}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <>
                <ChevronLeft className="h-4 w-4" />
                <span className="text-[13px] font-medium">Collapse</span>
              </>
            )}
          </button>
        </div>
      </aside>
    </>
  );
}
