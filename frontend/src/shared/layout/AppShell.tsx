import { useState } from "react";
import { Outlet, useLocation } from "react-router";

import type { CurrentUser } from "../types/accounts";
import { cn } from "../utils/cn";
import { navTitleFor } from "./navigation";
import { contentOffsetClass } from "./shellLayout";
import { toRoleCode } from "./shellContext";
import type { ShellContext } from "./shellContext";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

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
        pageTitle={navTitleFor(location.pathname)}
        collapsed={collapsed}
        user={user}
        onMobileMenu={() => setMobileOpen(true)}
      />
      <main
        className={cn(
          "min-h-screen overflow-x-clip pt-14 transition-[padding] duration-200",
          contentOffsetClass(collapsed),
        )}
      >
        <div
          className="mx-auto min-w-0 px-4 py-6 sm:px-6"
          style={{ maxWidth: 1440 }}
        >
          <Outlet context={context} />
        </div>
      </main>
    </div>
  );
}
