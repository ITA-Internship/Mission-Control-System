import { useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts";
import { cn } from "./ui/utils";

const FLEET_DATA = [
  { status: "Active",         count: 18, color: "#3FB950" },
  { status: "In Mission",     count: 7,  color: "#4C8DFF" },
  { status: "Maintenance",    count: 5,  color: "#C8A24A" },
  { status: "Damaged",        count: 3,  color: "#E5484D" },
  { status: "Lost",           count: 1,  color: "#8A94A6" },
  { status: "Decommissioned", count: 0,  color: "#4A5568" },
];

const TOTAL = FLEET_DATA.reduce((s, d) => s + d.count, 0);

type ChartView = "donut" | "bar";

function SkeletonChart() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="flex items-center justify-between">
        <div className="h-4 w-28 bg-white/10 rounded" />
        <div className="h-7 w-24 bg-white/10 rounded-lg" />
      </div>
      <div className="h-48 bg-white/5 rounded-xl" />
      <div className="space-y-2">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="w-2.5 h-2.5 rounded-full bg-white/10" />
            <div className="h-3 flex-1 bg-white/10 rounded" />
            <div className="h-3 w-8 bg-white/10 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; payload: { status: string; color: string } }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="px-3 py-2 rounded-lg border border-border text-[12px]" style={{ background: "#1C2530" }}>
      <span className="font-mono font-semibold" style={{ color: d.color }}>{d.status}</span>
      <span className="text-[#8A94A6] ml-2">— </span>
      <span className="font-mono font-semibold text-[#E6EAF0]">{payload[0].value}</span>
      <span className="text-[#8A94A6] ml-1">units</span>
    </div>
  );
}

interface FleetStatusChartProps {
  loading?: boolean;
}

export function FleetStatusChart({ loading = false }: FleetStatusChartProps) {
  const [view, setView] = useState<ChartView>("donut");
  const [hovered, setHovered] = useState<string | null>(null);

  if (loading) return (
    <div className="rounded-xl border border-border p-5 h-full" style={{ background: "var(--card)" }}>
      <SkeletonChart />
    </div>
  );

  return (
    <div className="rounded-xl border border-border p-5 h-full flex flex-col" style={{ background: "var(--card)" }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[13px] font-semibold text-[#E6EAF0] uppercase tracking-wider">Fleet Status</h3>
        <div className="flex items-center gap-1 p-0.5 rounded-lg border border-border" style={{ background: "#0B0F14" }}>
          {(["donut", "bar"] as ChartView[]).map(v => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={cn(
                "px-2.5 py-1 rounded-md font-mono text-[10px] uppercase tracking-wide transition-all duration-150",
                view === v
                  ? "bg-[#C8A24A]/15 text-[#C8A24A]"
                  : "text-[#8A94A6] hover:text-[#E6EAF0]"
              )}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-0" style={{ height: "180px" }}>
        <ResponsiveContainer width="100%" height="100%">
          {view === "donut" ? (
            <PieChart>
              <Pie
                data={FLEET_DATA}
                cx="50%"
                cy="50%"
                innerRadius={52}
                outerRadius={78}
                dataKey="count"
                nameKey="status"
                paddingAngle={2}
                onMouseEnter={(_, idx) => setHovered(FLEET_DATA[idx].status)}
                onMouseLeave={() => setHovered(null)}
              >
                {FLEET_DATA.map((entry) => (
                  <Cell
                    key={entry.status}
                    fill={entry.color}
                    opacity={hovered && hovered !== entry.status ? 0.35 : 1}
                    style={{ cursor: "pointer", outline: "none" }}
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              {/* Center label */}
            </PieChart>
          ) : (
            <BarChart data={FLEET_DATA} layout="vertical" margin={{ left: 0, right: 16, top: 4, bottom: 4 }}>
              <CartesianGrid horizontal={false} stroke="rgba(255,255,255,0.05)" />
              <XAxis
                type="number"
                tick={{ fill: "#8A94A6", fontSize: 10, fontFamily: "JetBrains Mono, monospace" }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="status"
                tick={{ fill: "#8A94A6", fontSize: 10, fontFamily: "JetBrains Mono, monospace" }}
                axisLine={false}
                tickLine={false}
                width={90}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
              <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={18}>
                {FLEET_DATA.map((entry) => (
                  <Cell key={entry.status} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Donut center overlay */}
      {view === "donut" && (
        <div className="flex flex-col items-center -mt-1 mb-2" style={{ marginTop: "-148px", marginBottom: "8px", pointerEvents: "none", position: "relative", zIndex: 1, height: 0 }}>
          <div style={{ position: "absolute", top: "-80px", left: "50%", transform: "translateX(-50%)", textAlign: "center" }}>
            <div className="font-mono font-bold text-[#E6EAF0]" style={{ fontSize: "22px", lineHeight: 1 }}>{TOTAL}</div>
            <div className="font-mono text-[10px] text-[#8A94A6] uppercase tracking-wider mt-0.5">Total</div>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-1.5">
        {FLEET_DATA.map((entry) => (
          <div
            key={entry.status}
            className="flex items-center justify-between group cursor-default"
            onMouseEnter={() => setHovered(entry.status)}
            onMouseLeave={() => setHovered(null)}
          >
            <div className="flex items-center gap-2 min-w-0">
              <span className="w-2 h-2 rounded-full shrink-0" style={{ background: entry.color }} />
              <span className={cn(
                "font-mono text-[11px] truncate transition-colors",
                hovered === entry.status ? "text-[#E6EAF0]" : "text-[#8A94A6]"
              )}>
                {entry.status}
              </span>
            </div>
            <span className={cn(
              "font-mono text-[11px] font-semibold ml-2 shrink-0 transition-colors",
              hovered === entry.status ? "text-[#E6EAF0]" : "text-[#8A94A6]"
            )}>
              {entry.count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
