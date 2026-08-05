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
import { OrderStatusPill } from "../../../shared/components/StatusPill";
import { NetworkError } from "../../../shared/api/apiClient";
import { useAsyncData } from "../../../shared/hooks/useAsyncData";
import { useShellContext } from "../../../shared/layout/shellContext";
import { toRoleCode } from "../../../shared/layout/shellContext";
import { humanizeEnum } from "../../../shared/utils/format";
import { formatDateTime } from "../../admin/utils/adminFormat";
import { fetchRepairOrders } from "../api/repairsApi";
import { OrderDrawer } from "../components/OrderDrawer";
import { NewRepairOrderModal } from "../components/modals/NewRepairOrderModal";
import {
  ORDER_STATUS_OPTIONS,
  REPAIRS_PAGE_SIZE,
} from "../constants/repairsCatalog";
import { CAN_CREATE_REPAIRS } from "../rbac";
import {
  formatDefectId,
  formatDroneLabel,
  formatOrderId,
  formatUserLabel,
} from "../utils/repairsFormat";
import {
  describeTableError,
  REPAIRS_ENDPOINTS,
} from "../utils/repairsErrors";

interface OrdersTabProps {
  reloadSignal: number;
  onNetworkStateChange: (isOffline: boolean) => void;
  onDataChanged: () => void;
}

export function OrdersTab({
  reloadSignal,
  onNetworkStateChange,
  onDataChanged,
}: OrdersTabProps) {
  const { user } = useShellContext();
  const role = toRoleCode(user.role_code);

  const [status, setStatus] = useState("");
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

      return fetchRepairOrders(
        {
          page,
          pageSize: REPAIRS_PAGE_SIZE,
          status: status || undefined,
          drone:
            droneId !== undefined && !Number.isNaN(droneId)
              ? droneId
              : undefined,
          ordering: "-created_at",
        },
        signal,
      );
    },
    [droneId, page, reloadSignal, status],
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
        status
          ? {
              key: "status",
              label: `Status: ${humanizeEnum(status)}`,
              onRemove: () =>
                changeFilter(() => setStatus("")),
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
    [droneFilter, status],
  );

  const tableError = error
    ? describeTableError(
        error,
        "Repair orders",
        REPAIRS_ENDPOINTS.orders,
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
          id="orders-drone-filter"
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
          id="orders-status-filter"
          label="Status"
          value={status}
          placeholder="Status"
          options={ORDER_STATUS_OPTIONS}
          onChange={(value) =>
            changeFilter(() => setStatus(value))
          }
        />

        {canCreate ? (
          <div className="ms-auto">
            <Button
              icon={<Plus size={14} aria-hidden="true" />}
              onClick={() => setIsCreateOpen(true)}
            >
              New Order
            </Button>
          </div>
        ) : null}
      </div>

      <ActiveFilterChips
        filters={activeFilters}
        onClearAll={() =>
          changeFilter(() => {
            setStatus("");
            setDroneFilter("");
          })
        }
      />

      <TablePanel
        label="Repair orders"
        footer={
          <Pagination
            page={page}
            pageSize={REPAIRS_PAGE_SIZE}
            count={data?.count ?? 0}
            note={
              <span className="font-mono text-[10px] tracking-wider uppercase">
                {data?.count ?? 0} orders
              </span>
            }
            onChange={setPage}
          />
        }
      >
        <table className="min-w-full border-collapse text-sm">
          <thead className="border-b border-white/7 bg-mc-panel/60">
            <tr>
              <HeaderCell>Order ID</HeaderCell>
              <HeaderCell>Drone</HeaderCell>
              <HeaderCell>Linked defect</HeaderCell>
              <HeaderCell>Status</HeaderCell>
              <HeaderCell>Assigned to</HeaderCell>
              <HeaderCell>Created</HeaderCell>
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
                title="No repair orders"
                hint="Create an order to begin maintenance work."
              />
            ) : (
              data.results.map((order) => (
                <tr
                  key={order.id}
                  className="cursor-pointer border-b border-white/5 transition-colors hover:bg-white/3"
                  onClick={() => setSelectedId(order.id)}
                >
                  <td className="px-4 py-3 font-mono text-sm font-semibold text-mc-accent">
                    {formatOrderId(order.id)}
                  </td>
                  <td className="px-4 py-3">
                    {formatDroneLabel(order.drone)}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-mc-muted">
                    {order.defect_report
                      ? formatDefectId(order.defect_report)
                      : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <OrderStatusPill status={order.status} />
                  </td>
                  <td className="px-4 py-3 text-mc-text">
                    {formatUserLabel(order.assigned_to)}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-mc-muted">
                    {formatDateTime(order.created_at)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </TablePanel>

      {isCreateOpen ? (
        <NewRepairOrderModal
          onClose={() => setIsCreateOpen(false)}
          onCreated={handleCreated}
        />
      ) : null}

      {selectedId !== null && role ? (
        <OrderDrawer
          orderId={selectedId}
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
