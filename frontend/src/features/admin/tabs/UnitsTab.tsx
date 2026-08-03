import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  Building2,
  Pencil,
  Plus,
} from "lucide-react";

import { ActionBanner } from "../components/ActionBanner";
import { Button } from "../components/Button";
import { SearchInput } from "../components/SearchInput";
import { StatusPill } from "../components/StatusPill";
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
import { UnitFormModal } from "../components/modals/UnitFormModal";
import {
  ADMIN_ENDPOINTS,
  listUnits,
  updateUnit,
} from "../api/adminApi";
import { CATALOG_PAGE_SIZE } from "../constants/adminCatalog";
import { NetworkError } from "../../../shared/api/apiClient";
import { useAsyncData } from "../../../shared/hooks/useAsyncData";
import { useDebouncedValue } from "../../../shared/hooks/useDebouncedValue";
import { getFormError } from "../../../shared/utils/apiErrors";
import { describeTableError } from "../utils/adminErrors";
import {
  formatCount,
  formatText,
} from "../utils/adminFormat";
import {
  sortRows,
  toggleSort,
} from "../utils/adminSorting";

import type { BannerMessage } from "../components/ActionBanner";
import type {
  MilitaryUnit,
  SortState,
} from "../types/admin";

type UnitColumn =
  | "name"
  | "code"
  | "drones"
  | "users";

const COLUMN_COUNT = 7;

interface UnitsTabProps {
  reloadSignal: number;
  onNetworkStateChange: (
    isOffline: boolean,
  ) => void;
  onUnitsChanged: () => void;
}

function selectSortValue(
  unit: MilitaryUnit,
  column: UnitColumn,
): string | number | null {
  switch (column) {
    case "name":
      return unit.name;
    case "code":
      return unit.code;
    case "drones":
      return unit.drone_count;
    case "users":
      return unit.user_count;
  }
}

export function UnitsTab({
  reloadSignal,
  onNetworkStateChange,
  onUnitsChanged,
}: UnitsTabProps) {
  const [searchInput, setSearchInput] =
    useState("");

  const search = useDebouncedValue(
    searchInput,
    350,
  );

  const [sort, setSort] = useState<
    SortState<UnitColumn>
  >({
    column: "name",
    direction: "asc",
  });

  const [banner, setBanner] =
    useState<BannerMessage | null>(null);

  const [isCreateOpen, setIsCreateOpen] =
    useState(false);

  const [editTarget, setEditTarget] =
    useState<MilitaryUnit | null>(null);

  const [pendingUnitId, setPendingUnitId] =
    useState<number | null>(null);

  const load = useCallback(
    (signal: AbortSignal) => {
      // Dependency only — see UsersTab.
      void reloadSignal;

      return listUnits(
        {
          page_size: CATALOG_PAGE_SIZE,
          search: search.trim() || undefined,
        },
        signal,
      );
    },
    [reloadSignal, search],
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

  const rows = useMemo(
    () =>
      sortRows(
        data?.results ?? [],
        (unit) =>
          selectSortValue(unit, sort.column),
        sort.direction,
      ),
    [data, sort],
  );

  async function handleToggleActive(
    unit: MilitaryUnit,
  ) {
    setPendingUnitId(unit.id);
    setBanner(null);

    try {
      await updateUnit(unit.id, {
        is_active: !unit.is_active,
      });

      setBanner({
        tone: "success",
        text: `${unit.name} was ${unit.is_active ? "deactivated" : "activated"}.`,
      });

      reload();
      onUnitsChanged();
    } catch (caughtError) {
      setBanner({
        tone: "error",
        text: getFormError(
          caughtError,
          "The unit status could not be updated.",
        ),
      });
    } finally {
      setPendingUnitId(null);
    }
  }

  const tableError = error
    ? describeTableError(
        error,
        "Military units",
        `GET ${ADMIN_ENDPOINTS.units}`,
      )
    : null;

  function handleSaved(unitName: string) {
    setBanner({
      tone: "success",
      text: `${unitName} was saved.`,
    });

    reload();
    onUnitsChanged();
  }

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
          id="units-search"
          label="Search units by name or code"
          value={searchInput}
          placeholder="Search unit name or code…"
          onChange={setSearchInput}
        />

        <div className="ms-auto">
          <Button
            icon={
              <Plus
                size={14}
                aria-hidden="true"
              />
            }
            onClick={() =>
              setIsCreateOpen(true)
            }
          >
            Add Unit
          </Button>
        </div>
      </div>

      <TablePanel label="Military units">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/7 bg-mc-panel">
              <SortableHeaderCell
                label="Unit name"
                column="name"
                sort={sort}
                onSort={(column) =>
                  setSort(
                    toggleSort(sort, column),
                  )
                }
              />

              <SortableHeaderCell
                label="Code"
                column="code"
                sort={sort}
                onSort={(column) =>
                  setSort(
                    toggleSort(sort, column),
                  )
                }
              />

              <HeaderCell>
                Description
              </HeaderCell>

              <SortableHeaderCell
                label="Drones"
                column="drones"
                sort={sort}
                align="right"
                onSort={(column) =>
                  setSort(
                    toggleSort(sort, column),
                  )
                }
              />

              <SortableHeaderCell
                label="Users"
                column="users"
                sort={sort}
                align="right"
                onSort={(column) =>
                  setSort(
                    toggleSort(sort, column),
                  )
                }
              />

              <HeaderCell>Status</HeaderCell>

              <HeaderCell
                align="right"
                srOnly
              >
                Row actions
              </HeaderCell>
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
                icon={Building2}
                title="No units found"
                hint="Add a unit or adjust your search."
              />
            ) : (
              rows.map((unit) => (
                <tr
                  key={unit.id}
                  className="border-b border-white/5 transition-colors last:border-b-0 hover:bg-white/3"
                >
                  <td className="px-4 py-3 font-semibold whitespace-nowrap text-mc-text">
                    {unit.name}
                  </td>

                  <td className="px-4 py-3">
                    <span className="rounded bg-white/6 px-2 py-0.5 font-mono text-xs whitespace-nowrap text-mc-accent">
                      {unit.code}
                    </span>
                  </td>

                  <td className="max-w-xs truncate px-4 py-3 text-mc-muted">
                    {formatText(
                      unit.description,
                    )}
                  </td>

                  <td
                    className={[
                      "px-4 py-3 text-right font-mono text-xs",
                      unit.drone_count
                        ? "text-mc-text"
                        : "text-mc-muted",
                    ].join(" ")}
                  >
                    {formatCount(
                      unit.drone_count,
                    )}
                  </td>

                  <td
                    className={[
                      "px-4 py-3 text-right font-mono text-xs",
                      unit.user_count
                        ? "text-mc-text"
                        : "text-mc-muted",
                    ].join(" ")}
                  >
                    {formatCount(
                      unit.user_count,
                    )}
                  </td>

                  <td className="px-4 py-3">
                    <StatusPill
                      isActive={
                        unit.is_active
                      }
                    />
                  </td>

                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        className="h-8 px-2"
                        icon={
                          <Pencil
                            size={13}
                            aria-hidden="true"
                          />
                        }
                        onClick={() =>
                          setEditTarget(unit)
                        }
                      >
                        <span className="sr-only">
                          {`Edit ${unit.name}`}
                        </span>
                      </Button>

                      <Button
                        variant="secondary"
                        className={[
                          "h-8 px-3 text-xs",
                          unit.is_active
                            ? "border-mc-error/30 text-mc-error hover:text-mc-error"
                            : "border-mc-success/30 text-mc-success hover:text-mc-success",
                        ].join(" ")}
                        isLoading={
                          pendingUnitId ===
                          unit.id
                        }
                        onClick={() =>
                          void handleToggleActive(
                            unit,
                          )
                        }
                      >
                        {unit.is_active
                          ? "Deactivate"
                          : "Activate"}
                      </Button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </TablePanel>

      {isCreateOpen ? (
        <UnitFormModal
          onClose={() =>
            setIsCreateOpen(false)
          }
          onSaved={handleSaved}
        />
      ) : null}

      {editTarget ? (
        <UnitFormModal
          unit={editTarget}
          onClose={() => setEditTarget(null)}
          onSaved={handleSaved}
        />
      ) : null}
    </div>
  );
}
