import {
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { NavLink } from "react-router";

import { cn } from "../../../shared/utils/cn";
import { MissionControlLogo } from "../../auth/components/MissionControlLogo";
import { visibleNavItems } from "../rbac";
import type { RoleCode } from "../types/dashboard";

interface SidebarProps {
  role: RoleCode | null;
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({
  role,
  collapsed,
  onToggle,
}: SidebarProps) {
  const items = visibleNavItems(role);

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-mc-border bg-mc-sidebar transition-all duration-200",
        collapsed ? "w-16" : "w-60",
      )}
    >
      {/* Logo / wordmark */}
      <div
        className={cn(
          "flex h-14 shrink-0 items-center border-b border-mc-border px-4",
          collapsed ? "justify-center" : "gap-2.5",
        )}
      >
        <MissionControlLogo className="h-7 w-7 text-mc-accent" />
        {!collapsed && (
          <div>
            <div className="font-mono text-[11px] font-semibold uppercase tracking-widest text-mc-accent">
              Mission
            </div>
            <div className="font-mono text-[11px] font-semibold uppercase tracking-widest text-mc-text">
              Control
            </div>
          </div>
        )}
      </div>

      {/* Nav items */}
      <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 py-3">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.id}
              to={item.path}
              title={collapsed ? item.label : undefined}
              className={({ isActive }) =>
                cn(
                  "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors",
                  isActive
                    ? "bg-mc-accent/10 text-mc-accent"
                    : "text-mc-muted hover:bg-white/5 hover:text-mc-text",
                  collapsed && "justify-center px-2",
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
                      "shrink-0",
                      collapsed ? "h-5 w-5" : "h-4 w-4",
                    )}
                  />
                  {!collapsed && (
                    <span className="text-[13px] font-medium tracking-wide">
                      {item.label}
                    </span>
                  )}
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <div className="shrink-0 border-t border-mc-border px-2 py-3">
        <button
          type="button"
          onClick={onToggle}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
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
  );
}
