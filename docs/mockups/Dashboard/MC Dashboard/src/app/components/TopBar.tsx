import { useState } from "react";
import { Bell, Search, ChevronDown, LogOut, Settings, User } from "lucide-react";
import { cn } from "./ui/utils";
import type { Role, User as UserType } from "../types";

const ROLE_COLORS: Record<Role, string> = {
  Admin:       "text-[#E5484D] bg-[#E5484D]/15",
  Commander:   "text-[#4C8DFF] bg-[#4C8DFF]/15",
  Dispatcher:  "text-[#C8A24A] bg-[#C8A24A]/15",
  Operator:    "text-[#3FB950] bg-[#3FB950]/15",
  Technician:  "text-[#F0883E] bg-[#F0883E]/15",
  Viewer:      "text-[#8A94A6] bg-[#8A94A6]/15",
};

const MOCK_NOTIFICATIONS = [
  { id: 1, text: "DRONE-047 lost contact — Zone Delta", time: "2m ago", critical: true },
  { id: 2, text: "Mission OWL-9 entered restricted airspace", time: "7m ago", critical: true },
  { id: 3, text: "Maintenance complete: DRONE-023", time: "14m ago", critical: false },
  { id: 4, text: "New defect reported: DRONE-031 gimbal fault", time: "22m ago", critical: false },
  { id: 5, text: "Mission NIGHTFALL-3 status updated to Active", time: "35m ago", critical: false },
];

interface TopBarProps {
  pageTitle: string;
  sidebarCollapsed: boolean;
  user: UserType;
  onRoleChange: (role: Role) => void;
}

const ALL_ROLES: Role[] = ["Admin", "Commander", "Dispatcher", "Operator", "Technician", "Viewer"];

export function TopBar({ pageTitle, sidebarCollapsed, user, onRoleChange }: TopBarProps) {
  const [notifOpen, setNotifOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [searchFocused, setSearchFocused] = useState(false);

  const criticalCount = MOCK_NOTIFICATIONS.filter(n => n.critical).length;

  return (
    <header
      className={cn(
        "fixed top-0 right-0 h-14 z-30 flex items-center px-6",
        "border-b border-border",
        "transition-all duration-200",
      )}
      style={{
        left: sidebarCollapsed ? "64px" : "240px",
        background: "#0E141B",
      }}
    >
      {/* Page title */}
      <div className="flex-1 min-w-0">
        <h1 className="text-[15px] font-semibold text-[#E6EAF0] tracking-wide uppercase truncate">
          {pageTitle}
        </h1>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-3">
        {/* Search */}
        <div className={cn(
          "flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all duration-150",
          searchFocused
            ? "border-[#C8A24A]/50 bg-[#1C2530]"
            : "border-border bg-[#161D26] hover:border-white/15"
        )}>
          <Search className="w-3.5 h-3.5 text-[#8A94A6] shrink-0" />
          <input
            type="text"
            placeholder="Search..."
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
            className="bg-transparent outline-none text-[13px] text-[#E6EAF0] placeholder:text-[#8A94A6] w-40"
          />
          <span className="font-mono text-[10px] text-[#8A94A6] border border-border rounded px-1">⌘K</span>
        </div>

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => { setNotifOpen(!notifOpen); setUserMenuOpen(false); }}
            className={cn(
              "relative w-8 h-8 flex items-center justify-center rounded-lg border transition-all duration-150",
              notifOpen
                ? "border-[#C8A24A]/40 bg-[#C8A24A]/10 text-[#C8A24A]"
                : "border-border bg-[#161D26] text-[#8A94A6] hover:text-[#E6EAF0] hover:border-white/15"
            )}
          >
            <Bell className="w-4 h-4" />
            {criticalCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-[#E5484D] rounded-full flex items-center justify-center font-mono text-[9px] font-bold text-white">
                {criticalCount}
              </span>
            )}
          </button>

          {notifOpen && (
            <div className="absolute right-0 top-10 w-80 rounded-xl border border-border shadow-2xl overflow-hidden z-50"
              style={{ background: "#161D26" }}>
              <div className="px-4 py-2.5 border-b border-border flex items-center justify-between">
                <span className="text-[12px] font-semibold text-[#E6EAF0] uppercase tracking-wider">Notifications</span>
                <span className="font-mono text-[10px] text-[#8A94A6]">{MOCK_NOTIFICATIONS.length} new</span>
              </div>
              <div className="divide-y divide-border max-h-72 overflow-y-auto">
                {MOCK_NOTIFICATIONS.map(n => (
                  <div key={n.id} className={cn(
                    "px-4 py-2.5 hover:bg-white/5 cursor-pointer transition-colors",
                    n.critical && "border-l-2 border-l-[#E5484D]"
                  )}>
                    <p className="text-[12px] text-[#E6EAF0] leading-snug">{n.text}</p>
                    <p className="font-mono text-[10px] text-[#8A94A6] mt-0.5">{n.time}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={() => { setUserMenuOpen(!userMenuOpen); setNotifOpen(false); }}
            className={cn(
              "flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg border transition-all duration-150",
              userMenuOpen
                ? "border-[#C8A24A]/40 bg-[#C8A24A]/10"
                : "border-border bg-[#161D26] hover:border-white/15"
            )}
          >
            {/* Avatar */}
            <div className="w-7 h-7 rounded-full bg-[#C8A24A]/20 border border-[#C8A24A]/40 flex items-center justify-center">
              <span className="font-mono text-[11px] font-semibold text-[#C8A24A]">{user.initials}</span>
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-[12px] font-semibold text-[#E6EAF0] leading-none">{user.name}</div>
              <div className="text-[10px] text-[#8A94A6] leading-none mt-0.5">{user.rank}</div>
            </div>
            <span className={cn(
              "hidden sm:inline-flex px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold uppercase tracking-wide",
              ROLE_COLORS[user.role]
            )}>
              {user.role}
            </span>
            <ChevronDown className={cn("w-3 h-3 text-[#8A94A6] transition-transform", userMenuOpen && "rotate-180")} />
          </button>

          {userMenuOpen && (
            <div className="absolute right-0 top-11 w-52 rounded-xl border border-border shadow-2xl overflow-hidden z-50"
              style={{ background: "#161D26" }}>
              {/* Role switcher (demo) */}
              <div className="px-3 py-2 border-b border-border">
                <p className="font-mono text-[10px] text-[#8A94A6] uppercase tracking-wider mb-1.5">Demo: Switch Role</p>
                <div className="grid grid-cols-2 gap-1">
                  {ALL_ROLES.map(r => (
                    <button
                      key={r}
                      onClick={() => { onRoleChange(r); setUserMenuOpen(false); }}
                      className={cn(
                        "px-2 py-1 rounded text-[10px] font-mono font-medium text-left transition-colors",
                        user.role === r
                          ? ROLE_COLORS[r] + " opacity-100"
                          : "text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/5"
                      )}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>
              <div className="p-1.5">
                <button className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/5 transition-colors">
                  <User className="w-3.5 h-3.5" />
                  Profile
                </button>
                <button className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/5 transition-colors">
                  <Settings className="w-3.5 h-3.5" />
                  Settings
                </button>
                <button className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] text-[#E5484D] hover:bg-[#E5484D]/10 transition-colors">
                  <LogOut className="w-3.5 h-3.5" />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
