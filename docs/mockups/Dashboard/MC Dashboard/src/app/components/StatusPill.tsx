import { cn } from "./ui/utils";

export type DroneStatus = "Active" | "In Mission" | "Maintenance" | "Damaged" | "Lost" | "Decommissioned";
export type SeverityLevel = "Low" | "Medium" | "High" | "Critical";
export type MissionStatus = "Active" | "Planning" | "Completed" | "Aborted" | "Delayed";
export type SystemHealth = "Operational" | "Degraded" | "Critical";

const droneStatusConfig: Record<DroneStatus, { label: string; bg: string; text: string; dot: string }> = {
  Active:          { label: "Active",          bg: "bg-[#3FB950]/15", text: "text-[#3FB950]", dot: "bg-[#3FB950]" },
  "In Mission":    { label: "In Mission",      bg: "bg-[#4C8DFF]/15", text: "text-[#4C8DFF]", dot: "bg-[#4C8DFF]" },
  Maintenance:     { label: "Maintenance",     bg: "bg-[#C8A24A]/15", text: "text-[#C8A24A]", dot: "bg-[#C8A24A]" },
  Damaged:         { label: "Damaged",         bg: "bg-[#E5484D]/15", text: "text-[#E5484D]", dot: "bg-[#E5484D]" },
  Lost:            { label: "Lost",            bg: "bg-[#8A94A6]/15", text: "text-[#8A94A6]", dot: "bg-[#8A94A6]" },
  Decommissioned:  { label: "Decommissioned",  bg: "bg-[#4A5568]/25", text: "text-[#8A94A6]", dot: "bg-[#4A5568]" },
};

const severityConfig: Record<SeverityLevel, { label: string; bg: string; text: string }> = {
  Low:      { label: "Low",      bg: "bg-[#8A94A6]/15", text: "text-[#8A94A6]" },
  Medium:   { label: "Medium",   bg: "bg-[#C8A24A]/15", text: "text-[#C8A24A]" },
  High:     { label: "High",     bg: "bg-[#F0883E]/15", text: "text-[#F0883E]" },
  Critical: { label: "Critical", bg: "bg-[#E5484D]/20", text: "text-[#E5484D]" },
};

const missionStatusConfig: Record<MissionStatus, { label: string; bg: string; text: string }> = {
  Active:    { label: "Active",    bg: "bg-[#3FB950]/15", text: "text-[#3FB950]" },
  Planning:  { label: "Planning",  bg: "bg-[#4C8DFF]/15", text: "text-[#4C8DFF]" },
  Completed: { label: "Completed", bg: "bg-[#8A94A6]/15", text: "text-[#8A94A6]" },
  Aborted:   { label: "Aborted",   bg: "bg-[#E5484D]/15", text: "text-[#E5484D]" },
  Delayed:   { label: "Delayed",   bg: "bg-[#F0883E]/15", text: "text-[#F0883E]" },
};

const healthConfig: Record<SystemHealth, { label: string; bg: string; text: string; dot: string }> = {
  Operational: { label: "Operational", bg: "bg-[#3FB950]/15", text: "text-[#3FB950]", dot: "bg-[#3FB950]" },
  Degraded:    { label: "Degraded",    bg: "bg-[#F0883E]/15", text: "text-[#F0883E]", dot: "bg-[#F0883E]" },
  Critical:    { label: "Critical",    bg: "bg-[#E5484D]/15", text: "text-[#E5484D]", dot: "bg-[#E5484D]" },
};

interface StatusPillProps {
  type: "drone" | "severity" | "mission" | "health";
  value: DroneStatus | SeverityLevel | MissionStatus | SystemHealth;
  showDot?: boolean;
  className?: string;
}

export function StatusPill({ type, value, showDot = false, className }: StatusPillProps) {
  let config: { label: string; bg: string; text: string; dot?: string };

  if (type === "drone") config = droneStatusConfig[value as DroneStatus];
  else if (type === "severity") config = severityConfig[value as SeverityLevel];
  else if (type === "mission") config = missionStatusConfig[value as MissionStatus];
  else config = healthConfig[value as SystemHealth];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full font-mono text-[11px] font-medium tracking-wide uppercase whitespace-nowrap",
        config.bg,
        config.text,
        className
      )}
    >
      {(showDot && config.dot) && (
        <span className={cn("w-1.5 h-1.5 rounded-full shrink-0", config.dot)} />
      )}
      {config.label}
    </span>
  );
}

export { droneStatusConfig, severityConfig, missionStatusConfig, healthConfig };
