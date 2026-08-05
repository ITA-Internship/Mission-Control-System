import { getAuditActionStyle } from "../constants/adminCatalog";

interface AuditActionPillProps {
  actionType: string;
}

export function AuditActionPill({
  actionType,
}: AuditActionPillProps) {
  return (
    <span
      className={[
        "inline-flex items-center rounded px-2 py-0.5",
        "font-mono text-[11px] font-medium tracking-wider whitespace-nowrap",
        getAuditActionStyle(actionType).className,
      ].join(" ")}
    >
      {actionType || "UNKNOWN"}
    </span>
  );
}
