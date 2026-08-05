import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Download, Plus, Search } from "lucide-react";

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
import { NetworkError } from "../../../shared/api/apiClient";
import { useAsyncData } from "../../../shared/hooks/useAsyncData";
import { useShellContext } from "../../../shared/layout/shellContext";
import { toRoleCode } from "../../../shared/layout/shellContext";
import { saveDownloadedFile } from "../../../shared/utils/downloadFile";
import { getFormError } from "../../../shared/utils/apiErrors";
import { humanizeEnum } from "../../../shared/utils/format";
import { formatDateTime } from "../../admin/utils/adminFormat";
import {
  exportReplacements,
  fetchReplacements,
} from "../api/repairsApi";
import { LogReplacementModal } from "../components/modals/LogReplacementModal";
import {
  COMPONENT_TYPE_OPTIONS,
  REPAIRS_PAGE_SIZE,
} from "../constants/repairsCatalog";
import {
  CAN_CREATE_REPAIRS,
  CAN_EXPORT_REPLACEMENTS,
} from "../rbac";
import {
  formatDroneLabel,
  formatUserLabel,
} from "../utils/repairsFormat";
import {
  describeTableError,
  REPAIRS_ENDPOINTS,
} from "../utils/repairsErrors";

interface ReplacementsTabProps {
  reloadSignal: number;
  onNetworkStateChange: (isOffline: boolean) => void;
  onDataChanged: () => void;
}

export function ReplacementsTab({
  reloadSignal,
  onNetworkStateChange,
  onDataChanged,
}: ReplacementsTabProps) {
  const { user } = useShellContext();
  const role = toRoleCode(user.role_code);

  const [componentType, setComponentType] = useState("");
  const [droneFilter, setDroneFilter] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [page, setPage] = useState(1);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(
    null,
  );

  const droneId = droneFilter.trim()
    ? Number(droneFilter)
    : undefined;

  const load = useCallback(
    (signal: AbortSignal) => {
      void reloadSignal;

      return fetchReplacements(
        {
          page,
          pageSize: REPAIRS_PAGE_SIZE,
          componentType: componentType || undefined,
          drone:
            droneId !== undefined && !Number.isNaN(droneId)
              ? droneId
              : undefined,
          startDate: startDate || undefined,
          endDate: endDate || undefined,
          ordering: "-replaced_at",
        },
        signal,
      );
    },
    [
      componentType,
      droneId,
      endDate,
      page,
      reloadSignal,
      startDate,
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
        componentType
          ? {
              key: "componentType",
              label: `Component: ${humanizeEnum(componentType)}`,
              onRemove: () =>
                changeFilter(() => setComponentType("")),
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
        startDate
          ? {
              key: "startDate",
              label: `From: ${startDate}`,
              onRemove: () =>
                changeFilter(() => setStartDate("")),
            }
          : null,
        endDate
          ? {
              key: "endDate",
              label: `To: ${endDate}`,
              onRemove: () =>
                changeFilter(() => setEndDate("")),
            }
          : null,
      ].filter(
        (filter): filter is NonNullable<typeof filter> =>
          filter !== null,
      ),
    [componentType, droneFilter, endDate, startDate],
  );

  const tableError = error
    ? describeTableError(
        error,
        "Component replacements",
        REPAIRS_ENDPOINTS.replacements,
      )
    : null;

  const canCreate =
    role !== null && CAN_CREATE_REPAIRS.has(role);
  const canExport =
    role !== null && CAN_EXPORT_REPLACEMENTS.has(role);

  async function handleExport() {
    setExportError(null);
    setIsExporting(true);

    try {
      const file = await exportReplacements({
        componentType: componentType || undefined,
        drone:
          droneId !== undefined && !Number.isNaN(droneId)
            ? droneId
            : undefined,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
      });
      saveDownloadedFile(
        file,
        "component-replacements.csv",
      );
    } catch (exportErr) {
      setExportError(
        getFormError(
          exportErr,
          "Could not export replacements.",
        ),
      );
    } finally {
      setIsExporting(false);
    }
  }

  function handleCreated() {
    reload();
    onDataChanged();
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-2">
        <TextField
          id="replacements-drone-filter"
          label="Drone ID"
          value={droneFilter}
          placeholder="Any"
          onChange={(value) =>
            changeFilter(() => setDroneFilter(value))
          }
          isMono
        />

        <FilterSelect
          id="replacements-type-filter"
          label="Component type"
          value={componentType}
          placeholder="Type"
          options={COMPONENT_TYPE_OPTIONS}
          onChange={(value) =>
            changeFilter(() => setComponentType(value))
          }
        />

        <TextField
          id="replacements-start-date"
          label="Start date"
          type="date"
          value={startDate}
          onChange={(value) =>
            changeFilter(() => setStartDate(value))
          }
        />

        <TextField
          id="replacements-end-date"
          label="End date"
          type="date"
          value={endDate}
          onChange={(value) =>
            changeFilter(() => setEndDate(value))
          }
        />

        <div className="ms-auto flex flex-wrap gap-2">
          {canExport ? (
            <Button
              variant="secondary"
              isLoading={isExporting}
              icon={<Download size={14} aria-hidden="true" />}
              onClick={() => void handleExport()}
            >
              Export CSV
            </Button>
          ) : null}

          {canCreate ? (
            <Button
              icon={<Plus size={14} aria-hidden="true" />}
              onClick={() => setIsCreateOpen(true)}
            >
              Log Replacement
            </Button>
          ) : null}
        </div>
      </div>

      {exportError ? (
        <p className="text-sm text-mc-error" role="alert">
          {exportError}
        </p>
      ) : null}

      <ActiveFilterChips
        filters={activeFilters}
        onClearAll={() =>
          changeFilter(() => {
            setComponentType("");
            setDroneFilter("");
            setStartDate("");
            setEndDate("");
          })
        }
      />

      <TablePanel
        label="Component replacements"
        footer={
          <Pagination
            page={page}
            pageSize={REPAIRS_PAGE_SIZE}
            count={data?.count ?? 0}
            note={
              <span className="font-mono text-[10px] tracking-wider uppercase">
                {data?.count ?? 0} replacements
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
              <HeaderCell>Component</HeaderCell>
              <HeaderCell>New serial</HeaderCell>
              <HeaderCell>Replaced at</HeaderCell>
              <HeaderCell>Replaced by</HeaderCell>
              <HeaderCell>Order</HeaderCell>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <TableSkeleton columns={6} rows={6} />
            ) : tableError ? (
              <TableErrorState
                colSpan={6}
                error={tableError}
                onRetry={reload}
              />
            ) : !data?.results.length ? (
              <TableEmptyState
                colSpan={6}
                icon={Search}
                title="No replacements"
                hint="Log a component swap to begin tracking lifecycle history."
              />
            ) : (
              data.results.map((item) => (
                <tr
                  key={item.id}
                  className="border-b border-white/5"
                >
                  <td className="px-4 py-3">
                    {formatDroneLabel(item.drone)}
                  </td>
                  <td className="px-4 py-3">
                    <p className="font-medium text-mc-text">
                      {item.component_name ??
                        humanizeEnum(item.component_type)}
                    </p>
                    <p className="font-mono text-[10px] text-mc-muted">
                      {humanizeEnum(item.component_type)}
                    </p>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-mc-accent">
                    {item.new_serial_number}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-mc-muted">
                    {formatDateTime(item.replaced_at)}
                  </td>
                  <td className="px-4 py-3 text-mc-text">
                    {formatUserLabel(item.replaced_by)}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-mc-muted">
                    —
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </TablePanel>

      {isCreateOpen ? (
        <LogReplacementModal
          onClose={() => setIsCreateOpen(false)}
          onCreated={handleCreated}
        />
      ) : null}
    </div>
  );
}
