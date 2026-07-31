import { useState } from "react";
import { Outlet, useLocation } from "react-router";

import { cn } from "../../../shared/utils/cn";
import type { CurrentUser } from "../../auth/types/auth";
import { NAV_ITEMS } from "../rbac";
import { contentOffsetClass } from "../shellLayout";
import { toRoleCode } from "../shellContext";
import type { ShellContext } from "../shellContext";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

function pageTitleFor(pathname: string): string {
  const match = NAV_ITEMS.find((item) =>
    pathname.startsWith(item.path),
  );
  return match?.label ?? "Mission Control";
}

export function AppShell({ user }: { user: CurrentUser }) {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const role = toRoleCode(user.role_code);
  const context: ShellContext = { user };

  return (
    <div className="min-h-screen bg-mc-bg text-mc-text">
      <Sidebar
        role={role}
        collapsed={collapsed}
        onToggle={() => setCollapsed((value) => !value)}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />
      <TopBar
        pageTitle={pageTitleFor(location.pathname)}
        collapsed={collapsed}
        user={user}
        onMobileMenu={() => setMobileOpen(true)}
      />
      <main
        className={cn(
          "min-h-screen pt-14 transition-[padding] duration-200",
          contentOffsetClass(collapsed),
        )}
      >
        <div className="mx-auto px-6 py-6" style={{ maxWidth: 1440 }}>
          <Outlet context={context} />
        </div>
      </main>
    </div>
  );
}
