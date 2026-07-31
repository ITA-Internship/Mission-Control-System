import { AuditFeed } from "../components/AuditFeed";
import { DefectsPanel } from "../components/DefectsPanel";
import { FleetStatusChart } from "../components/FleetStatusChart";
import { KpiTiles } from "../components/KpiTiles";
import { MissionsList } from "../components/MissionsList";
import { Panel } from "../components/Panel";
import { RestrictedState } from "../components/states";
import { useDashboardData } from "../hooks/useDashboardData";
import {
  CAN_SEE_AUDIT,
  CAN_SEE_DEFECTS,
  CAN_SEE_FLEET_CHART,
  CAN_SEE_MISSIONS,
} from "../rbac";
import { toRoleCode } from "../shellContext";
import { useShellContext } from "../shellContext";

export function DashboardPage() {
  const { user } = useShellContext();
  const role = toRoleCode(user.role_code);
  const { summary, missions, defects, audit } =
    useDashboardData(role);

  if (!role) {
    return (
      <Panel>
        <RestrictedState description="No role is assigned to your account. Contact an administrator." />
      </Panel>
    );
  }

  const showFleet = CAN_SEE_FLEET_CHART.has(role);
  const showMissions = CAN_SEE_MISSIONS.has(role);
  const showDefects = CAN_SEE_DEFECTS.has(role);
  const showAudit = CAN_SEE_AUDIT.has(role);
  const showReducedNotice = !showAudit && !showDefects;

  return (
    <div className="space-y-5">
      <KpiTiles role={role} summary={summary} />

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        {/* Left column */}
        <div className="space-y-5">
          {showFleet && (
            <FleetStatusChart
              fleet={summary.data?.fleet ?? null}
              loading={summary.status === "loading"}
              error={summary.status === "error"}
            />
          )}
          {showDefects && <DefectsPanel state={defects} />}
        </div>

        {/* Right column */}
        <div className="space-y-5">
          {showMissions && <MissionsList state={missions} />}
          {showAudit && <AuditFeed state={audit} />}
          {showReducedNotice && (
            <Panel>
              <RestrictedState description={`${role} role does not have permission to view audit logs or defect data.`} />
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}
