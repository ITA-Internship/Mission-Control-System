import type { DefectSeverity } from "../../../shared/types/repairs";
import type {
  DefectTransitionStatus,
  OrderStatus,
} from "../types";

export const REPAIRS_PAGE_SIZE = 20;

export const SEVERITY_OPTIONS: {
  value: DefectSeverity;
  label: string;
}[] = [
  { value: "LOW", label: "Low" },
  { value: "MEDIUM", label: "Medium" },
  { value: "HIGH", label: "High" },
  { value: "CRITICAL", label: "Critical" },
];

export const DEFECT_STATUS_OPTIONS: {
  value: DefectTransitionStatus;
  label: string;
}[] = [
  { value: "REPORTED", label: "Reported" },
  { value: "IN_PROGRESS", label: "In progress" },
  { value: "FIXED", label: "Fixed" },
  { value: "VERIFIED", label: "Verified" },
];

export const ORDER_STATUS_OPTIONS: {
  value: OrderStatus;
  label: string;
}[] = [
  { value: "PENDING", label: "Pending" },
  { value: "IN_PROGRESS", label: "In progress" },
  { value: "COMPLETED", label: "Completed" },
  { value: "CANCELLED", label: "Cancelled" },
];

export const DEFECT_TYPE_OPTIONS = [
  { value: "MOTOR", label: "Motor" },
  { value: "BATTERY", label: "Battery" },
  { value: "CAMERA", label: "Camera" },
  { value: "FRAME", label: "Frame" },
  { value: "PROPELLER", label: "Propeller" },
  {
    value: "FLIGHT_CONTROLLER",
    label: "Flight controller",
  },
  { value: "VTX", label: "Video transmitter" },
  { value: "WIRING", label: "Wiring" },
  { value: "FIRMWARE", label: "Firmware" },
  { value: "OTHER", label: "Other" },
];

export const COMPONENT_TYPE_OPTIONS = [
  { value: "MOTOR", label: "Motor" },
  { value: "BATTERY", label: "Battery" },
  { value: "CAMERA", label: "Camera" },
  { value: "FRAME", label: "Frame" },
  { value: "PROPELLER", label: "Propeller" },
  {
    value: "FLIGHT_CONTROLLER",
    label: "Flight controller",
  },
  { value: "VTX", label: "Video transmitter" },
  { value: "WIRING", label: "Wiring" },
  { value: "OTHER", label: "Other" },
];
