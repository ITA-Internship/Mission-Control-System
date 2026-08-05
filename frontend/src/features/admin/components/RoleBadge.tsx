import { getRolePillStyle } from "../constants/adminCatalog";
import type { Role } from "../types/admin";

interface RoleBadgeProps {
  role: Role | null;
}

export function RoleBadge({
  role,
}: RoleBadgeProps) {
  if (!role) {
    return (
      <span className="font-mono text-xs text-mc-subtle">
        No role
      </span>
    );
  }

  const label = (role.code || role.name)
    .replace(/_/g, " ")
    .toUpperCase();

  return (
    <span
      className={[
        "inline-flex items-center rounded-full border px-2 py-0.5",
        "text-[11px] font-semibold tracking-wide whitespace-nowrap",
        getRolePillStyle(role.code).className,
      ].join(" ")}
      title={role.name}
    >
      {label}
    </span>
  );
}
