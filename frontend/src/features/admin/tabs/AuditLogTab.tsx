import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  Download,
  ScrollText,
  Shield,
} from "lucide-react";

import { ActionBanner } from "../components/ActionBanner";
import { ActiveFilterChips } from "../components/ActiveFilterChips";
import { AuditActionPill } from "../components/AuditActionPill";
import { Button } from "../components/Button";
import { FilterSelect } from "../components/FilterSelect";
import { Pagination } from "../components/Pagination";
import { ResultPill } from "../components/ResultPill";
import { SearchInput } from "../components/SearchInput";
import { TablePanel } from "../components/TablePanel";
import {
  HeaderCell,
  SortableHeaderCell,
} from "../components/TableHeaderCell";
import {
  TableEmptyState,
  TableErrorState,
  TableSkeleton,
} from "../components/TableStates";
import {
  ADMIN_ENDPOINTS,
  exportAuditLog,
  listAuditLog,
} from "../api/adminApi";
import {
  AUDIT_ACTION_TYPES,
  AUDIT_PAGE_SIZE,
  AUDIT_RESULTS,
} from "../constants/adminCatalog";
import { NetworkError } from "../../../shared/api/apiClient";
import { useAsyncData } from "../../../shared/hooks/useAsyncData";
import { useDebouncedValue } from "../../../shared/hooks/useDebouncedValue";
import { saveDownloadedFile } from "../../../shared/utils/downloadFile";
import { getFormError } from "../../../shared/utils/apiErrors";
import { describeTableError } from "../utils/adminErrors";
import {
  formatText,
  formatTimestamp,
} from "../utils/adminFormat";
import {
  sortRows,
  toggleSort,
} from "../utils/adminSorting";

import type { BannerMessage } from "../components/ActionBanner";
import type {
  AuditLogEntry,
  SortState,
} from "../types/admin";

type AuditColumn =
  | "actor"
  | "target"
  | "created_at";

const COLUMN_COUNT = 7;

const ACTION_OPTIONS =
  AUDIT_ACTION_TYPES.map((actionType) => ({
    value: actionType,
    label: actionType,
  }));

interface AuditLogTabProps {
  reloadSignal: number;
  onNetworkStateChange: (
    isOffline: boolean,
  ) => void;
}

function selectSortValue(
  entry: AuditLogEntry,
  column: AuditColumn,
): string | null {
  switch (column) {
    case "actor":
      return entry.actor_username;
    case "target":
      return entry.target_user_username;
    case "created_at":
      return entry.created_at;
  }
}

export function AuditLogTab({
  reloadSignal,
  onNetworkStateChange,
}: AuditLogTabProps) {
  const [searchInput, setSearchInput] =
    useState("");

  const search = useDebouncedValue(
    searchInput,
    250,
  );

  const [actionType, setActionType] =
    useState("");

  const [result, setResult] = useState("");
  const [startDate, setStartDate] =
    useState("");
  const [endDate, setEndDate] = useState("");
  const [page, setPage] = useState(1);

  const [sort, setSort] = useState<
    SortState<AuditColumn>
  >({
    column: "created_at",
    direction: "desc",
  });

  const [banner, setBanner] =
    useState<BannerMessage | null>(null);

  const [isExporting, setIsExporting] =
    useState(false);

  const filterParams = useMemo(
    () => ({
      action_type: actionType || undefined,
      result: result || undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    }),
    [actionType, endDate, result, startDate],
  );

  const load = useCallback(
    (signal: AbortSignal) => {
      // Dependency only — see UsersTab.
      void reloadSignal;

      return listAuditLog(
        {
          ...filterParams,
          page,
          page_size: AUDIT_PAGE_SIZE,
        },
        signal,
      );
    },
    [filterParams, page, reloadSignal],
  );

  const {
    data,
    error,
    isLoading,
    reload,
  } = useAsyncData(load);

  useEffect(() => {
    onNetworkStateChange(
      error instanceof NetworkError,
    );
  }, [error, onNetworkStateChange]);

  const rows = useMemo(() => {
    const query = search.trim().toLowerCase();

    const filtered = (
      data?.results ?? []
    ).filter((entry) => {
      if (!query) {
        return true;
      }

      return [
        entry.actor_username,
        entry.target_user_username,
        entry.description,
      ].some((value) =>
        (value ?? "")
          .toLowerCase()
          .includes(query),
      );
    });

    return sortRows(
      filtered,
      (entry) =>
        selectSortValue(entry, sort.column),
      sort.direction,
    );
  }, [data, search, sort]);

  function changeFilter(apply: () => void) {
    apply();
    setPage(1);
  }

  const activeFilters = [
    actionType
      ? {
          key: "action",
          label: `Action: ${actionType}`,
          onRemove: () =>
            changeFilter(() =>
              setActionType(""),
            ),
        }
      : null,
    result
      ? {
          key: "result",
          label: `Result: ${
            result === "SUCCESS"
              ? "Success"
              : "Failure"
          }`,
          onRemove: () =>
            changeFilter(() => setResult("")),
        }
      : null,
    startDate
      ? {
          key: "start",
          label: `From: ${startDate}`,
          onRemove: () =>
            changeFilter(() =>
              setStartDate(""),
            ),
        }
      : null,
    endDate
      ? {
          key: "end",
          label: `To: ${endDate}`,
          onRemove: () =>
            changeFilter(() => setEndDate("")),
        }
      : null,
  ].filter(
    (filter): filter is NonNullable<
      typeof filter
    > => filter !== null,
  );

  async function handleExport() {
    setIsExporting(true);
    setBanner(null);

    try {
      const file = await exportAuditLog(
        filterParams,
      );

      saveDownloadedFile(
        file,
        "audit_logs.csv",
      );

      setBanner({
        tone: "success",
        text: "The filtered audit log was exported as CSV.",
      });
    } catch (caughtError) {
      setBanner({
        tone: "error",
        text: getFormError(
          caughtError,
          "The export could not be generated. Try again.",
        ),
      });
    } finally {
      setIsExporting(false);
    }
  }

  const tableError = error
    ? describeTableError(
        error,
        "Audit log",
        `GET ${ADMIN_ENDPOINTS.auditLog}`,
      )
    : null;

  const dateInputClasses = [
    "h-9 rounded-lg border border-white/9 bg-mc-panel px-3 text-sm",
    "transition-colors focus:border-mc-accent/60 focus:ring-2 focus:ring-mc-accent/15 focus:outline-none",
  ].join(" ");

  return (
    <div className="flex flex-col gap-4">
      {banner ? (
        <ActionBanner
          message={banner}
          onDismiss={() => setBanner(null)}
        />
      ) : null}

      <div className="flex flex-wrap items-center gap-2">
        <SearchInput
          id="audit-search"
          label="Search the loaded page by actor, target or description"
          value={searchInput}
          placeholder="Search actor or target…"
          onChange={setSearchInput}
        />

        <FilterSelect
          id="audit-action-filter"
          label="Filter by action type"
          value={actionType}
          placeholder="Action type"
          options={ACTION_OPTIONS}
          onChange={(value) =>
            changeFilter(() =>
              setActionType(value),
            )
          }
        />

        <FilterSelect
          id="audit-result-filter"
          label="Filter by result"
          value={result}
          placeholder="Result"
          options={AUDIT_RESULTS}
          onChange={(value) =>
            changeFilter(() =>
              setResult(value),
            )
          }
        />

        <div className="flex items-center gap-1.5">
          <label
            htmlFor="audit-start-date"
            className="sr-only"
          >
            From date
          </label>

          <input
            id="audit-start-date"
            type="date"
            value={startDate}
            max={endDate || undefined}
            onChange={(event) =>
              changeFilter(() =>
                setStartDate(
                  event.target.value,
                ),
              )
            }
            className={`${dateInputClasses} ${startDate ? "text-mc-text" : "text-mc-muted"}`}
          />

          <span
            className="text-xs text-mc-muted"
            aria-hidden="true"
          >
            –
          </span>

          <label
            htmlFor="audit-end-date"
            className="sr-only"
          >
            To date
          </label>

          <input
            id="audit-end-date"
            type="date"
            value={endDate}
            min={startDate || undefined}
            onChange={(event) =>
              changeFilter(() =>
                setEndDate(event.target.value),
              )
            }
            className={`${dateInputClasses} ${endDate ? "text-mc-text" : "text-mc-muted"}`}
          />
        </div>

        <div className="ms-auto">
          <Button
            variant="accentOutline"
            icon={
              <Download
                size={14}
                aria-hidden="true"
              />
            }
            isLoading={isExporting}
            onClick={() =>
              void handleExport()
            }
          >
            Export CSV
          </Button>
        </div>
      </div>

      <ActiveFilterChips
        filters={activeFilters}
        onClearAll={() =>
          changeFilter(() => {
            setActionType("");
            setResult("");
            setStartDate("");
            setEndDate("");
          })
        }
      />

      <p className="text-[11px] leading-4 text-mc-subtle">
        Action, result and date filters are
        applied by the API. Text search and
        column sorting apply to the page shown
        below.
      </p>

      <TablePanel
        label="Audit log"
        footer={
          <Pagination
            page={page}
            pageSize={AUDIT_PAGE_SIZE}
            count={data?.count ?? 0}
            note={
              <span className="flex items-center gap-1.5">
                <Shield
                  size={12}
                  aria-hidden="true"
                />
                Immutable — entries cannot be
                edited or deleted.
              </span>
            }
            onChange={setPage}
          />
        }
      >
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/7 bg-mc-panel">
              <HeaderCell>Action</HeaderCell>

              <SortableHeaderCell
                label="Actor"
                column="actor"
                sort={sort}
                onSort={(column) =>
                  setSort(
                    toggleSort(sort, column),
                  )
                }
              />

              <SortableHeaderCell
                label="Target"
                column="target"
                sort={sort}
                onSort={(column) =>
                  setSort(
                    toggleSort(sort, column),
                  )
                }
              />

              <HeaderCell>Result</HeaderCell>

              <HeaderCell>
                IP address
              </HeaderCell>

              <HeaderCell>
                User agent
              </HeaderCell>

              <SortableHeaderCell
                label="Timestamp"
                column="created_at"
                sort={sort}
                onSort={(column) =>
                  setSort(
                    toggleSort(sort, column),
                  )
                }
              />
            </tr>
          </thead>

          <tbody>
            {isLoading ? (
              <TableSkeleton
                columns={COLUMN_COUNT}
              />
            ) : tableError ? (
              <TableErrorState
                colSpan={COLUMN_COUNT}
                error={tableError}
                onRetry={reload}
              />
            ) : rows.length === 0 ? (
              <TableEmptyState
                colSpan={COLUMN_COUNT}
                icon={ScrollText}
                title="No audit entries"
                hint="Adjust the filters, date range or search query."
              />
            ) : (
              rows.map((entry) => (
                <tr
                  key={entry.id}
                  className="border-b border-white/5 transition-colors last:border-b-0 hover:bg-white/3"
                >
                  <td className="px-4 py-3">
                    <AuditActionPill
                      actionType={
                        entry.action_type
                      }
                    />
                  </td>

                  <td className="px-4 py-3 font-mono text-xs whitespace-nowrap text-mc-text">
                    {formatText(
                      entry.actor_username,
                    )}
                  </td>

                  <td className="px-4 py-3 font-mono text-xs whitespace-nowrap text-mc-muted">
                    {formatText(
                      entry.target_user_username,
                    )}
                  </td>

                  <td className="px-4 py-3">
                    <ResultPill
                      result={entry.result}
                    />
                  </td>

                  <td className="px-4 py-3 font-mono text-xs whitespace-nowrap text-mc-muted">
                    {formatText(
                      entry.ip_address,
                    )}
                  </td>

                  <td
                    className="max-w-42 truncate px-4 py-3 font-mono text-xs text-mc-muted"
                    title={
                      entry.user_agent ||
                      undefined
                    }
                  >
                    {formatText(
                      entry.user_agent,
                    )}
                  </td>

                  <td className="px-4 py-3 font-mono text-xs whitespace-nowrap text-mc-muted">
                    {formatTimestamp(
                      entry.created_at,
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </TablePanel>
    </div>
  );
}
