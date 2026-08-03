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

import type { CurrentUser } from "../../auth/types/auth";
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
  onSignOut: () => void;
  signingOut: boolean;
  children: ReactNode;
}) {
  return (
    <div
      className="flex h-screen overflow-hidden"
      style={{
        background: "#0B0F14",
        fontFamily:
          "'Inter', -apple-system, sans-serif",
      }}
    >
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-60 flex-col border-r transition-transform duration-200 lg:static lg:z-auto lg:translate-x-0 ${
          sidebarOpen
            ? "translate-x-0"
            : "-translate-x-full"
        }`}
        style={{
          background: "#0D1219",
          borderColor:
            "rgba(255,255,255,.07)",
        }}
      >
        <div
          className="flex h-14 shrink-0 items-center gap-3 border-b px-5"
          style={{
            borderColor:
              "rgba(255,255,255,.07)",
          }}
        >
          <div
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded"
            style={{
              background:
                "rgba(200,162,74,.13)",
              border:
                "1px solid rgba(200,162,74,.28)",
            }}
          >
            <Crosshair
              size={14}
              style={{
                color: "#C8A24A",
              }}
            />
          </div>
          <div className="leading-none">
            <div
              className="text-xs font-bold uppercase tracking-widest"
              style={{
                color: "#E6EAF0",
              }}
            >
              Mission
            </div>
            <div
              className="mt-0.5 text-[10px] tracking-widest"
              style={{
                color: "#8A94A6",
              }}
            >
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
          <p
            className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest"
            style={{
              color: "#4A5568",
            }}
          >
            Navigation
          </p>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.label}
                type="button"
                className="mb-0.5 flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-all"
                style={{
                  color: "#8A94A6",
                  background: "transparent",
                }}
              >
                <Icon size={15} />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div
          className="border-t px-4 py-4"
          style={{
            borderColor:
              "rgba(255,255,255,.07)",
          }}
        >
          <div className="flex items-center gap-3">
            <div
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold"
              style={{
                background:
                  "rgba(200,162,74,.13)",
                color: "#C8A24A",
                border:
                  "1px solid rgba(200,162,74,.25)",
              }}
            >
              {getInitials(currentUser)}
            </div>
            <div className="min-w-0">
              <div
                className="truncate text-xs font-semibold"
                style={{
                  color: "#E6EAF0",
                }}
              >
                {currentUser.rank
                  ? `${currentUser.rank} ${currentUser.first_name?.[0]}. ${currentUser.last_name}`
                  : `${currentUser.first_name} ${currentUser.last_name}`}
              </div>
              <div
                className="truncate text-xs"
                style={{
                  color: "#8A94A6",
                }}
              >
                {getUnitLabel(currentUser)}
              </div>
            </div>
          </div>
        </div>
      </aside>

      {sidebarOpen ? (
        <div
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
          onClick={onCloseSidebar}
        />
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <header
          className="flex h-14 shrink-0 items-center justify-between border-b px-5"
          style={{
            background: "#0D1219",
            borderColor:
              "rgba(255,255,255,.07)",
          }}
        >
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="lg:hidden"
              onClick={onToggleSidebar}
              style={{
                color: "#8A94A6",
              }}
              aria-label="Toggle navigation"
            >
              <LayoutDashboard size={20} />
            </button>
            <nav
              className="flex items-center gap-1.5 text-xs"
              style={{
                color: "#8A94A6",
              }}
            >
              <span>Home</span>
              <ChevronRight size={11} />
              <span
                style={{
                  color: "#E6EAF0",
                }}
              >
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
                className="flex items-center gap-2 rounded-lg px-3 py-1.5 transition-all"
                style={{
                  background:
                    "rgba(255,255,255,.04)",
                  border:
                    "1px solid rgba(255,255,255,.08)",
                }}
                aria-haspopup="menu"
                aria-expanded={userMenuOpen}
                aria-label="Open account menu"
              >
                <div
                  className="relative flex h-6 w-6 items-center justify-center overflow-hidden rounded-full text-xs font-bold"
                  style={{
                    background:
                      "rgba(200,162,74,.13)",
                    color: "#C8A24A",
                  }}
                >
                  <span aria-hidden={Boolean(avatarDisplay)}>
                    {getInitials(currentUser)}
                  </span>
                  <ProfileAvatarImage
                    source={avatarDisplay}
                    alt="Profile avatar"
                    className="absolute inset-0 h-full w-full object-cover"
                  />
                </div>
                <span
                  className="hidden text-xs font-medium sm:block"
                  style={{
                    color: "#E6EAF0",
                  }}
                >
                  {currentUser.rank
                    ? `${currentUser.rank} ${currentUser.last_name}`
                    : `${currentUser.first_name} ${currentUser.last_name}`}
                </span>
                <ChevronDown
                  size={12}
                  style={{
                    color: "#8A94A6",
                  }}
                />
              </button>

              {userMenuOpen ? (
                <div
                  className="absolute right-0 top-full z-50 mt-2 w-56 overflow-hidden rounded-xl border shadow-2xl"
                  style={{
                    background: "#161D26",
                    borderColor:
                      "rgba(255,255,255,.1)",
                  }}
                >
                  <div
                    className="border-b px-4 py-3"
                    style={{
                      borderColor:
                        "rgba(255,255,255,.07)",
                    }}
                  >
                    <div
                      className="text-sm font-semibold"
                      style={{
                        color: "#E6EAF0",
                      }}
                    >
                      {currentUser.first_name}{" "}
                      {currentUser.last_name}
                    </div>
                    <div
                      className="mt-0.5 text-xs font-mono"
                      style={{
                        color: "#8A94A6",
                      }}
                    >
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
                      className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm transition-all"
                      style={{
                        color: "#E6EAF0",
                      }}
                    >
                      <User
                        size={13}
                        style={{
                          color: "#C8A24A",
                        }}
                      />
                      My Profile
                    </button>
                    <button
                      type="button"
                      className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm transition-all"
                      style={{
                        color: "#E6EAF0",
                      }}
                    >
                      <Settings
                        size={13}
                        style={{
                          color: "#8A94A6",
                        }}
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
