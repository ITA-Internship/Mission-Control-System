import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import { Button } from "../../admin/components/Button";
import { TextAreaField } from "../../admin/components/FormFields";
import {
  DefectStatusPill,
  SeverityPill,
} from "../../../shared/components/StatusPill";
import {
  ErrorState,
  SkeletonRows,
} from "../../../shared/components/states";
import {
  fetchDefect,
  fetchDefectCurrentStatus,
  fetchDefectHistory,
  updateDefectStatus,
} from "../api/repairsApi";
import { nextDefectTransition } from "../rbac";
import { SideDrawer } from "./SideDrawer";
import {
  formatDefectId,
  formatDroneLabel,
  formatUserLabel,
} from "../utils/repairsFormat";
import { formatDateTime } from "../../admin/utils/adminFormat";
import { humanizeEnum } from "../../../shared/utils/format";
import { isAbortError } from "../../../shared/api/apiClient";
import { getFormError } from "../../../shared/utils/apiErrors";
import { useAbortableRequest } from "../../../shared/hooks/useAbortableRequest";

import type { RoleCode } from "../../../shared/types/accounts";
import type { DefectTransitionStatus } from "../../../shared/types/repairs";
import type { DefectDetail, RepairEvent } from "../types";

interface DefectDrawerProps {
  defectId: number;
  role: RoleCode;
  onClose: () => void;
  onUpdated: () => void;
}

export function DefectDrawer({
  defectId,
  role,
  onClose,
  onUpdated,
}: DefectDrawerProps) {
  const { run } = useAbortableRequest();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [detail, setDetail] = useState<DefectDetail | null>(null);
  const [status, setStatus] =
    useState<DefectTransitionStatus | null>(null);
  const [history, setHistory] = useState<RepairEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionTaken, setActionTaken] = useState("");
  const [transitionError, setTransitionError] =
    useState<string | null>(null);

  const load = useCallback(
    async (signal: AbortSignal) => {
      setIsLoading(true);
      setError(null);

      try {
        const [defect, currentStatus, historyPage] =
          await Promise.all([
            fetchDefect(defectId, signal),
            fetchDefectCurrentStatus(defectId, signal),
            fetchDefectHistory(
              defectId,
              { pageSize: 20 },
              signal,
            ),
          ]);

        setDetail(defect);
        setStatus(currentStatus as DefectTransitionStatus);
        setHistory(historyPage.results);
      } catch (loadError) {
        if (isAbortError(loadError)) return;
        setError(
          getFormError(
            loadError,
            "Could not load defect details.",
          ),
        );
      } finally {
        if (!signal.aborted) {
          setIsLoading(false);
        }
      }
    },
    [defectId],
  );

  useEffect(() => {
    void run((signal) => load(signal));
  }, [load, run]);

  const nextStatus =
    status !== null
      ? nextDefectTransition(status, role)
      : null;

  async function handleTransition(event: FormEvent) {
    event.preventDefault();
    if (!nextStatus) return;

    setTransitionError(null);

    if (actionTaken.trim().length < 3) {
      setTransitionError(
        "Describe the action taken (at least 3 characters).",
      );
      return;
    }

    try {
      setIsSubmitting(true);
      await run(() =>
        updateDefectStatus(defectId, {
          status: nextStatus,
          action_taken: actionTaken.trim(),
        }),
      );
      setActionTaken("");
      onUpdated();
      const controller = new AbortController();
      await load(controller.signal);
    } catch (transitionErr) {
      if (isAbortError(transitionErr)) return;
      setTransitionError(
        getFormError(
          transitionErr,
          "Could not update defect status.",
        ),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <SideDrawer
      title={detail ? formatDefectId(detail.id) : "Defect"}
      subtitle={
        detail
          ? `${formatDroneLabel(detail.drone)} · ${humanizeEnum(detail.defect_type)}`
          : undefined
      }
      onClose={onClose}
    >
      {isLoading ? (
        <SkeletonRows rows={6} />
      ) : error ? (
        <ErrorState description={error} />
      ) : detail && status ? (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center gap-2">
            <SeverityPill severity={detail.severity} />
            <DefectStatusPill status={status} />
          </div>

          <dl className="grid grid-cols-1 gap-3 text-sm">
            <div>
              <dt className="text-[11px] font-semibold tracking-widest text-mc-muted uppercase">
                Detected
              </dt>
              <dd className="mt-0.5 text-mc-text">
                {formatDateTime(detail.detected_at)}
              </dd>
            </div>
            <div>
              <dt className="text-[11px] font-semibold tracking-widest text-mc-muted uppercase">
                Reporter
              </dt>
              <dd className="mt-0.5 text-mc-text">
                {formatUserLabel(detail.reporter)}
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
          </dl>

          {nextStatus ? (
            <form
              className="space-y-3 rounded-lg border border-white/8 bg-mc-panel/40 p-4"
              onSubmit={handleTransition}
            >
              <p className="text-xs font-medium text-mc-muted">
                Advance to{" "}
                <span className="text-mc-text">
                  {humanizeEnum(nextStatus)}
                </span>
              </p>

              <TextAreaField
                id="defect-action-taken"
                label="Action taken"
                value={actionTaken}
                onChange={(value) =>
                  setActionTaken(value)
                }
                rows={3}
                placeholder="Work performed, parts replaced, test results..."
              />

              {transitionError ? (
                <p className="text-sm text-mc-error" role="alert">
                  {transitionError}
                </p>
              ) : null}

              <Button type="submit" isLoading={isSubmitting}>
                Update status
              </Button>
            </form>
          ) : null}

          <section>
            <h3 className="mb-2 text-[11px] font-semibold tracking-widest text-mc-muted uppercase">
              History
            </h3>
            {history.length === 0 ? (
              <p className="text-sm text-mc-muted">
                No status transitions recorded yet.
              </p>
            ) : (
              <ul className="space-y-3">
                {history.map((event) => (
                  <li
                    key={event.id}
                    className="rounded-lg border border-white/6 px-3 py-2"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <DefectStatusPill
                        status={event.from_status}
                      />
                      <span className="text-mc-muted">→</span>
                      <DefectStatusPill
                        status={event.to_status}
                      />
                      <span className="ml-auto font-mono text-[10px] text-mc-muted">
                        {formatDateTime(event.created_at)}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-mc-text">
                      {event.action_taken}
                    </p>
                    <p className="mt-0.5 font-mono text-[10px] text-mc-muted">
                      Tech {formatUserLabel(event.technician)}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      ) : null}
    </SideDrawer>
  );
}
