import type { Classification, DroneStatus } from "../types";

export const STATUS_UI: Record<DroneStatus, { label: string; dot: string; color: string }> = {
  ACTIVE: { label: "Active", dot: "bg-[#3FB950]", color: "text-[#3FB950]" },
  IN_MISSION: { label: "In mission", dot: "bg-[#4C8DFF]", color: "text-[#4C8DFF]" },
  DAMAGED: { label: "Damaged", dot: "bg-[#D2A8FF]", color: "text-[#D2A8FF]" },
  LOST: { label: "Lost", dot: "bg-[#E5484D]", color: "text-[#E5484D]" },
  MAINTENANCE: { label: "Maintenance", dot: "bg-[#D2A8FF]", color: "text-[#D2A8FF]" },
  DECOMMISSIONED: { label: "Decommissioned", dot: "bg-[#8A94A6]", color: "text-[#8A94A6]" },
  SOLD: { label: "Sold", dot: "bg-[#8A94A6]", color: "text-[#8A94A6]" },
  TRANSFERRED: { label: "Transferred", dot: "bg-[#8A94A6]", color: "text-[#8A94A6]" },
  WRITTEN_OFF: { label: "Written off", dot: "bg-[#E5484D]", color: "text-[#E5484D]" },
};

export const CLASSIFICATIONS: Classification[] = [
  "RECONNAISSANCE",
  "COMBAT",
  "TRANSPORT",
  "SURVEILLANCE",
];

export const CLASS_COLORS: Record<Classification, string> = {
  RECONNAISSANCE: "bg-[#1a2840] text-[#4C8DFF] border border-[#4C8DFF]/30",
  COMBAT: "bg-[#2a1518] text-[#E5484D] border border-[#E5484D]/30",
  TRANSPORT: "bg-[#1e2a1a] text-[#3FB950] border border-[#3FB950]/30",
  SURVEILLANCE: "bg-[#2a2010] text-[#C8A24A] border border-[#C8A24A]/30",
};
