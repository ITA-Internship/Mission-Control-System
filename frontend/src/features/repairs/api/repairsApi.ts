import {
  apiDownload,
  apiRequest,
  withQuery,
} from "../../../shared/api/apiClient";
import type { Paginated } from "../../../shared/types/api";
import type { DefectListItem } from "../../../shared/types/repairs";
import type {
  ComponentReplacementCreatePayload,
  ComponentReplacementDetail,
  ComponentReplacementListItem,
  DefectCreatePayload,
  DefectDetail,
  DefectStatusUpdatePayload,
  OrderReplacement,
  RepairEvent,
  RepairOrderCreatePayload,
  RepairOrderDetail,
  RepairOrderListItem,
  RepairOrderStatusUpdatePayload,
} from "../types";

export const OPEN_DEFECT_STATUSES = "REPORTED,IN_PROGRESS";

export const ACTIVE_ORDER_STATUSES = "PENDING,IN_PROGRESS";

async function fetchCount(
  path: string,
  params: Record<string, string>,
  signal?: AbortSignal,
): Promise<number> {
  const query = new URLSearchParams({
    ...params,
    page_size: "1",
  }).toString();

  const data = await apiRequest<Paginated<unknown>>(
    `${path}?${query}`,
    { signal },
  );

  return data.count;
}

export function fetchOpenDefectsCount(
  params: Record<string, string> = {},
  signal?: AbortSignal,
): Promise<number> {
  return fetchCount(
    "/api/repairs/defects/",
    { status__in: OPEN_DEFECT_STATUSES, ...params },
    signal,
  );
}

export function fetchActiveOrdersCount(
  signal?: AbortSignal,
): Promise<number> {
  return fetchCount(
    "/api/repairs/orders/",
    { status__in: ACTIVE_ORDER_STATUSES },
    signal,
  );
}

export interface FetchDefectsParams {
  page?: number;
  pageSize?: number;
  drone?: number;
  severity?: string;
  defectType?: string;
  reporter?: number;
  status?: string;
  statusIn?: string[];
  ordering?: string;
}

export function fetchDefects(
  params: FetchDefectsParams = {},
  signal?: AbortSignal,
) {
  return apiRequest<Paginated<DefectListItem>>(
    withQuery("/api/repairs/defects/", {
      page: params.page,
      page_size: params.pageSize,
      drone: params.drone,
      severity: params.severity,
      defect_type: params.defectType,
      reporter: params.reporter,
      status: params.status,
      status__in: params.statusIn?.join(","),
      ordering: params.ordering,
    }),
    { signal },
  );
}

export function fetchDefect(
  id: number | string,
  signal?: AbortSignal,
) {
  return apiRequest<DefectDetail>(
    `/api/repairs/defects/${id}/`,
    { signal },
  );
}

export function createDefect(data: DefectCreatePayload) {
  return apiRequest<DefectDetail>("/api/repairs/defects/", {
    method: "POST",
    json: data,
  });
}

export function fetchDefectHistory(
  id: number | string,
  params: { page?: number; pageSize?: number } = {},
  signal?: AbortSignal,
) {
  return apiRequest<Paginated<RepairEvent>>(
    withQuery(`/api/repairs/defects/${id}/history/`, {
      page: params.page,
      page_size: params.pageSize,
    }),
    { signal },
  );
}

export async function fetchDefectCurrentStatus(
  id: number | string,
  signal?: AbortSignal,
): Promise<string> {
  const history = await fetchDefectHistory(
    id,
    { pageSize: 1, page: 1 },
    signal,
  );
  return history.results[0]?.to_status ?? "REPORTED";
}

export function updateDefectStatus(
  id: number | string,
  data: DefectStatusUpdatePayload,
) {
  return apiRequest<RepairEvent>(
    `/api/repairs/defects/${id}/update-status/`,
    { method: "POST", json: data },
  );
}

export interface FetchRepairOrdersParams {
  page?: number;
  pageSize?: number;
  drone?: number;
  status?: string;
  defectReport?: number;
  assignedTo?: number;
  createdAtGte?: string;
  createdAtLte?: string;
  ordering?: string;
}

export function fetchRepairOrders(
  params: FetchRepairOrdersParams = {},
  signal?: AbortSignal,
) {
  return apiRequest<Paginated<RepairOrderListItem>>(
    withQuery("/api/repairs/orders/", {
      page: params.page,
      page_size: params.pageSize,
      drone: params.drone,
      status: params.status,
      defect_report: params.defectReport,
      assigned_to: params.assignedTo,
      created_at__gte: params.createdAtGte,
      created_at__lte: params.createdAtLte,
      ordering: params.ordering,
    }),
    { signal },
  );
}

export function fetchRepairOrder(
  id: number | string,
  signal?: AbortSignal,
) {
  return apiRequest<RepairOrderDetail>(
    `/api/repairs/orders/${id}/`,
    { signal },
  );
}

export function createRepairOrder(data: RepairOrderCreatePayload) {
  return apiRequest<RepairOrderDetail>("/api/repairs/orders/", {
    method: "POST",
    json: data,
  });
}

export function updateRepairOrderStatus(
  id: number | string,
  data: RepairOrderStatusUpdatePayload,
) {
  return apiRequest<RepairOrderDetail>(
    `/api/repairs/orders/${id}/`,
    { method: "PATCH", json: data },
  );
}

export function addOrderReplacement(
  orderId: number | string,
  data: ComponentReplacementCreatePayload,
) {
  return apiRequest<OrderReplacement>(
    `/api/repairs/orders/${orderId}/replacements/`,
    { method: "POST", json: data },
  );
}

export interface FetchReplacementsParams {
  page?: number;
  pageSize?: number;
  drone?: number;
  componentType?: string;
  replacedBy?: number;
  startDate?: string;
  endDate?: string;
  ordering?: string;
}

function replacementsQuery(params: FetchReplacementsParams) {
  return {
    page: params.page,
    page_size: params.pageSize,
    drone: params.drone,
    component_type: params.componentType,
    replaced_by: params.replacedBy,
    start_date: params.startDate,
    end_date: params.endDate,
    ordering: params.ordering,
  };
}

export function fetchReplacements(
  params: FetchReplacementsParams = {},
  signal?: AbortSignal,
) {
  return apiRequest<Paginated<ComponentReplacementListItem>>(
    withQuery(
      "/api/repairs/replacements/",
      replacementsQuery(params),
    ),
    { signal },
  );
}

export function fetchReplacement(
  id: number | string,
  signal?: AbortSignal,
) {
  return apiRequest<ComponentReplacementDetail>(
    `/api/repairs/replacements/${id}/`,
    { signal },
  );
}

export function createReplacement(
  data: ComponentReplacementCreatePayload,
) {
  return apiRequest<ComponentReplacementDetail>(
    "/api/repairs/replacements/",
    { method: "POST", json: data },
  );
}

export async function exportReplacements(
  params: FetchReplacementsParams = {},
) {
  const file = await apiDownload(
    withQuery(
      "/api/repairs/replacements/export/",
      replacementsQuery(params),
    ),
  );
  return {
    blob: file.blob,
    filename: file.filename ?? "component-replacements.csv",
  };
}
