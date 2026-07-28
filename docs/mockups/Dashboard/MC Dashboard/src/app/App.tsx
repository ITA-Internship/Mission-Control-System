/* MARKER-MAKE-KIT-INVOKED */
import { useState, useEffect } from "react";
import { Sidebar } from "./components/Sidebar";
import { TopBar } from "./components/TopBar";
import { KpiTiles } from "./components/KpiTiles";
import { FleetStatusChart } from "./components/FleetStatusChart";
import { MissionsList } from "./components/MissionsList";
import { DefectsPanel } from "./components/DefectsPanel";
import { AuditFeed } from "./components/AuditFeed";
import { cn } from "./components/ui/utils";
import type { Role, User } from "./types";

/* RBAC panel visibility matrix */
const CAN_SEE_FLEET_CHART = new Set<Role>(["Admin", "Commander", "Dispatcher", "Technician", "Viewer"]);
const CAN_SEE_MISSIONS    = new Set<Role>(["Admin", "Commander", "Dispatcher", "Operator", "Viewer"]);
const CAN_SEE_DEFECTS     = new Set<Role>(["Admin", "Commander", "Technician"]);
const CAN_SEE_AUDIT       = new Set<Role>(["Admin", "Commander"]);

const USER_PROFILES: Record<Role, User> = {
  Admin:      { name: "Gen. Harrison",  rank: "Brigadier General",  role: "Admin",      initials: "GH" },
  Commander:  { name: "Col. Vasquez",   rank: "Colonel",            role: "Commander",  initials: "RV" },
  Dispatcher: { name: "Sgt. Adeyemi",  rank: "Staff Sergeant",     role: "Dispatcher", initials: "KA" },
  Operator:   { name: "Cpt. Rourke",   rank: "Captain",            role: "Operator",   initials: "AR" },
  Technician: { name: "Tech. M. Kwan", rank: "Technical Specialist",role: "Technician", initials: "MK" },
  Viewer:     { name: "Lt. Henriksen", rank: "Lieutenant",         role: "Viewer",     initials: "MH" },
};

const PAGE_TITLES: Record<string, string> = {
  dashboard:      "Dashboard",
  drones:         "Drone Fleet",
  missions:       "Missions Board",
  repairs:        "Repairs & Maintenance",
  media:          "Mission Media",
  administration: "Administration",
};

export default function App() {
  const [role, setRole] = useState<Role>("Admin");
  const [collapsed, setCollapsed] = useState(false);
  const [activeNav, setActiveNav] = useState("dashboard");
  const [loading, setLoading] = useState(true);

  /* Simulate initial data load */
  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 1400);
    return () => clearTimeout(t);
  }, []);

  /* Re-trigger loading skeleton when role switches */
  const handleRoleChange = (newRole: Role) => {
    setRole(newRole);
    setLoading(true);
    setTimeout(() => setLoading(false), 800);
  };

  const user = USER_PROFILES[role];
  const sidebarW = collapsed ? 64 : 240;

  const showFleet    = CAN_SEE_FLEET_CHART.has(role);
  const showMissions = CAN_SEE_MISSIONS.has(role);
  const showDefects  = CAN_SEE_DEFECTS.has(role);
  const showAudit    = CAN_SEE_AUDIT.has(role);

  return (
    <div className="min-h-screen bg-background text-foreground" style={{ fontFamily: "'IBM Plex Sans', 'Inter', system-ui, sans-serif" }}>
      {/* Sidebar */}
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed(!collapsed)}
        activeItem={activeNav}
        onNavigate={setActiveNav}
        role={role}
      />

      {/* Top bar */}
      <TopBar
        pageTitle={PAGE_TITLES[activeNav] ?? "Mission Control"}
        sidebarCollapsed={collapsed}
        user={user}
        onRoleChange={handleRoleChange}
      />

      {/* Main content */}
      <main
        className="min-h-screen transition-all duration-200"
        style={{ paddingLeft: `${sidebarW}px`, paddingTop: "56px" }}
      >
        <div className="mx-auto px-6 py-6" style={{ maxWidth: "1440px" }}>

          {/* Dashboard page */}
          {activeNav === "dashboard" && (
            <div className="space-y-5">
              {/* KPI row */}
              <KpiTiles role={role} loading={loading} />

              {/* Content grid */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">

                {/* Left column */}
                <div className="space-y-5">
                  {showFleet && (
                    <FleetStatusChart loading={loading} />
                  )}
                  {showDefects && (
                    <div style={{ minHeight: "320px" }}>
                      <DefectsPanel loading={loading} />
                    </div>
                  )}
                </div>

                {/* Right column */}
                <div className="space-y-5">
                  {showMissions && (
                    <div style={{ minHeight: "280px" }}>
                      <MissionsList loading={loading} />
                    </div>
                  )}
                  {showAudit && (
                    <div style={{ minHeight: "320px" }}>
                      <AuditFeed loading={loading} />
                    </div>
                  )}

                  {/* Operator reduced view — show only their assigned info */}
                  {!showAudit && !showDefects && (
                    <OperatorHint role={role} />
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Placeholder pages */}
          {activeNav !== "dashboard" && (
            <PlaceholderPage title={PAGE_TITLES[activeNav] ?? activeNav} />
          )}
        </div>
      </main>
    </div>
  );
}

/* Reduced-privilege notice shown to Operator/Viewer on the right column */
function OperatorHint({ role }: { role: Role }) {
  return (
    <div className="rounded-xl border border-border p-8 flex flex-col items-center justify-center gap-3" style={{ background: "var(--card)" }}>
      <div className="w-10 h-10 rounded-xl bg-[#C8A24A]/10 flex items-center justify-center">
        <svg className="w-5 h-5 text-[#C8A24A]" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
        </svg>
      </div>
      <div className="text-center">
        <p className="text-[13px] font-semibold text-[#E6EAF0]">Restricted access</p>
        <p className="font-mono text-[11px] text-[#8A94A6] mt-1">
          {role} role does not have permission to view audit logs or defect data.
        </p>
      </div>
    </div>
  );
}

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
      <div className="w-16 h-16 rounded-2xl border border-border flex items-center justify-center" style={{ background: "var(--card)" }}>
        <svg className="w-8 h-8 text-[#8A94A6]" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
        </svg>
      </div>
      <div className="text-center">
        <h2 className="text-[16px] font-semibold text-[#E6EAF0]">{title}</h2>
        <p className="font-mono text-[12px] text-[#8A94A6] mt-1">Page not yet implemented in this prototype</p>
      </div>
    </div>
  );
}
