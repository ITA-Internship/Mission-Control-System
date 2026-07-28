import { cn } from "./ui/utils";
import {
  LayoutDashboard,
  Plane,
  Target,
  Wrench,
  Image,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import type { Role } from "../types";

interface NavItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  allowedRoles: Role[];
}

const NAV_ITEMS: NavItem[] = [
  { id: "dashboard",      label: "Dashboard",      icon: LayoutDashboard, allowedRoles: ["Admin","Commander","Dispatcher","Operator","Technician","Viewer"] },
  { id: "drones",         label: "Drones",          icon: Plane,           allowedRoles: ["Admin","Commander","Dispatcher","Operator","Technician"] },
  { id: "missions",       label: "Missions",         icon: Target,          allowedRoles: ["Admin","Commander","Dispatcher","Operator"] },
  { id: "repairs",        label: "Repairs",          icon: Wrench,          allowedRoles: ["Admin","Commander","Technician"] },
  { id: "media",          label: "Media",            icon: Image,           allowedRoles: ["Admin","Commander","Dispatcher","Operator"] },
  { id: "administration", label: "Administration",   icon: ShieldCheck,     allowedRoles: ["Admin"] },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  activeItem: string;
  onNavigate: (id: string) => void;
  role: Role;
}

export function Sidebar({ collapsed, onToggle, activeItem, onNavigate, role }: SidebarProps) {
  const visibleItems = NAV_ITEMS.filter(item => item.allowedRoles.includes(role));

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 h-screen flex flex-col z-40 transition-all duration-200",
        "border-r border-border",
        collapsed ? "w-16" : "w-60"
      )}
      style={{ background: "var(--sidebar)" }}
    >
      {/* Logo / Wordmark */}
      <div className={cn(
        "flex items-center h-14 px-4 border-b border-border shrink-0",
        collapsed ? "justify-center" : "justify-between"
      )}>
        {collapsed ? (
          <div className="w-8 h-8 flex items-center justify-center">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <polygon points="14,2 26,24 2,24" fill="none" stroke="#C8A24A" strokeWidth="2" strokeLinejoin="round"/>
              <circle cx="14" cy="16" r="2.5" fill="#C8A24A"/>
            </svg>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-2.5">
              <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                <polygon points="14,2 26,24 2,24" fill="none" stroke="#C8A24A" strokeWidth="2" strokeLinejoin="round"/>
                <circle cx="14" cy="16" r="2.5" fill="#C8A24A"/>
              </svg>
              <div>
                <div className="font-mono text-[11px] font-semibold tracking-widest uppercase text-[#C8A24A]">Mission</div>
                <div className="font-mono text-[11px] font-semibold tracking-widest uppercase text-[#E6EAF0]">Control</div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Nav Items */}
      <nav className="flex-1 px-2 py-3 overflow-y-auto space-y-0.5">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeItem === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              title={collapsed ? item.label : undefined}
              className={cn(
                "relative w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-150 group",
                "text-left",
                isActive
                  ? "bg-[#C8A24A]/10 text-[#C8A24A]"
                  : "text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/5",
                collapsed && "justify-center px-2"
              )}
            >
              {/* Active bar */}
              {isActive && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-[#C8A24A] rounded-r" />
              )}
              <Icon className={cn("shrink-0", isActive ? "text-[#C8A24A]" : "text-current", collapsed ? "w-5 h-5" : "w-4 h-4")} />
              {!collapsed && (
                <span className={cn("text-[13px] font-medium tracking-wide", isActive ? "text-[#C8A24A]" : "")}>
                  {item.label}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <div className="px-2 py-3 border-t border-border shrink-0">
        <button
          onClick={onToggle}
          className={cn(
            "w-full flex items-center gap-3 px-3 py-2 rounded-lg",
            "text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/5 transition-all duration-150",
            collapsed && "justify-center"
          )}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <>
              <ChevronLeft className="w-4 h-4" />
              <span className="text-[13px] font-medium">Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
