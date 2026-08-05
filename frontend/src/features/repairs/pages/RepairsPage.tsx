import {
  useCallback,
  useRef,
  useState,
} from "react";
import {
  ClipboardList,
  Package,
  RefreshCw,
  Wrench,
} from "lucide-react";
import {
  Navigate,
  NavLink,
  Outlet,
} from "react-router";
import type { LucideIcon } from "lucide-react";

import { Button } from "../../admin/components/Button";
import { RepairsKpiCards } from "../components/RepairsKpiCards";
import { useRepairsStats } from "../hooks/useRepairsStats";
import { CAN_VIEW_REPAIRS } from "../rbac";
import {
  toRoleCode,
  useShellContext,
} from "../../../shared/layout/shellContext";

type TabId = "defects" | "orders" | "replacements";

interface TabDefinition {
  id: TabId;
  label: string;
  icon: LucideIcon;
  path: string;
}

const TABS: TabDefinition[] = [
  {
    id: "defects",
    label: "Defects",
    icon: Wrench,
    path: "/repairs/defects",
  },
  {
    id: "orders",
    label: "Repair Orders",
    icon: ClipboardList,
    path: "/repairs/orders",
  },
  {
    id: "replacements",
    label: "Component Replacements",
    icon: Package,
    path: "/repairs/replacements",
  },
];

export function RepairsPage() {
  const { user } = useShellContext();
  const role = toRoleCode(user.role_code);

  if (!role || !CAN_VIEW_REPAIRS.has(role)) {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    );
  }

  return <RepairsConsole role={role} />;
}

function RepairsConsole({
  role,
}: {
  role: NonNullable<ReturnType<typeof toRoleCode>>;
}) {
  const [reloadSignal, setReloadSignal] = useState(0);
  const [isOffline, setIsOffline] = useState(false);

  const { stats, isLoading: statsLoading } =
    useRepairsStats(reloadSignal);

  const tabRefs = useRef<
    Array<HTMLAnchorElement | null>
  >([]);

  const handleNetworkStateChange = useCallback(
    (offline: boolean) => {
      setIsOffline(offline);
    },
    [],
  );

  const handleDataChanged = useCallback(() => {
    setReloadSignal((signal) => signal + 1);
  }, []);

  function handleRefresh() {
    setReloadSignal((signal) => signal + 1);
  }

  function handleTabKeyDown(
    event: React.KeyboardEvent,
    index: number,
  ) {
    let nextIndex: number;

    switch (event.key) {
      case "ArrowRight":
        nextIndex = (index + 1) % TABS.length;
        break;
      case "ArrowLeft":
        nextIndex =
          (index - 1 + TABS.length) % TABS.length;
        break;
      case "Home":
        nextIndex = 0;
        break;
      case "End":
        nextIndex = TABS.length - 1;
        break;
      default:
        return;
    }

    event.preventDefault();
    tabRefs.current[nextIndex]?.click();
    tabRefs.current[nextIndex]?.focus();
  }

  return (
    <div className="flex w-full flex-col">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-mc-text">
            Repairs & Maintenance
          </h1>
          <p className="mt-0.5 max-w-xl text-sm text-mc-muted">
            Defect tracking, repair orders, and component
            lifecycle management.
          </p>
        </div>

        <div className="flex flex-col items-end gap-3">
          <RepairsKpiCards
            openDefects={stats.openDefects}
            criticalDefects={stats.criticalDefects}
            activeOrders={stats.activeOrders}
            isLoading={statsLoading}
          />

          <div className="flex flex-wrap items-center gap-2">
            {isOffline ? (
              <p
                className="flex items-center gap-1.5 rounded px-2.5 py-1 font-mono text-[11px] tracking-wider text-mc-error"
                role="status"
              >
                <span
                  className="size-1.5 rounded-full bg-current"
                  aria-hidden="true"
                />
                LINK DEGRADED
              </p>
            ) : null}

            <Button
              variant="secondary"
              icon={
                <RefreshCw
                  size={14}
                  aria-hidden="true"
                />
              }
              isLoading={statsLoading}
              onClick={handleRefresh}
            >
              Refresh
            </Button>
          </div>
        </div>
      </div>

      <div
        className="mc-scroll mb-5 flex items-center overflow-x-auto border-b border-white/7"
        role="tablist"
        aria-label="Repairs sections"
      >
        {TABS.map((tab, index) => {
          const Icon = tab.icon;

          return (
            <NavLink
              key={tab.id}
              to={tab.path}
              end
              role="tab"
              ref={(element) => {
                tabRefs.current[index] = element;
              }}
              id={`repairs-tab-${tab.id}`}
              aria-controls={`repairs-panel-${tab.id}`}
              onKeyDown={(event) =>
                handleTabKeyDown(event, index)
              }
              className={({ isActive }) =>
                [
                  "relative inline-flex items-center gap-2 px-4 py-3 sm:px-5",
                  "text-sm font-medium whitespace-nowrap transition-colors",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-mc-accent/40",
                  isActive
                    ? "text-mc-accent"
                    : "text-mc-muted hover:text-mc-text",
                ].join(" ")
              }
            >
              {({ isActive }) => (
                <>
                  <Icon size={14} aria-hidden="true" />
                  {tab.label}
                  {isActive ? (
                    <span
                      className="absolute inset-x-0 bottom-0 h-0.5 rounded-t bg-mc-accent"
                      aria-hidden="true"
                    />
                  ) : null}
                </>
              )}
            </NavLink>
          );
        })}
      </div>

      <div role="tabpanel">
        <Outlet
          context={{
            reloadSignal,
            onNetworkStateChange: handleNetworkStateChange,
            onDataChanged: handleDataChanged,
            role,
          }}
        />
      </div>
    </div>
  );
}

export interface RepairsOutletContext {
  reloadSignal: number;
  onNetworkStateChange: (isOffline: boolean) => void;
  onDataChanged: () => void;
  role: NonNullable<ReturnType<typeof toRoleCode>>;
}
