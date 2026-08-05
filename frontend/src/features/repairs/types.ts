/* Extends `shared/types/repairs.ts` with Repair Order and Component Replacement
 * shapes. Mirrors repairs/serializers.py — see task-216 context for API gaps. */

import type {
  DefectSeverity,
  DefectTransitionStatus,
  OrderStatus,
} from "../../shared/types/repairs";

export type { DefectTransitionStatus, OrderStatus };

export interface RepairOrderListItem {
  id: number;
  drone: number;
  defect_report: number | null;
  status: OrderStatus;
  assigned_to: number | null;
  created_by: number;
  created_at: string;
}

export interface RepairOrderDetail extends RepairOrderListItem {
  description: string;
  started_at: string | null;
  completed_at: string | null;
  notes: string;
  updated_at: string;
}

export interface RepairOrderCreatePayload {
  drone: number;
  defect_report?: number | null;
  description: string;
  assigned_to?: number | null;
}

export interface RepairOrderStatusUpdatePayload {
  status: OrderStatus;
  notes?: string;
}

export interface ComponentReplacementListItem {
  id: number;
  drone: number;
  component_type: string;
  component_name: string | null;
  new_serial_number: string;
  replaced_at: string;
  replaced_by: number;
  created_at: string;
}

export interface ComponentReplacementDetail
  extends ComponentReplacementListItem {
  old_serial_number: string;
  reason: string;
  updated_at: string;
}

export interface OrderReplacement {
  id: number;
  component_type: string;
  component_name: string | null;
  old_serial_number: string;
  new_serial_number: string;
  reason: string;
  replaced_at: string;
  replaced_by: number;
  created_at: string;
  updated_at: string;
}

export interface ComponentReplacementCreatePayload {
  drone: number;
  component_type: string;
  component_name?: string | null;
  old_serial_number: string;
  new_serial_number: string;
  reason: string;
  replaced_at: string;
}

export interface RepairEvent {
  id: number;
  from_status: DefectTransitionStatus;
  to_status: DefectTransitionStatus;
  action_taken: string;
  technician: number;
  created_at: string;
}

export interface DefectStatusUpdatePayload {
  status: DefectTransitionStatus;
  action_taken: string;
}

export interface DefectDetail {
  id: number;
  drone: number;
  defect_type: string;
  severity: DefectSeverity;
  description: string;
  detected_at: string;
  reporter: number | null;
  created_at: string;
  updated_at: string;
}

export interface DefectCreatePayload {
  drone: number;
  defect_type: string;
  severity: DefectSeverity;
  description: string;
  detected_at: string;
}
