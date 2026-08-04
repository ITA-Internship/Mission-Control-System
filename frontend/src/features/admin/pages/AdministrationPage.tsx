import {
  useCallback,
  useState,
} from "react";
import {
  Building2,
  RefreshCw,
  ScrollText,
  Shield,
  Users,
} from "lucide-react";
import {
  Navigate,
  useOutletContext,
  useSearchParams,
} from "react-router";
import type { LucideIcon } from "lucide-react";

import { Button } from "../components/Button";
import { AuditLogTab } from "../tabs/AuditLogTab";
import { UnitsTab } from "../tabs/UnitsTab";
import { UsersTab } from "../tabs/UsersTab";
import { useAdminCatalog } from "../hooks/useAdminCatalog";
import { toRoleCode } from "../../../shared/layout/shellContext";
import type { ShellContext } from "../../../shared/layout/shellContext";

type TabId = "users" | "units" | "audit";

interface TabDefinition {
  id: TabId;
  label: string;
  icon: LucideIcon;
}

const TABS: TabDefinition[] = [
  {
    id: "users",
    label: "Users",
    icon: Users,
  },
  {
    id: "units",
    label: "Military Units",
    icon: Building2,
  },
  {
    id: "audit",
    label: "Audit Log",
    icon: ScrollText,
  },
];

function resolveTab(
  value: string | null,
): TabId {
  return (
    TABS.find((tab) => tab.id === value)?.id ??
    "users"
  );
}

/**
 * Route entry for `/administration`.
 *
 * The console belongs to the Admin role: the sidebar offers the destination to
 * admins only, so this covers the deep-link case (typed URL, stale bookmark) by
 * sending everyone else back to the dashboard. Nothing renders and no
 * administration request is fired for a non-admin.
 */
export function AdministrationPage() {
  const context =
    useOutletContext<ShellContext | null>();

  const role = toRoleCode(
    context?.user.role_code,
  );

  if (role !== "ADMIN") {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    );
  }

  return <AdministrationConsole />;
}

function AdministrationConsole() {
  const [searchParams, setSearchParams] =
    useSearchParams();

  const activeTab = resolveTab(
    searchParams.get("tab"),
  );

  const [reloadSignal, setReloadSignal] =
    useState(0);

  const [isOffline, setIsOffline] =
    useState(false);

  const catalog = useAdminCatalog();

  const handleNetworkStateChange =
    useCallback((offline: boolean) => {
      setIsOffline(offline);
    }, []);

  function selectTab(tabId: TabId) {
    setSearchParams(
      (params) => {
        const next = new URLSearchParams(
          params,
        );

        next.set("tab", tabId);

        return next;
      },
      { replace: true },
    );
  }

  function handleTabKeyDown(
    event: React.KeyboardEvent,
    index: number,
  ) {
    if (
      event.key !== "ArrowRight" &&
      event.key !== "ArrowLeft"
    ) {
      return;
    }

    event.preventDefault();

    const offset =
      event.key === "ArrowRight" ? 1 : -1;

    const nextIndex =
      (index + offset + TABS.length) %
      TABS.length;

    selectTab(TABS[nextIndex].id);
  }

  function handleRefresh() {
    setReloadSignal(
      (signal) => signal + 1,
    );

    catalog.reload();
  }

  return (
    <div className="flex w-full flex-col">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-mc-text">
            Administration
          </h1>

          <p className="mt-0.5 font-mono text-xs text-mc-muted">
            Restricted — Admin role only
          </p>
        </div>

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
            isLoading={catalog.isLoading}
            onClick={handleRefresh}
          >
            Refresh
          </Button>

          <p className="flex items-center gap-2 rounded-lg border border-mc-error/20 bg-mc-error/8 px-3 py-1.5 text-xs font-medium tracking-wide text-mc-error uppercase">
            <Shield
              size={14}
              aria-hidden="true"
            />
            Restricted access
          </p>
        </div>
      </div>

      <div
        className="mc-scroll mb-5 flex items-center overflow-x-auto border-b border-white/7"
        role="tablist"
        aria-label="Administration sections"
      >
        {TABS.map((tab, index) => {
          const Icon = tab.icon;
          const isActive =
            tab.id === activeTab;

          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              id={`admin-tab-${tab.id}`}
              aria-selected={isActive}
              aria-controls={`admin-panel-${tab.id}`}
              tabIndex={isActive ? 0 : -1}
              onClick={() =>
                selectTab(tab.id)
              }
              onKeyDown={(event) =>
                handleTabKeyDown(
                  event,
                  index,
                )
              }
              className={[
                "relative inline-flex items-center gap-2 px-4 py-3 sm:px-5",
                "text-sm font-medium whitespace-nowrap transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-mc-accent/40",
                isActive
                  ? "text-mc-accent"
                  : "text-mc-muted hover:text-mc-text",
              ].join(" ")}
            >
              <Icon
                size={14}
                aria-hidden="true"
              />

              {tab.label}

              {isActive ? (
                <span
                  className="absolute inset-x-0 bottom-0 h-0.5 rounded-t bg-mc-accent"
                  aria-hidden="true"
                />
              ) : null}
            </button>
          );
        })}
      </div>

      <div
        role="tabpanel"
        id={`admin-panel-${activeTab}`}
        aria-labelledby={`admin-tab-${activeTab}`}
      >
        {activeTab === "users" ? (
          <UsersTab
            catalog={catalog}
            reloadSignal={reloadSignal}
            onNetworkStateChange={
              handleNetworkStateChange
            }
          />
        ) : null}

        {activeTab === "units" ? (
          <UnitsTab
            reloadSignal={reloadSignal}
            onNetworkStateChange={
              handleNetworkStateChange
            }
            onUnitsChanged={catalog.reload}
          />
        ) : null}

        {activeTab === "audit" ? (
          <AuditLogTab
            reloadSignal={reloadSignal}
            onNetworkStateChange={
              handleNetworkStateChange
            }
          />
        ) : null}
      </div>
    </div>
  );
}
