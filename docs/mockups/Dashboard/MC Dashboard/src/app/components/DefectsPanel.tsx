import { ArrowRight, ShieldAlert } from "lucide-react";
import { StatusPill } from "./StatusPill";
import type { SeverityLevel } from "./StatusPill";
import { cn } from "./ui/utils";

interface Defect {
  id: string;
  drone: string;
  type: string;
  severity: SeverityLevel;
  reportedBy: string;
  reportedAt: string;
}

const DEFECTS: Defect[] = [
  { id: "DEF-441", drone: "DRONE-047", type: "Signal Loss — GPS module",       severity: "Critical", reportedBy: "Auto-detect",    reportedAt: "08:03 UTC" },
  { id: "DEF-440", drone: "DRONE-031", type: "Gimbal mechanical fault",         severity: "Critical", reportedBy: "Cpt. A. Rourke", reportedAt: "07:55 UTC" },
  { id: "DEF-439", drone: "DRONE-019", type: "Battery cell degradation >25%",   severity: "Critical", reportedBy: "Lt. S. Petrov",  reportedAt: "06:12 UTC" },
  { id: "DEF-438", drone: "DRONE-012", type: "Propeller micro-fracture Port-2", severity: "Critical", reportedBy: "Tech. M. Kwan",  reportedAt: "Yesterday" },
  { id: "DEF-435", drone: "DRONE-028", type: "Transmission jitter — 2.4 GHz",   severity: "High",     reportedBy: "Auto-detect",    reportedAt: "Yesterday" },
  { id: "DEF-433", drone: "DRONE-022", type: "Compass calibration drift",       severity: "High",     reportedBy: "Tech. D. Osei",  reportedAt: "Yesterday" },
  { id: "DEF-430", drone: "DRONE-009", type: "ESC thermal warning — Starboard", severity: "High",     reportedBy: "Auto-detect",    reportedAt: "2d ago" },
  { id: "DEF-427", drone: "DRONE-041", type: "Camera lens moisture ingress",    severity: "Medium",   reportedBy: "Cpt. F. Liang",  reportedAt: "2d ago" },
  { id: "DEF-420", drone: "DRONE-033", type: "Firmware update pending v4.2.1",  severity: "Low",      reportedBy: "System",         reportedAt: "3d ago" },
];

function SkeletonRow() {
  return (
    <div className="flex items-center gap-3 py-2.5 animate-pulse">
      <div className="w-16 h-3 bg-white/10 rounded" />
      <div className="flex-1 h-3 bg-white/10 rounded" />
      <div className="w-14 h-5 bg-white/10 rounded-full" />
    </div>
  );
}

interface DefectsPanelProps {
  loading?: boolean;
}

export function DefectsPanel({ loading = false }: DefectsPanelProps) {
  return (
    <div className="rounded-xl border border-border p-5 flex flex-col h-full" style={{ background: "var(--card)" }}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[13px] font-semibold text-[#E6EAF0] uppercase tracking-wider">Open Defects</h3>
        <div className="flex items-center gap-3">
          <span className="font-mono text-[11px] text-[#E5484D] bg-[#E5484D]/15 px-2 py-0.5 rounded-full">4 Critical</span>
          <button className="flex items-center gap-1 font-mono text-[11px] text-[#C8A24A] hover:text-[#E6EAF0] transition-colors uppercase tracking-wide">
            View all <ArrowRight className="w-3 h-3" />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="divide-y divide-border">
          {[...Array(5)].map((_, i) => <SkeletonRow key={i} />)}
        </div>
      ) : DEFECTS.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center py-10 gap-3">
          <ShieldAlert className="w-8 h-8 text-[#2E3A4A]" />
          <p className="text-[13px] text-[#8A94A6]">No open defects</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto -mx-1 px-1">
          {/* Column headers */}
          <div className="grid grid-cols-[4.5rem_1fr_5.5rem_4.5rem] gap-x-3 mb-1 px-1">
            {["REF", "DEFECT", "SEVERITY", "REPORTED"].map(h => (
              <span key={h} className="font-mono text-[10px] text-[#8A94A6] uppercase tracking-wider">{h}</span>
            ))}
          </div>

          <div className="divide-y divide-border">
            {DEFECTS.map((d) => (
              <div
                key={d.id}
                className={cn(
                  "grid grid-cols-[4.5rem_1fr_5.5rem_4.5rem] gap-x-3 items-center py-2.5 px-1 -mx-1 rounded-lg",
                  "hover:bg-white/5 cursor-pointer transition-colors group",
                  d.severity === "Critical" && "border-l-2 border-l-[#E5484D] pl-[calc(0.25rem-2px)]"
                )}
              >
                <span className={cn(
                  "font-mono text-[11px]",
                  d.severity === "Critical" ? "text-[#E5484D] font-semibold" : "text-[#8A94A6]"
                )}>
                  {d.id}
                </span>
                <div className="min-w-0">
                  <div className="font-mono text-[11px] font-medium text-[#E6EAF0] truncate group-hover:text-[#C8A24A] transition-colors">
                    {d.type}
                  </div>
                  <div className="font-mono text-[10px] text-[#8A94A6] truncate">{d.drone} · {d.reportedBy}</div>
                </div>
                <StatusPill type="severity" value={d.severity} />
                <span className="font-mono text-[10px] text-[#8A94A6]">{d.reportedAt}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
