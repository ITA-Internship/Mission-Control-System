import { useState } from "react";
import { Outlet, useLocation } from "react-router";

import type { CurrentUser } from "../../auth/types/auth";
import { NAV_ITEMS } from "../rbac";
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

  const role = toRoleCode(user.role_code);
  const context: ShellContext = { user };

  return (
    <div className="min-h-screen bg-mc-bg text-mc-text">
      <Sidebar
        role={role}
        collapsed={collapsed}
        onToggle={() => setCollapsed((value) => !value)}
      />
      <TopBar
        pageTitle={pageTitleFor(location.pathname)}
        collapsed={collapsed}
        user={user}
      />
      <main
        className="min-h-screen transition-all duration-200"
        style={{
          paddingLeft: collapsed ? 64 : 240,
          paddingTop: 56,
        }}
      >
        <div className="mx-auto px-6 py-6" style={{ maxWidth: 1440 }}>
          <Outlet context={context} />
        </div>
      </main>
    </div>
  );
}
