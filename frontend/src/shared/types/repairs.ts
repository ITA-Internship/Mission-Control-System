export type DefectSeverity =
  | "LOW"
  | "MEDIUM"
  | "HIGH"
  | "CRITICAL";

export type DefectTransitionStatus =
  | "REPORTED"
  | "IN_PROGRESS"
  | "FIXED"
  | "VERIFIED";

export type OrderStatus =
  | "PENDING"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "CANCELLED";

/* Mirrors `repairs.serializers.DefectReportListSerializer`. The list endpoint
 * exposes `drone` as an id only (no name) and has no `status` field/filter. */
export interface DefectListItem {
  id: number;
  drone: number;
  defect_type: string;
  severity: DefectSeverity;
  detected_at: string;
  reporter: number | null;
  created_at: string;
}
