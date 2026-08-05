import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  Pencil,
  Plus,
  ToggleLeft,
  ToggleRight,
  TriangleAlert,
  Users,
} from "lucide-react";

import { ActionBanner } from "../components/ActionBanner";
import { ActiveFilterChips } from "../components/ActiveFilterChips";
import { Avatar } from "../../../shared/components/Avatar";
import { Button } from "../components/Button";
import { FilterSelect } from "../components/FilterSelect";
import { FormNote } from "../components/FormFields";
import { Pagination } from "../components/Pagination";
import { RoleBadge } from "../components/RoleBadge";
import { RowActionsMenu } from "../components/RowActionsMenu";
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
import { ChangeRoleModal } from "../components/modals/ChangeRoleModal";
import { CreateUserModal } from "../components/modals/CreateUserModal";
import { UserStatusModal } from "../components/modals/UserStatusModal";
import {
  ADMIN_ENDPOINTS,
  listUsers,
} from "../api/adminApi";
import { resolveUser } from "../api/adminTransforms";
import {
  USER_STATUS_OPTIONS,
  USERS_PAGE_SIZE,
} from "../constants/adminCatalog";
import { NetworkError } from "../../../shared/api/apiClient";
import { useAsyncData } from "../../../shared/hooks/useAsyncData";
import { useDebouncedValue } from "../../../shared/hooks/useDebouncedValue";
import { describeTableError } from "../utils/adminErrors";
import {
  formatDateTime,
  formatText,
} from "../utils/adminFormat";
import {
  sortRows,
  toggleSort,
} from "../utils/adminSorting";

import type { BannerMessage } from "../components/ActionBanner";
import type { AdminCatalog } from "../hooks/useAdminCatalog";
import type { AsyncData } from "../../../shared/hooks/useAsyncData";
import type {
  AdminUser,
  SortState,
} from "../types/admin";

type UserColumn =
  | "name"
  | "email"
  | "unit"
  | "created_by"
  | "last_login";

const COLUMN_COUNT = 8;

interface UsersTabProps {
  catalog: AsyncData<AdminCatalog>;
  reloadSignal: number;
  onNetworkStateChange: (
    isOffline: boolean,
  ) => void;
}

function selectSortValue(
  user: AdminUser,
  column: UserColumn,
): string | null {
  switch (column) {
    case "name":
      return user.full_name;
    case "email":
      return user.email;
    case "unit":
      return user.unit?.code ?? null;
    case "created_by":
      return user.created_by;
    case "last_login":
      return user.last_login;
  }
}

export function UsersTab({
  catalog,
  reloadSignal,
  onNetworkStateChange,
}: UsersTabProps) {
  const [searchInput, setSearchInput] =
    useState("");

  const search = useDebouncedValue(
    searchInput,
    350,
  );

  const [roleFilter, setRoleFilter] =
    useState("");

  const [unitFilter, setUnitFilter] =
    useState("");

  const [statusFilter, setStatusFilter] =
    useState("");

  const [page, setPage] = useState(1);

  const [sort, setSort] = useState<
    SortState<UserColumn>
  >({
    column: "name",
    direction: "asc",
  });

  const [banner, setBanner] =
    useState<BannerMessage | null>(null);

  const [isCreateOpen, setIsCreateOpen] =
    useState(false);

  const [roleTarget, setRoleTarget] =
    useState<AdminUser | null>(null);

  const [statusTarget, setStatusTarget] =
    useState<AdminUser | null>(null);

  const load = useCallback(
    (signal: AbortSignal) => {
      // `reloadSignal` is a dependency only: a bump from the top bar's
      // refresh control re-creates this loader and refetches the page.
      void reloadSignal;

      return listUsers(
        {
          page,
          page_size: USERS_PAGE_SIZE,
          search: search.trim() || undefined,
          role: roleFilter
            ? Number(roleFilter)
            : null,
          unit: unitFilter
            ? Number(unitFilter)
            : null,
          is_active: statusFilter
            ? statusFilter === "true"
            : null,
        },
        signal,
      );
    },
    [
      page,
      reloadSignal,
      roleFilter,
      search,
      statusFilter,
      unitFilter,
    ],
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

  const roles = useMemo(
    () => catalog.data?.roles ?? [],
    [catalog.data],
  );

  const units = useMemo(
    () => catalog.data?.units ?? [],
    [catalog.data],
  );

  const rows = useMemo(() => {
    const resolved = (
      data?.results ?? []
    ).map((user) =>
      resolveUser(user, roles, units),
    );

    return sortRows(
      resolved,
      (user) =>
        selectSortValue(user, sort.column),
      sort.direction,
    );
  }, [data, roles, sort, units]);

  function changeFilter(
    apply: () => void,
  ) {
    apply();
    setPage(1);
  }

  const activeFilters = [
    roleFilter
      ? {
          key: "role",
          label: `Role: ${
            roles.find(
              (role) =>
                String(role.id) ===
                roleFilter,
            )?.name ?? roleFilter
          }`,
          onRemove: () =>
            changeFilter(() =>
              setRoleFilter(""),
            ),
        }
      : null,
    unitFilter
      ? {
          key: "unit",
          label: `Unit: ${
            units.find(
              (unit) =>
                String(unit.id) ===
                unitFilter,
            )?.code ?? unitFilter
          }`,
          onRemove: () =>
            changeFilter(() =>
              setUnitFilter(""),
            ),
        }
      : null,
    statusFilter
      ? {
          key: "status",
          label: `Status: ${
            statusFilter === "true"
              ? "Active"
              : "Inactive"
          }`,
          onRemove: () =>
            changeFilter(() =>
              setStatusFilter(""),
            ),
        }
      : null,
  ].filter(
    (filter): filter is NonNullable<
      typeof filter
    > => filter !== null,
  );

  const tableError = error
    ? describeTableError(
        error,
        "Users",
        `GET ${ADMIN_ENDPOINTS.users}`,
      )
    : null;

  const degradedCatalogs = [
    catalog.data?.rolesError
      ? "roles"
      : null,
    catalog.data?.unitsError
      ? "military units"
      : null,
  ].filter(Boolean);

  return (
    <div className="flex flex-col gap-4">
      {banner ? (
        <ActionBanner
          message={banner}
          onDismiss={() => setBanner(null)}
        />
      ) : null}

      {degradedCatalogs.length > 0 ? (
        <FormNote
          tone="muted"
          icon={<TriangleAlert size={13} />}
        >
          {`The ${degradedCatalogs.join(" and ")} catalog could not be loaded, so the matching filters and selects are disabled.`}
        </FormNote>
      ) : null}

      <div className="flex flex-wrap items-center gap-2">
        <SearchInput
          id="users-search"
          label="Search users by name or email"
          value={searchInput}
          placeholder="Search name or email…"
          onChange={(value) =>
            changeFilter(() =>
              setSearchInput(value),
            )
          }
        />

        <FilterSelect
          id="users-role-filter"
          label="Filter by role"
          value={roleFilter}
          placeholder="Role"
          options={roles.map((role) => ({
            value: String(role.id),
            label: role.name,
          }))}
          disabled={roles.length === 0}
          onChange={(value) =>
            changeFilter(() =>
              setRoleFilter(value),
            )
          }
        />

        <FilterSelect
          id="users-unit-filter"
          label="Filter by unit"
          value={unitFilter}
          placeholder="Unit"
          options={units.map((unit) => ({
            value: String(unit.id),
            label: unit.code || unit.name,
          }))}
          disabled={units.length === 0}
          onChange={(value) =>
            changeFilter(() =>
              setUnitFilter(value),
            )
          }
        />

        <FilterSelect
          id="users-status-filter"
          label="Filter by status"
          value={statusFilter}
          placeholder="Status"
          options={USER_STATUS_OPTIONS}
          onChange={(value) =>
            changeFilter(() =>
              setStatusFilter(value),
            )
          }
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
            Create User
          </Button>
        </div>
      </div>

      <ActiveFilterChips
        filters={activeFilters}
        onClearAll={() =>
          changeFilter(() => {
            setRoleFilter("");
            setUnitFilter("");
            setStatusFilter("");
          })
        }
      />

      <p className="text-[11px] leading-4 text-mc-subtle">
        Search and filters are applied by the
        API. Column sorting applies to the page
        shown below.
      </p>

      <TablePanel
        label="Users"
        footer={
          <Pagination
            page={page}
            pageSize={USERS_PAGE_SIZE}
            count={data?.count ?? 0}
            onChange={setPage}
          />
        }
      >
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/7 bg-mc-panel">
              <SortableHeaderCell
                label="Name"
                column="name"
                sort={sort}
                onSort={(column) =>
                  setSort(
                    toggleSort(sort, column),
                  )
                }
              />

              <SortableHeaderCell
                label="Email"
                column="email"
                sort={sort}
                onSort={(column) =>
                  setSort(
                    toggleSort(sort, column),
                  )
                }
              />

              <HeaderCell>Role</HeaderCell>

              <SortableHeaderCell
                label="Unit"
                column="unit"
                sort={sort}
                onSort={(column) =>
                  setSort(
                    toggleSort(sort, column),
                  )
                }
              />

              <HeaderCell>Status</HeaderCell>

              <SortableHeaderCell
                label="Created by"
                column="created_by"
                sort={sort}
                onSort={(column) =>
                  setSort(
                    toggleSort(sort, column),
                  )
                }
              />

              <SortableHeaderCell
                label="Last login"
                column="last_login"
                sort={sort}
                onSort={(column) =>
                  setSort(
                    toggleSort(sort, column),
                  )
                }
              />

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
                icon={Users}
                title="No users found"
                hint="Adjust the filters or search query."
              />
            ) : (
              rows.map((user) => (
                <tr
                  key={user.id}
                  className="border-b border-white/5 transition-colors last:border-b-0 hover:bg-white/3"
                >
                  <td className="px-4 py-3 font-medium whitespace-nowrap text-mc-text">
                    <span className="flex items-center gap-2.5">
                      <Avatar
                        name={user.full_name}
                      />

                      {user.full_name}
                    </span>
                  </td>

                  <td className="px-4 py-3 whitespace-nowrap text-mc-muted">
                    {formatText(user.email)}
                  </td>

                  <td className="px-4 py-3">
                    <RoleBadge
                      role={user.role}
                    />
                  </td>

                  <td className="px-4 py-3 font-mono text-xs whitespace-nowrap text-mc-muted">
                    {formatText(
                      user.unit?.code ??
                        user.unit?.name ??
                        null,
                    )}
                  </td>

                  <td className="px-4 py-3">
                    <StatusPill
                      isActive={
                        user.is_active
                      }
                    />
                  </td>

                  <td className="px-4 py-3 font-mono text-xs whitespace-nowrap text-mc-muted">
                    {formatText(
                      user.created_by,
                    )}
                  </td>

                  <td className="px-4 py-3 font-mono text-xs whitespace-nowrap text-mc-muted">
                    {formatDateTime(
                      user.last_login,
                    )}
                  </td>

                  <td className="px-4 py-3 text-right">
                    <RowActionsMenu
                      label={`Actions for ${user.full_name}`}
                      actions={[
                        {
                          key: "role",
                          label: "Change role",
                          icon: (
                            <Pencil
                              size={14}
                            />
                          ),
                          onSelect: () =>
                            setRoleTarget(
                              user,
                            ),
                        },
                        {
                          key: "status",
                          label: user.is_active
                            ? "Deactivate"
                            : "Activate",
                          icon: user.is_active ? (
                            <ToggleLeft
                              size={14}
                            />
                          ) : (
                            <ToggleRight
                              size={14}
                            />
                          ),
                          tone: user.is_active
                            ? "danger"
                            : "success",
                          onSelect: () =>
                            setStatusTarget(
                              user,
                            ),
                        },
                      ]}
                    />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </TablePanel>

      {isCreateOpen ? (
        <CreateUserModal
          roles={roles}
          units={units}
          onClose={() =>
            setIsCreateOpen(false)
          }
          onCreated={(username) => {
            setBanner({
              tone: "success",
              text: `User ${username} created — an activation email has been sent.`,
            });

            reload();
          }}
        />
      ) : null}

      {roleTarget ? (
        <ChangeRoleModal
          user={roleTarget}
          roles={roles}
          onClose={() => setRoleTarget(null)}
          onChanged={(username) => {
            setBanner({
              tone: "success",
              text: `Role updated for ${username}. The change was written to the audit log.`,
            });

            reload();
          }}
        />
      ) : null}

      {statusTarget ? (
        <UserStatusModal
          user={statusTarget}
          onClose={() =>
            setStatusTarget(null)
          }
          onUpdated={(
            username,
            isActive,
          ) => {
            setBanner({
              tone: "success",
              text: `${username} was ${isActive ? "activated" : "deactivated"}.`,
            });

            reload();
          }}
        />
      ) : null}
    </div>
  );
}
