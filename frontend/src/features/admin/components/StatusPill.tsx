interface StatusPillProps {
  isActive: boolean;
  activeLabel?: string;
  inactiveLabel?: string;
}

export function StatusPill({
  isActive,
  activeLabel = "Active",
  inactiveLabel = "Inactive",
}: StatusPillProps) {
  return (
    <span
      className={[
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5",
        "text-[11px] font-semibold whitespace-nowrap",
        isActive
          ? "bg-mc-success/12 text-mc-success"
          : "bg-mc-muted/12 text-mc-muted",
      ].join(" ")}
    >
      <span
        className="size-1.5 rounded-full bg-current"
        aria-hidden="true"
      />

      {isActive ? activeLabel : inactiveLabel}
    </span>
  );
}
