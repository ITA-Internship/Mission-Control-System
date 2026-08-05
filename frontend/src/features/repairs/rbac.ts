import type { RoleCode } from "../../shared/types/accounts";
import type {
  DefectTransitionStatus,
  OrderStatus,
} from "../../shared/types/repairs";

export const CAN_VIEW_REPAIRS = new Set<RoleCode>([
  "ADMIN",
  "COMMANDER",
  "DISPATCHER",
  "OPERATOR",
  "TECHNICIAN",
  "VIEWER",
]);

export const CAN_CREATE_REPAIRS = new Set<RoleCode>([
  "ADMIN",
  "TECHNICIAN",
]);

export const CAN_MANAGE_REPAIRS = new Set<RoleCode>([
  "ADMIN",
  "TECHNICIAN",
]);

export const CAN_VERIFY_DEFECTS = new Set<RoleCode>([
  "ADMIN",
  "COMMANDER",
]);

export const CAN_EXPORT_REPLACEMENTS = new Set<RoleCode>([
  "ADMIN",
  "COMMANDER",
  "TECHNICIAN",
]);

const DEFECT_NEXT: Record<
  DefectTransitionStatus,
  DefectTransitionStatus | null
> = {
  REPORTED: "IN_PROGRESS",
  IN_PROGRESS: "FIXED",
  FIXED: "VERIFIED",
  VERIFIED: null,
};

const ORDER_NEXT: Partial<
  Record<OrderStatus, OrderStatus[]>
> = {
  PENDING: ["IN_PROGRESS", "CANCELLED"],
  IN_PROGRESS: ["COMPLETED", "CANCELLED"],
};

export function nextDefectTransition(
  current: DefectTransitionStatus,
  role: RoleCode,
): DefectTransitionStatus | null {
  const next = DEFECT_NEXT[current];
  if (!next) return null;

  if (next === "VERIFIED") {
    return CAN_VERIFY_DEFECTS.has(role) ? next : null;
  }

  return CAN_MANAGE_REPAIRS.has(role) ? next : null;
}

export function allowedOrderTransitions(
  current: OrderStatus,
  role: RoleCode,
): OrderStatus[] {
  if (!CAN_MANAGE_REPAIRS.has(role)) {
    return [];
  }
  return ORDER_NEXT[current] ?? [];
}
