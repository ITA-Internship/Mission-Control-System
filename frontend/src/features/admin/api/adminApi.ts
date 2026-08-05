import {
  apiDownload,
  apiRequest,
  withQuery,
} from "../../../shared/api/apiClient";
import {
  parseAuditEntry,
  parsePage,
  parseRole,
  parseUnit,
  parseUser,
} from "./adminTransforms";
import { CATALOG_PAGE_SIZE } from "../constants/adminCatalog";

import type { DownloadedFile } from "../../../shared/api/apiClient";
import type { DetailResponse } from "../../../shared/types/api";
import type { ParsedUser } from "./adminTransforms";
import type {
  AuditLogEntry,
  AuditLogParams,
  CreateUserPayload,
  MilitaryUnit,
  Page,
  Role,
  UnitPayload,
  UserListParams,
} from "../types/admin";

/**
 * Endpoints per the Administration design brief (`docs/design/administration.md`).
 *
 * All endpoints below are implemented by the backend: the audit log (list + CSV
 * export), user creation, the user list, the user status and role endpoints, the
 * military-unit endpoints, and the role catalog. The parsers and per-resource
 * degradation states are kept defensive so a transient failure surfaces an
 * "endpoint unavailable" state instead of blanking out the console.
 */
export const ADMIN_ENDPOINTS = {
  users: "/api/accounts/users/",
  userStatus: (userId: number) =>
    `/api/accounts/users/${userId}/status/`,
  userRole: (userId: number) =>
    `/api/accounts/users/${userId}/role/`,
  roles: "/api/roles/",
  units: "/api/accounts/military-units/",
  unit: (unitId: number) =>
    `/api/accounts/military-units/${unitId}/`,
  auditLog: "/api/accounts/audit-log/",
  auditLogExport:
    "/api/accounts/audit-log/export/",
} as const;

export async function listUsers(
  params: UserListParams,
  signal?: AbortSignal,
): Promise<Page<ParsedUser>> {
  const payload = await apiRequest<unknown>(
    withQuery(ADMIN_ENDPOINTS.users, {
      page: params.page,
      page_size: params.page_size,
      search: params.search,
      role: params.role,
      unit: params.unit,
      is_active: params.is_active,
    }),
    { signal },
  );

  return parsePage(payload, parseUser);
}

export function createUser(
  payload: CreateUserPayload,
  signal?: AbortSignal,
): Promise<unknown> {
  return apiRequest<unknown>(
    ADMIN_ENDPOINTS.users,
    {
      method: "POST",
      json: payload,
      signal,
    },
  );
}

export function updateUserStatus(
  userId: number,
  isActive: boolean,
  reason: string,
  signal?: AbortSignal,
): Promise<DetailResponse> {
  return apiRequest<DetailResponse>(
    ADMIN_ENDPOINTS.userStatus(userId),
    {
      method: "PATCH",
      json: {
        is_active: isActive,
        reason,
      },
      signal,
    },
  );
}

export function updateUserRole(
  userId: number,
  roleId: number,
  signal?: AbortSignal,
): Promise<unknown> {
  return apiRequest<unknown>(
    ADMIN_ENDPOINTS.userRole(userId),
    {
      method: "PATCH",
      json: {
        role_id: roleId,
      },
      signal,
    },
  );
}

export async function listRoles(
  signal?: AbortSignal,
): Promise<Role[]> {
  const payload = await apiRequest<unknown>(
    withQuery(ADMIN_ENDPOINTS.roles, {
      page_size: CATALOG_PAGE_SIZE,
    }),
    { signal },
  );

  return parsePage(payload, parseRole).results;
}

export async function listUnits(
  params: {
    page?: number;
    page_size?: number;
    search?: string;
  } = {},
  signal?: AbortSignal,
): Promise<Page<MilitaryUnit>> {
  const payload = await apiRequest<unknown>(
    withQuery(ADMIN_ENDPOINTS.units, {
      page: params.page,
      page_size:
        params.page_size ?? CATALOG_PAGE_SIZE,
      search: params.search,
    }),
    { signal },
  );

  return parsePage(payload, parseUnit);
}

export function createUnit(
  payload: UnitPayload,
  signal?: AbortSignal,
): Promise<unknown> {
  return apiRequest<unknown>(
    ADMIN_ENDPOINTS.units,
    {
      method: "POST",
      json: payload,
      signal,
    },
  );
}

export function updateUnit(
  unitId: number,
  payload: Partial<
    UnitPayload & { is_active: boolean }
  >,
  signal?: AbortSignal,
): Promise<unknown> {
  return apiRequest<unknown>(
    ADMIN_ENDPOINTS.unit(unitId),
    {
      method: "PATCH",
      json: payload,
      signal,
    },
  );
}

export async function listAuditLog(
  params: AuditLogParams,
  signal?: AbortSignal,
): Promise<Page<AuditLogEntry>> {
  const payload = await apiRequest<unknown>(
    withQuery(ADMIN_ENDPOINTS.auditLog, {
      page: params.page,
      page_size: params.page_size,
      action_type: params.action_type,
      result: params.result,
      start_date: params.start_date,
      end_date: params.end_date,
    }),
    { signal },
  );

  return parsePage(payload, parseAuditEntry);
}

export function exportAuditLog(
  params: AuditLogParams,
  signal?: AbortSignal,
): Promise<DownloadedFile> {
  return apiDownload(
    withQuery(ADMIN_ENDPOINTS.auditLogExport, {
      action_type: params.action_type,
      result: params.result,
      start_date: params.start_date,
      end_date: params.end_date,
    }),
    { signal },
  );
}
