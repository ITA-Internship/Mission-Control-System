interface RepairsKpiCardsProps {
  openDefects: number | null;
  criticalDefects: number | null;
  activeOrders: number | null;
  isLoading: boolean;
}

function KpiCard({
  label,
  value,
  tone,
  isLoading,
}: {
  label: string;
  value: number | null;
  tone: "accent" | "error" | "mission";
  isLoading: boolean;
}) {
  const toneClasses = {
    accent: "border-mc-accent/35 text-mc-accent",
    error: "border-mc-error/35 text-mc-error",
    mission: "border-[var(--color-status-mission)]/35 text-[var(--color-status-mission)]",
  };

  return (
    <div
      className={[
        "min-w-[7.5rem] rounded-lg border px-4 py-3 text-center",
        toneClasses[tone],
      ].join(" ")}
    >
      <p className="font-mono text-2xl font-bold tabular-nums">
        {isLoading || value === null ? "—" : value}
      </p>
      <p className="mt-0.5 font-mono text-[10px] font-semibold tracking-widest uppercase">
        {label}
      </p>
    </div>
  );
}

export function RepairsKpiCards({
  openDefects,
  criticalDefects,
  activeOrders,
  isLoading,
}: RepairsKpiCardsProps) {
  return (
    <div className="flex flex-wrap gap-3">
      <KpiCard
        label="Open defects"
        value={openDefects}
        tone="accent"
        isLoading={isLoading}
      />
      <KpiCard
        label="Critical"
        value={criticalDefects}
        tone="error"
        isLoading={isLoading}
      />
      <KpiCard
        label="Active orders"
        value={activeOrders}
        tone="mission"
        isLoading={isLoading}
      />
    </div>
  );
}
