import { useCallback, useEffect, useState } from "react";
import { Plus } from "lucide-react";

import { Button } from "../../admin/components/Button";
import { TextAreaField } from "../../admin/components/FormFields";
import { OrderStatusPill } from "../../../shared/components/StatusPill";
import {
  ErrorState,
  SkeletonRows,
} from "../../../shared/components/states";
import {
  fetchRepairOrder,
  updateRepairOrderStatus,
} from "../api/repairsApi";
import { allowedOrderTransitions } from "../rbac";
import { AddOrderReplacementModal } from "./modals/AddOrderReplacementModal";
import { SideDrawer } from "./SideDrawer";
import {
  formatDefectId,
  formatDroneLabel,
  formatOrderId,
  formatUserLabel,
} from "../utils/repairsFormat";
import { formatDateTime } from "../../admin/utils/adminFormat";
import { humanizeEnum } from "../../../shared/utils/format";
import { isAbortError } from "../../../shared/api/apiClient";
import { getFormError } from "../../../shared/utils/apiErrors";
import { useAbortableRequest } from "../../../shared/hooks/useAbortableRequest";

import type { RoleCode } from "../../../shared/types/accounts";
import type { OrderStatus } from "../../../shared/types/repairs";
import type {
  OrderReplacement,
  RepairOrderDetail,
} from "../types";

interface OrderDrawerProps {
  orderId: number;
  role: RoleCode;
  onClose: () => void;
  onUpdated: () => void;
}

export function OrderDrawer({
  orderId,
  role,
  onClose,
  onUpdated,
}: OrderDrawerProps) {
  const { run, isPending } = useAbortableRequest();

  const [detail, setDetail] =
    useState<RepairOrderDetail | null>(null);
  const [sessionReplacements, setSessionReplacements] =
    useState<OrderReplacement[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [transitionError, setTransitionError] =
    useState<string | null>(null);
  const [isReplacementOpen, setIsReplacementOpen] =
    useState(false);

  const load = useCallback(
    async (signal: AbortSignal) => {
      setIsLoading(true);
      setError(null);

      try {
        const order = await fetchRepairOrder(orderId, signal);
        setDetail(order);
        setNotes(order.notes ?? "");
      } catch (loadError) {
        if (isAbortError(loadError)) return;
        setError(
          getFormError(
            loadError,
            "Could not load repair order.",
          ),
        );
      } finally {
        if (!signal.aborted) {
          setIsLoading(false);
        }
      }
    },
    [orderId],
  );

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const transitions =
    detail !== null
      ? allowedOrderTransitions(detail.status, role)
      : [];

  const canAddReplacement =
    detail !== null &&
    (detail.status === "PENDING" ||
      detail.status === "IN_PROGRESS");

  async function handleTransition(nextStatus: OrderStatus) {
    setTransitionError(null);

    try {
      await run(() =>
        updateRepairOrderStatus(orderId, {
          status: nextStatus,
          notes: notes.trim() || undefined,
        }),
      );
      onUpdated();
      const controller = new AbortController();
      await load(controller.signal);
    } catch (transitionErr) {
      if (isAbortError(transitionErr)) return;
      setTransitionError(
        getFormError(
          transitionErr,
          "Could not update order status.",
        ),
      );
    }
  }

  return (
    <>
      <SideDrawer
        title={detail ? formatOrderId(detail.id) : "Repair order"}
        subtitle={
          detail ? formatDroneLabel(detail.drone) : undefined
        }
        onClose={onClose}
      >
        {isLoading ? (
          <SkeletonRows rows={6} />
        ) : error ? (
          <ErrorState description={error} />
        ) : detail ? (
          <div className="space-y-6">
            <OrderStatusPill status={detail.status} />

            <dl className="grid grid-cols-1 gap-3 text-sm">
              <div>
                <dt className="text-[11px] font-semibold tracking-widest text-mc-muted uppercase">
                  Linked defect
                </dt>
                <dd className="mt-0.5 font-mono text-mc-accent">
                  {detail.defect_report
                    ? formatDefectId(detail.defect_report)
                    : "—"}
                </dd>
              </div>
              <div>
                <dt className="text-[11px] font-semibold tracking-widest text-mc-muted uppercase">
                  Assigned to
                </dt>
                <dd className="mt-0.5 text-mc-text">
                  {formatUserLabel(detail.assigned_to)}
                </dd>
              </div>
              <div>
                <dt className="text-[11px] font-semibold tracking-widest text-mc-muted uppercase">
                  Description
                </dt>
                <dd className="mt-0.5 whitespace-pre-wrap text-mc-text">
                  {detail.description}
                </dd>
              </div>
              <div>
                <dt className="text-[11px] font-semibold tracking-widest text-mc-muted uppercase">
                  Created
                </dt>
                <dd className="mt-0.5 text-mc-text">
                  {formatDateTime(detail.created_at)}
                </dd>
              </div>
              <div>
                <dt className="text-[11px] font-semibold tracking-widest text-mc-muted uppercase">
                  Updated
                </dt>
                <dd className="mt-0.5 text-mc-text">
                  {formatDateTime(detail.updated_at)}
                </dd>
              </div>
            </dl>

            {transitions.length > 0 ? (
              <div className="space-y-3 rounded-lg border border-white/8 bg-mc-panel/40 p-4">
                <TextAreaField
                  id="order-notes"
                  label="Notes"
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  rows={2}
                  placeholder="Optional notes for this transition..."
                />

                {transitionError ? (
                  <p className="text-sm text-mc-error" role="alert">
                    {transitionError}
                  </p>
                ) : null}

                <div className="flex flex-wrap gap-2">
                  {transitions.map((nextStatus) => (
                    <Button
                      key={nextStatus}
                      variant={
                        nextStatus === "CANCELLED"
                          ? "danger"
                          : "secondary"
                      }
                      isLoading={isPending}
                      onClick={() =>
                        void handleTransition(nextStatus)
                      }
                    >
                      Mark {humanizeEnum(nextStatus)}
                    </Button>
                  ))}
                </div>
              </div>
            ) : null}

            {canAddReplacement ? (
              <div>
                <div className="mb-2 flex items-center justify-between gap-2">
                  <h3 className="text-[11px] font-semibold tracking-widest text-mc-muted uppercase">
                    Replacements (this session)
                  </h3>
                  <Button
                    variant="accentOutline"
                    icon={<Plus size={14} aria-hidden="true" />}
                    onClick={() => setIsReplacementOpen(true)}
                  >
                    Add replacement
                  </Button>
                </div>

                {sessionReplacements.length === 0 ? (
                  <p className="text-sm text-mc-muted">
                    No replacements logged in this session. Historical
                    replacements linked to this order are not available
                    via the list API yet.
                  </p>
                ) : (
                  <ul className="space-y-2">
                    {sessionReplacements.map((item) => (
                      <li
                        key={item.id}
                        className="rounded-lg border border-white/6 px-3 py-2 text-sm"
                      >
                        <p className="font-medium text-mc-text">
                          {humanizeEnum(item.component_type)}
                        </p>
                        <p className="font-mono text-[11px] text-mc-muted">
                          {item.old_serial_number} →{" "}
                          {item.new_serial_number}
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ) : null}
          </div>
        ) : null}
      </SideDrawer>

      {isReplacementOpen && detail ? (
        <AddOrderReplacementModal
          orderId={detail.id}
          droneId={detail.drone}
          onClose={() => setIsReplacementOpen(false)}
          onCreated={(replacement) => {
            setSessionReplacements((current) => [
              replacement,
              ...current,
            ]);
          }}
        />
      ) : null}
    </>
  );
}
