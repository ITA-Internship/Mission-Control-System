import { useState } from "react";
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Panel } from "../../../shared/components/Panel";
import {
  EmptyState,
  ErrorState,
  Skeleton,
} from "../../../shared/components/states";
import { cn } from "../../../shared/utils/cn";
import type { FleetStatusSlice } from "../types/dashboard";

type ChartView = "donut" | "bar";

interface TooltipEntry {
  value: number;
  payload: FleetStatusSlice;
}

function ChartTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: TooltipEntry[];
}) {
  if (!active || !payload?.length) return null;
  const slice = payload[0].payload;
  return (
    <div className="rounded-lg border border-mc-border bg-mc-popover px-3 py-2 text-[12px]">
      <span
        className="font-mono font-semibold"
        style={{ color: slice.color }}
      >
        {slice.label}
      </span>
      <span className="ml-2 font-mono font-semibold text-mc-text">
        {payload[0].value}
      </span>
      <span className="ml-1 text-mc-muted">units</span>
    </div>
  );
}

function ViewToggle({
  view,
  onChange,
}: {
  view: ChartView;
  onChange: (view: ChartView) => void;
}) {
  return (
    <div className="flex items-center gap-1 rounded-lg border border-mc-border bg-mc-bg p-0.5">
      {(["donut", "bar"] as ChartView[]).map((option) => (
        <button
          key={option}
          type="button"
          onClick={() => onChange(option)}
          aria-pressed={view === option}
          className={cn(
            "rounded-md px-2.5 py-1 font-mono text-[10px] uppercase tracking-wide transition-colors",
            view === option
              ? "bg-mc-accent/15 text-mc-accent"
              : "text-mc-muted hover:text-mc-text",
          )}
        >
          {option}
        </button>
      ))}
    </div>
  );
}

function Legend({
  data,
  hovered,
  onHover,
}: {
  data: FleetStatusSlice[];
  hovered: string | null;
  onHover: (status: string | null) => void;
}) {
  return (
    <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-1.5">
      {data.map((slice) => (
        <div
          key={slice.status}
          className="flex items-center justify-between"
          onMouseEnter={() => onHover(slice.status)}
          onMouseLeave={() => onHover(null)}
        >
          <div className="flex min-w-0 items-center gap-2">
            <span
              className="h-2 w-2 shrink-0 rounded-full"
              style={{ background: slice.color }}
            />
            <span
              className={cn(
                "truncate font-mono text-[11px] transition-colors",
                hovered === slice.status
                  ? "text-mc-text"
                  : "text-mc-muted",
              )}
            >
              {slice.label}
            </span>
          </div>
          <span
            className={cn(
              "ml-2 shrink-0 font-mono text-[11px] font-semibold transition-colors",
              hovered === slice.status
                ? "text-mc-text"
                : "text-mc-muted",
            )}
          >
            {slice.count}
          </span>
        </div>
      ))}
    </div>
  );
}

function SkeletonChart() {
  return (
    <div className="space-y-4">
      <Skeleton className="mx-auto h-44 w-44 rounded-full" />
      <div className="grid grid-cols-2 gap-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-3" />
        ))}
      </div>
    </div>
  );
}

export function FleetStatusChart({
  fleet,
  loading,
  error,
}: {
  fleet: FleetStatusSlice[] | null;
  loading: boolean;
  error?: boolean;
}) {
  const [view, setView] = useState<ChartView>("donut");
  const [hovered, setHovered] = useState<string | null>(null);

  const data = (fleet ?? []).filter((slice) => slice.count > 0);
  const total = data.reduce((sum, slice) => sum + slice.count, 0);

  return (
    <Panel
      title="Fleet Status"
      action={
        !loading && !error && total > 0 ? (
          <ViewToggle view={view} onChange={setView} />
        ) : undefined
      }
    >
      {loading ? (
        <SkeletonChart />
      ) : error ? (
        <ErrorState />
      ) : total === 0 ? (
        <EmptyState title="No fleet data" description="No drones registered yet." />
      ) : (
        <>
          <div
            className="relative w-full min-w-0"
            style={{ height: 200 }}
            role="img"
            aria-label={`Fleet status: ${total} drones — ${data
              .map((slice) => `${slice.label} ${slice.count}`)
              .join(", ")}.`}
          >
            <ResponsiveContainer width="100%" height="100%">
              {view === "donut" ? (
                <PieChart>
                  <Pie
                    data={data}
                    cx="50%"
                    cy="50%"
                    innerRadius={56}
                    outerRadius={84}
                    dataKey="count"
                    nameKey="label"
                    paddingAngle={2}
                    onMouseEnter={(_, index) =>
                      setHovered(data[index].status)
                    }
                    onMouseLeave={() => setHovered(null)}
                  >
                    {data.map((slice) => (
                      <Cell
                        key={slice.status}
                        fill={slice.color}
                        opacity={
                          hovered && hovered !== slice.status ? 0.35 : 1
                        }
                        style={{ cursor: "pointer", outline: "none" }}
                      />
                    ))}
                  </Pie>
                  <Tooltip content={<ChartTooltip />} />
                </PieChart>
              ) : (
                <BarChart
                  data={data}
                  layout="vertical"
                  margin={{ left: 0, right: 16, top: 4, bottom: 4 }}
                >
                  <XAxis
                    type="number"
                    tick={{ fill: "var(--color-mc-muted)", fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    type="category"
                    dataKey="label"
                    tick={{ fill: "var(--color-mc-muted)", fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                    width={92}
                  />
                  <Tooltip
                    content={<ChartTooltip />}
                    cursor={{ fill: "rgba(255,255,255,0.04)" }}
                  />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={18}>
                    {data.map((slice) => (
                      <Cell key={slice.status} fill={slice.color} />
                    ))}
                  </Bar>
                </BarChart>
              )}
            </ResponsiveContainer>
            {view === "donut" && (
              <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                <span className="font-mono text-[22px] font-bold leading-none text-mc-text">
                  {total}
                </span>
                <span className="mt-0.5 font-mono text-[10px] uppercase tracking-wider text-mc-muted">
                  Total
                </span>
              </div>
            )}
          </div>
          <Legend
            data={data}
            hovered={hovered}
            onHover={setHovered}
          />
        </>
      )}
    </Panel>
  );
}
