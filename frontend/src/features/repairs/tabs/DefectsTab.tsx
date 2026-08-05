import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Plus, Search } from "lucide-react";

import { ActiveFilterChips } from "../../admin/components/ActiveFilterChips";
import { Button } from "../../admin/components/Button";
import { FilterSelect } from "../../admin/components/FilterSelect";
import { Pagination } from "../../admin/components/Pagination";
import { TablePanel } from "../../admin/components/TablePanel";
import { HeaderCell } from "../../admin/components/TableHeaderCell";
import {
  TableEmptyState,
  TableErrorState,
  TableSkeleton,
} from "../../admin/components/TableStates";
import { TextField } from "../../admin/components/FormFields";
import { SeverityPill } from "../../../shared/components/StatusPill";
import { NetworkError } from "../../../shared/api/apiClient";
import { useAsyncData } from "../../../shared/hooks/useAsyncData";
import { useShellContext } from "../../../shared/layout/shellContext";
import { toRoleCode } from "../../../shared/layout/shellContext";
import { humanizeEnum } from "../../../shared/utils/format";
import { formatDateTime } from "../../admin/utils/adminFormat";
import { fetchDefects } from "../api/repairsApi";
import { DefectDrawer } from "../components/DefectDrawer";
import { ReportDefectModal } from "../components/modals/ReportDefectModal";
import {
  DEFECT_STATUS_OPTIONS,
  DEFECT_TYPE_OPTIONS,
  REPAIRS_PAGE_SIZE,
  SEVERITY_OPTIONS,
} from "../constants/repairsCatalog";
import { CAN_CREATE_REPAIRS } from "../rbac";
import {
  formatDefectId,
  formatDroneLabel,
  formatUserLabel,
} from "../utils/repairsFormat";
import {
  describeTableError,
  REPAIRS_ENDPOINTS,
} from "../utils/repairsErrors";

interface DefectsTabProps {
  reloadSignal: number;
  onNetworkStateChange: (isOffline: boolean) => void;
  onDataChanged: () => void;
}

export function DefectsTab({
  reloadSignal,
  onNetworkStateChange,
  onDataChanged,
}: DefectsTabProps) {
  const { user } = useShellContext();
  const role = toRoleCode(user.role_code);

  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const [defectType, setDefectType] = useState("");
  const [droneFilter, setDroneFilter] = useState("");
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const droneId = droneFilter.trim()
    ? Number(droneFilter)
    : undefined;

  const load = useCallback(
    (signal: AbortSignal) => {
      void reloadSignal;

      return fetchDefects(
        {
          page,
          pageSize: REPAIRS_PAGE_SIZE,
          severity: severity || undefined,
          status: status || undefined,
          defectType: defectType || undefined,
          drone:
            droneId !== undefined && !Number.isNaN(droneId)
              ? droneId
              : undefined,
          ordering: "-detected_at",
        },
        signal,
      );
    },
    [
      defectType,
      droneId,
      page,
      reloadSignal,
      severity,
      status,
    ],
  );

  const { data, error, isLoading, reload } =
    useAsyncData(load);

  useEffect(() => {
    onNetworkStateChange(error instanceof NetworkError);
  }, [error, onNetworkStateChange]);

  function changeFilter(apply: () => void) {
    apply();
    setPage(1);
  }

  const activeFilters = useMemo(
    () =>
      [
        severity
          ? {
              key: "severity",
              label: `Severity: ${severity}`,
              onRemove: () =>
                changeFilter(() => setSeverity("")),
            }
          : null,
        status
          ? {
              key: "status",
              label: `Status: ${humanizeEnum(status)}`,
              onRemove: () =>
                changeFilter(() => setStatus("")),
            }
          : null,
        defectType
          ? {
              key: "defectType",
              label: `Type: ${humanizeEnum(defectType)}`,
              onRemove: () =>
                changeFilter(() => setDefectType("")),
            }
          : null,
        droneFilter.trim()
          ? {
              key: "drone",
              label: `Drone: #${droneFilter.trim()}`,
              onRemove: () =>
                changeFilter(() => setDroneFilter("")),
            }
          : null,
      ].filter(
        (filter): filter is NonNullable<typeof filter> =>
          filter !== null,
      ),
    [defectType, droneFilter, severity, status],
  );

  const tableError = error
    ? describeTableError(
        error,
        "Defects",
        REPAIRS_ENDPOINTS.defects,
      )
    : null;

  const canCreate =
    role !== null && CAN_CREATE_REPAIRS.has(role);

  function handleCreated() {
    reload();
    onDataChanged();
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-2">
        <TextField
          id="defects-drone-filter"
          label="Drone ID"
          type="number"
          value={droneFilter}
          placeholder="Any"
          onChange={(value) =>
            changeFilter(() =>
              setDroneFilter(value),
            )
          }
        />

        <FilterSelect
          id="defects-severity-filter"
          label="Severity"
          value={severity}
          placeholder="Severity"
          options={SEVERITY_OPTIONS}
          onChange={(value) =>
            changeFilter(() => setSeverity(value))
          }
        />

        <FilterSelect
          id="defects-status-filter"
          label="Status"
          value={status}
          placeholder="Status"
          options={DEFECT_STATUS_OPTIONS}
          onChange={(value) =>
            changeFilter(() => setStatus(value))
          }
        />

        <FilterSelect
          id="defects-type-filter"
          label="Defect type"
          value={defectType}
          placeholder="Type"
          options={DEFECT_TYPE_OPTIONS}
          onChange={(value) =>
            changeFilter(() => setDefectType(value))
          }
        />

        {canCreate ? (
          <div className="ms-auto">
            <Button
              icon={<Plus size={14} aria-hidden="true" />}
              onClick={() => setIsCreateOpen(true)}
            >
              Report Defect
            </Button>
          </div>
        ) : null}
      </div>

      <ActiveFilterChips
        filters={activeFilters}
        onClearAll={() =>
          changeFilter(() => {
            setSeverity("");
            setStatus("");
            setDefectType("");
            setDroneFilter("");
          })
        }
      />

      <TablePanel
        label="Defects"
        footer={
          <Pagination
            page={page}
            pageSize={REPAIRS_PAGE_SIZE}
            count={data?.count ?? 0}
            note={
              <span className="font-mono text-[10px] tracking-wider uppercase">
                {data?.count ?? 0} defects
              </span>
            }
            onChange={setPage}
          />
        }
      >
        <table className="min-w-full border-collapse text-sm">
          <thead className="border-b border-white/7 bg-mc-panel/60">
            <tr>
              <HeaderCell>Drone</HeaderCell>
              <HeaderCell>Defect type</HeaderCell>
              <HeaderCell>Severity</HeaderCell>
              <HeaderCell>Detected at</HeaderCell>
              <HeaderCell>Reporter</HeaderCell>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <TableSkeleton columns={5} rows={6} />
            ) : tableError ? (
              <TableErrorState
                colSpan={5}
                error={tableError}
                onRetry={reload}
              />
            ) : !data?.results.length ? (
              <TableEmptyState
                colSpan={5}
                icon={Search}
                title="No defects found"
                hint="Adjust filters or report a new defect."
              />
            ) : (
              data.results.map((defect) => (
                <tr
                  key={defect.id}
                  className="cursor-pointer border-b border-white/5 transition-colors hover:bg-white/3"
                  onClick={() => setSelectedId(defect.id)}
                >
                  <td className="px-4 py-3">
                    <p className="font-medium text-mc-text">
                      {formatDroneLabel(defect.drone)}
                    </p>
                    <p className="font-mono text-[10px] text-mc-muted">
                      {formatDefectId(defect.id)}
                    </p>
                  </td>
                  <td className="px-4 py-3 text-mc-text">
                    {humanizeEnum(defect.defect_type)}
                  </td>
                  <td className="px-4 py-3">
                    <SeverityPill severity={defect.severity} />
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-mc-muted">
                    {formatDateTime(defect.detected_at)}
                  </td>
                  <td className="px-4 py-3 text-mc-text">
                    {formatUserLabel(defect.reporter)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </TablePanel>

      {isCreateOpen ? (
        <ReportDefectModal
          onClose={() => setIsCreateOpen(false)}
          onCreated={handleCreated}
        />
      ) : null}

      {selectedId !== null && role ? (
        <DefectDrawer
          defectId={selectedId}
          role={role}
          onClose={() => setSelectedId(null)}
          onUpdated={() => {
            reload();
            onDataChanged();
          }}
        />
      ) : null}
    </div>
  );
}
