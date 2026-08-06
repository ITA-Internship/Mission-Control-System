import {
  ChevronDown,
  ChevronRight,
  Crosshair,
  LayoutDashboard,
  LogOut,
  Navigation2,
  Settings,
  Target,
  User,
  Users,
  Wrench,
} from "lucide-react";
import type {
  ReactNode,
  RefObject,
} from "react";

import { cn } from "../../../shared/utils/cn";
import type { CurrentUser } from "../../../shared/types/accounts";
import {
  ProfileAvatarImage,
  RoleBadge,
  UnitChip,
} from "./ProfilePrimitives";
import {
  getInitials,
  getRoleLabel,
  getUnitLabel,
} from "../utils/profileUtils";

const NAV_ITEMS = [
  {
    icon: LayoutDashboard,
    label: "Dashboard",
  },
  {
    icon: Navigation2,
    label: "Drone Fleet",
  },
  {
    icon: Target,
    label: "Missions",
  },
  {
    icon: Users,
    label: "Operators",
  },
  {
    icon: Wrench,
    label: "Maintenance",
  },
  {
    icon: Settings,
    label: "Settings",
  },
];

export function ProfileWorkspaceLayout({
  currentUser,
  avatarDisplay,
  sidebarOpen,
  userMenuOpen,
  menuRef,
  onToggleSidebar,
  onCloseSidebar,
  onToggleUserMenu,
  onOpenProfile,
  onOpenSettings,
  onSignOut,
  signingOut,
  children,
}: {
  currentUser: CurrentUser;
  avatarDisplay: string | null;
  sidebarOpen: boolean;
  userMenuOpen: boolean;
  menuRef: RefObject<HTMLDivElement | null>;
  onToggleSidebar: () => void;
  onCloseSidebar: () => void;
  onToggleUserMenu: () => void;
  onOpenProfile: () => void;
  onOpenSettings: () => void;
  onSignOut: () => void;
  signingOut: boolean;
  children: ReactNode;
}) {
  return (
    <div className="flex h-screen overflow-hidden bg-mc-bg">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-60 flex-col border-r border-mc-border bg-mc-sidebar transition-transform duration-200 lg:static lg:z-auto lg:translate-x-0",
          sidebarOpen
            ? "translate-x-0"
            : "-translate-x-full",
        )}
      >
        <div className="flex h-14 shrink-0 items-center gap-3 border-b border-mc-border px-5">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded border border-mc-accent/[0.28] bg-mc-accent/[0.13]">
            <Crosshair
              size={14}
              className="text-mc-accent"
            />
          </div>
          <div className="leading-none">
            <div className="text-xs font-bold uppercase tracking-widest text-mc-text">
              Mission
            </div>
            <div className="mt-0.5 text-[10px] tracking-widest text-mc-muted">
              CONTROL SYSTEM
            </div>
          </div>
        </div>

        <nav
          className="flex-1 overflow-y-auto px-2 py-3"
          style={{
            scrollbarWidth: "none",
          }}
        >
          <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-mc-subtle">
            Navigation
          </p>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.label}
                type="button"
                onClick={
                  item.label === "Settings"
                    ? onOpenSettings
                    : undefined
                }
                aria-label={
                  item.label === "Settings"
                    ? "Open profile settings from navigation"
                    : undefined
                }
                className="mb-0.5 flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm text-mc-muted transition-colors hover:bg-white/5 hover:text-mc-text"
              >
                <Icon size={15} />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="border-t border-mc-border px-4 py-4">
          <button
            type="button"
            onClick={onOpenProfile}
            aria-label="Open my profile from sidebar"
            className="flex w-full items-center gap-3 rounded-lg p-1 text-left transition-colors hover:bg-white/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mc-accent"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-mc-accent/25 bg-mc-accent/[0.13] text-xs font-bold text-mc-accent">
              {getInitials(currentUser)}
            </div>
            <div className="min-w-0">
              <div className="truncate text-xs font-semibold text-mc-text">
                {currentUser.rank
                  ? `${currentUser.rank} ${currentUser.first_name?.[0]}. ${currentUser.last_name}`
                  : `${currentUser.first_name} ${currentUser.last_name}`}
              </div>
              <div className="truncate text-xs text-mc-muted">
                {getUnitLabel(currentUser)}
              </div>
            </div>
          </button>
        </div>
      </aside>

      {sidebarOpen ? (
        <div
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
          onClick={onCloseSidebar}
        />
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-mc-border bg-mc-sidebar px-5">
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="text-mc-muted lg:hidden"
              onClick={onToggleSidebar}
              aria-label="Toggle navigation"
            >
              <LayoutDashboard size={20} />
            </button>
            <nav className="flex items-center gap-1.5 text-xs text-mc-muted">
              <span>Home</span>
              <ChevronRight size={11} />
              <span className="text-mc-text">
                My Profile
              </span>
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <div
              className="relative"
              ref={menuRef}
            >
              <button
                type="button"
                onClick={onToggleUserMenu}
                className="flex items-center gap-2 rounded-lg border border-white/8 bg-white/[0.04] px-3 py-1.5 transition-colors hover:bg-white/[0.08]"
                aria-haspopup="menu"
                aria-expanded={userMenuOpen}
                aria-label="Open account menu"
              >
                <div className="relative flex h-6 w-6 items-center justify-center overflow-hidden rounded-full bg-mc-accent/[0.13] text-xs font-bold text-mc-accent">
                  <span aria-hidden={Boolean(avatarDisplay)}>
                    {getInitials(currentUser)}
                  </span>
                  <ProfileAvatarImage
                    source={avatarDisplay}
                    alt="Profile avatar"
                    className="absolute inset-0 h-full w-full object-cover"
                  />
                </div>
                <span className="hidden text-xs font-medium text-mc-text sm:block">
                  {currentUser.rank
                    ? `${currentUser.rank} ${currentUser.last_name}`
                    : `${currentUser.first_name} ${currentUser.last_name}`}
                </span>
                <ChevronDown
                  size={12}
                  className="text-mc-muted"
                />
              </button>

              {userMenuOpen ? (
                <div className="absolute right-0 top-full z-50 mt-2 w-56 overflow-hidden rounded-xl border border-white/10 bg-mc-card shadow-2xl">
                  <div className="border-b border-mc-border px-4 py-3">
                    <div className="text-sm font-semibold text-mc-text">
                      {currentUser.first_name}{" "}
                      {currentUser.last_name}
                    </div>
                    <div className="mt-0.5 font-mono text-xs text-mc-muted">
                      {currentUser.email}
                    </div>
                    <div className="mt-2 flex items-center gap-2">
                      <RoleBadge
                        role={getRoleLabel(
                          currentUser,
                        )}
                      />
                      <UnitChip
                        unit={getUnitLabel(
                          currentUser,
                        )}
                      />
                    </div>
                  </div>
                  <div className="p-2">
                    <button
                      type="button"
                      onClick={onOpenProfile}
                      aria-label="Open my profile"
                      className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm text-mc-text transition-colors hover:bg-white/5"
                    >
                      <User
                        size={13}
                        className="text-mc-accent"
                      />
                      My Profile
                    </button>
                    <button
                      type="button"
                      onClick={onOpenSettings}
                      aria-label="Open profile settings"
                      className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm text-mc-text transition-colors hover:bg-white/5"
                    >
                      <Settings
                        size={13}
                        className="text-mc-muted"
                      />
                      Settings
                    </button>
                    <div
                      className="my-1 border-t"
                      style={{
                        borderColor:
                          "rgba(255,255,255,.07)",
                      }}
                    />
                    <button
                      type="button"
                      onClick={onSignOut}
                      disabled={signingOut}
                      className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm transition-all"
                      style={{
                        color: "#E5484D",
                      }}
                    >
                      <LogOut size={13} />
                      {signingOut
                        ? "Signing Out..."
                        : "Sign Out"}
                    </button>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        </header>

        <main
          className="flex-1 overflow-y-auto"
          style={{
            scrollbarWidth: "none",
          }}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
