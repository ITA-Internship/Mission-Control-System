import type { ReactNode } from "react";
import {
  BarChart3,
  Bell,
  ChevronRight,
  FileText,
  Home,
  Map,
  Radio,
  Settings,
  Shield,
  Users,
} from "lucide-react";

interface AppShellProps {
  children: ReactNode;
}

const NAV_ITEMS = [
  { icon: Home, label: "Dashboard", active: false },
  { icon: Map, label: "Operations", active: false },
  { icon: Radio, label: "Fleet", active: true },
  { icon: BarChart3, label: "Analytics", active: false },
  { icon: Users, label: "Personnel", active: false },
  { icon: FileText, label: "Reports", active: false },
  { icon: Settings, label: "Settings", active: false },
];

const SUB_NAV_ITEMS = [
  { label: "Inventory", active: true },
  { label: "Models", active: false },
  { label: "Assignments", active: false },
  { label: "Maintenance Log", active: false },
];

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0B0F14]" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
      <aside className="flex w-[220px] shrink-0 flex-col border-r border-white/6 bg-[#0E141B]">
        <div className="border-b border-white/6 px-5 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded bg-[#C8A24A]">
              <Shield size={14} className="text-[#0B0F14]" />
            </div>
            <div>
              <p className="text-[13px] font-semibold leading-tight text-[#E6EAF0]">Mission</p>
              <p className="text-[10px] uppercase tracking-widest leading-tight text-[#8A94A6]">Control</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 space-y-0.5 px-3 py-4">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.label}
              className={`group flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium transition-all ${
                item.active
                  ? "border border-[#C8A24A]/15 bg-[#C8A24A]/10 text-[#C8A24A]"
                  : "text-[#8A94A6] hover:bg-white/4 hover:text-[#E6EAF0]"
              }`}
            >
              <item.icon size={15} className={item.active ? "text-[#C8A24A]" : "text-[#8A94A6] group-hover:text-[#E6EAF0]"} />
              {item.label}
              {item.active && <ChevronRight size={12} className="ml-auto text-[#C8A24A]/60" />}
            </button>
          ))}
        </nav>

        <div className="px-3 pb-2">
          <div className="space-y-0.5 border-t border-white/6 pt-3">
            {SUB_NAV_ITEMS.map((item) => (
              <button
                key={item.label}
                className={`flex w-full items-center gap-2 rounded-lg py-2 pl-7 pr-3 text-[12px] transition-all ${
                  item.active
                    ? "bg-[#C8A24A]/8 text-[#C8A24A]"
                    : "text-[#8A94A6] hover:bg-white/3 hover:text-[#E6EAF0]"
                }`}
              >
                {item.active && <span className="h-1 w-1 shrink-0 rounded-full bg-[#C8A24A]" />}
                {item.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2.5 border-t border-white/6 px-4 py-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-full border border-[#C8A24A]/30 bg-[#C8A24A]/20 text-[11px] font-semibold text-[#C8A24A]">
            JR
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-[12px] font-medium text-[#E6EAF0]">J. Rodriguez</p>
            <p className="text-[10px] text-[#8A94A6]">Fleet Admin</p>
          </div>
          <Settings size={13} className="cursor-pointer text-[#8A94A6] transition-colors hover:text-[#E6EAF0]" />
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="flex h-12 shrink-0 items-center justify-between border-b border-white/6 bg-[#0E141B] px-5">
          <div className="flex items-center gap-2 text-[12px] text-[#8A94A6]">
            <span>Fleet</span>
            <ChevronRight size={12} />
            <span className="text-[#E6EAF0]">Inventory</span>
          </div>
          <div className="flex items-center gap-3">
            <button className="relative text-[#8A94A6] transition-colors hover:text-[#E6EAF0]">
              <Bell size={15} />
              <span className="absolute -top-0.5 -right-0.5 h-1.5 w-1.5 rounded-full bg-[#E5484D]" />
            </button>
            <div className="h-4 w-px bg-white/10" />
            <span className="text-[11px] uppercase tracking-widest text-[#8A94A6]">NORTHERN COMMAND</span>
          </div>
        </header>

        {children}
      </div>
    </div>
  );
}
