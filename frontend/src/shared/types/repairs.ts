export type DefectSeverity =
  | "LOW"
  | "MEDIUM"
  | "HIGH"
  | "CRITICAL";

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
