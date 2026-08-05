import { describeTableError } from "../../admin/utils/adminErrors";

export { describeTableError };

export const REPAIRS_ENDPOINTS = {
  defects: "/api/repairs/defects/",
  orders: "/api/repairs/orders/",
  replacements: "/api/repairs/replacements/",
  replacementsExport: "/api/repairs/replacements/export/",
} as const;
