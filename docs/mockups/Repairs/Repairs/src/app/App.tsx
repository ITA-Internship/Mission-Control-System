import { useState, useRef, useEffect } from "react";
import {
  Search, ChevronDown, X, Plus, Download, ChevronRight,
  AlertTriangle, Wrench, RefreshCw, LayoutDashboard, Radio,
  FileText, Settings, Users, Shield, Bell, HelpCircle,
  Clock, CheckCircle, ArrowRight, Filter, MoreHorizontal,
  ChevronUp, Cpu, SortAsc, SortDesc, Loader2
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

type Severity = "Low" | "Medium" | "High" | "Critical";
type DefectStatus = "Reported" | "In Progress" | "Fixed" | "Verified";
type OrderStatus = "Pending" | "In Progress" | "Completed" | "Cancelled";

interface Defect {
  id: string;
  drone: string;
  droneSerial: string;
  defectType: string;
  severity: Severity;
  status: DefectStatus;
  detectedAt: string;
  reporter: string;
  description: string;
  history: HistoryEvent[];
}

interface RepairOrder {
  id: string;
  drone: string;
  droneSerial: string;
  defectId: string;
  status: OrderStatus;
  assignedTo: string;
  createdAt: string;
  updatedAt: string;
  notes: string;
}

interface ComponentReplacement {
  id: string;
  drone: string;
  droneSerial: string;
  componentType: string;
  oldSerial: string;
  newSerial: string;
  reason: string;
  replacedAt: string;
  replacedBy: string;
  orderId?: string;
}

interface HistoryEvent {
  id: string;
  timestamp: string;
  actor: string;
  from: string;
  to: string;
  note: string;
}

// ─── Mock Data ────────────────────────────────────────────────────────────────

const DEFECTS: Defect[] = [
  {
    id: "DEF-2241", drone: "Raptor-7", droneSerial: "DRN-0047-RX7", defectType: "Motor Failure",
    severity: "Critical", status: "In Progress", detectedAt: "2026-07-29 14:22", reporter: "Sgt. R. Torres",
    description: "Port-side motor #3 experiencing intermittent power loss during sustained hover at high altitude. Thermal imaging shows abnormal heat signature near motor controller board. Flight logs confirm 4 incidents in the past 72 hours. Unit grounded pending inspection.",
    history: [
      { id: "h1", timestamp: "2026-07-29 14:22", actor: "Sgt. R. Torres", from: "", to: "Reported", note: "Observed during routine inspection post-mission 44B." },
      { id: "h2", timestamp: "2026-07-29 15:45", actor: "Tech. M. Vasquez", from: "Reported", to: "In Progress", note: "Assigned to bay 3. Motor controller board removed for bench testing." },
    ]
  },
  {
    id: "DEF-2238", drone: "Specter-12", droneSerial: "DRN-0052-SP12", defectType: "GPS Module Drift",
    severity: "High", status: "Reported", detectedAt: "2026-07-29 09:11", reporter: "Lt. K. Okafor",
    description: "GPS module reporting 8-12m positional drift in urban canyon environments. GNSS lock stability degraded. Affects mission-critical waypoint tracking.",
    history: [
      { id: "h1", timestamp: "2026-07-29 09:11", actor: "Lt. K. Okafor", from: "", to: "Reported", note: "Flagged after mission debrief Delta-7." },
    ]
  },
  {
    id: "DEF-2231", drone: "Ghost-3", droneSerial: "DRN-0038-GH3", defectType: "Gimbal Calibration",
    severity: "Medium", status: "Fixed", detectedAt: "2026-07-27 11:30", reporter: "Tech. S. Patel",
    description: "Gimbal pitch axis shows 2.3° bias at power-on. Corrected via calibration routine v4.1.2. Awaiting verification flight.",
    history: [
      { id: "h1", timestamp: "2026-07-27 11:30", actor: "Tech. S. Patel", from: "", to: "Reported", note: "Calibration drift detected during pre-flight check." },
      { id: "h2", timestamp: "2026-07-27 14:00", actor: "Tech. M. Vasquez", from: "Reported", to: "In Progress", note: "Running calibration routine." },
      { id: "h3", timestamp: "2026-07-28 08:20", actor: "Tech. M. Vasquez", from: "In Progress", to: "Fixed", note: "Calibration complete. Bias within 0.1° tolerance." },
    ]
  },
  {
    id: "DEF-2229", drone: "Falcon-1", droneSerial: "DRN-0031-FC1", defectType: "Battery Cell Degradation",
    severity: "High", status: "Verified", detectedAt: "2026-07-26 16:44", reporter: "Sgt. R. Torres",
    description: "Cell 4 of primary battery pack showing 18% capacity below spec. Replaced under RO-0891.",
    history: [
      { id: "h1", timestamp: "2026-07-26 16:44", actor: "Sgt. R. Torres", from: "", to: "Reported", note: "" },
      { id: "h2", timestamp: "2026-07-26 18:00", actor: "Tech. C. Nguyen", from: "Reported", to: "In Progress", note: "Battery pack pulled for testing." },
      { id: "h3", timestamp: "2026-07-27 09:15", actor: "Tech. C. Nguyen", from: "In Progress", to: "Fixed", note: "Pack replaced. Capacity nominal." },
      { id: "h4", timestamp: "2026-07-28 10:30", actor: "Cdr. E. Walsh", from: "Fixed", to: "Verified", note: "Post-replacement flight test passed. Cleared for ops." },
    ]
  },
  {
    id: "DEF-2225", drone: "Specter-9", droneSerial: "DRN-0049-SP9", defectType: "RF Link Interference",
    severity: "Medium", status: "In Progress", detectedAt: "2026-07-25 13:05", reporter: "Tech. A. Kim",
    description: "C-band data link experiencing packet loss >12% at range >4km. Suspected antenna connector corrosion.",
    history: [
      { id: "h1", timestamp: "2026-07-25 13:05", actor: "Tech. A. Kim", from: "", to: "Reported", note: "" },
      { id: "h2", timestamp: "2026-07-25 15:20", actor: "Tech. A. Kim", from: "Reported", to: "In Progress", note: "Antenna assembly disassembled. Connector cleaning in progress." },
    ]
  },
  {
    id: "DEF-2219", drone: "Raptor-4", droneSerial: "DRN-0029-RX4", defectType: "Prop Guard Crack",
    severity: "Low", status: "Reported", detectedAt: "2026-07-24 08:00", reporter: "Tech. S. Patel",
    description: "Hairline crack in starboard prop guard bracket. No flight impact; scheduled for replacement.",
    history: [
      { id: "h1", timestamp: "2026-07-24 08:00", actor: "Tech. S. Patel", from: "", to: "Reported", note: "Found during daily inspection." },
    ]
  },
];

const ORDERS: RepairOrder[] = [
  { id: "RO-0901", drone: "Raptor-7", droneSerial: "DRN-0047-RX7", defectId: "DEF-2241", status: "In Progress", assignedTo: "Tech. M. Vasquez", createdAt: "2026-07-29 15:50", updatedAt: "2026-07-30 08:10", notes: "Motor controller board replacement. Parts on order. ETA 24h." },
  { id: "RO-0899", drone: "Specter-9", droneSerial: "DRN-0049-SP9", defectId: "DEF-2225", status: "In Progress", assignedTo: "Tech. A. Kim", createdAt: "2026-07-25 15:30", updatedAt: "2026-07-29 11:20", notes: "Antenna harness replacement underway." },
  { id: "RO-0891", drone: "Falcon-1", droneSerial: "DRN-0031-FC1", defectId: "DEF-2229", status: "Completed", assignedTo: "Tech. C. Nguyen", createdAt: "2026-07-26 18:05", updatedAt: "2026-07-27 09:30", notes: "Battery pack replaced. Cleared." },
  { id: "RO-0887", drone: "Ghost-3", droneSerial: "DRN-0038-GH3", defectId: "DEF-2231", status: "Pending", assignedTo: "Tech. M. Vasquez", createdAt: "2026-07-29 16:00", updatedAt: "2026-07-29 16:00", notes: "Awaiting verification flight scheduling." },
  { id: "RO-0876", drone: "Raptor-2", droneSerial: "DRN-0018-RX2", defectId: "DEF-2200", status: "Cancelled", assignedTo: "Tech. S. Patel", createdAt: "2026-07-20 10:00", updatedAt: "2026-07-22 14:00", notes: "Unit decommissioned. Order cancelled." },
];

const ORDER_REPLACEMENTS: Record<string, ComponentReplacement[]> = {
  "RO-0901": [
    { id: "CR-0551", drone: "Raptor-7", droneSerial: "DRN-0047-RX7", componentType: "Motor Controller Board", oldSerial: "MCB-2241-A", newSerial: "MCB-2290-B", reason: "Thermal failure", replacedAt: "2026-07-30 08:10", replacedBy: "Tech. M. Vasquez", orderId: "RO-0901" },
  ],
  "RO-0891": [
    { id: "CR-0544", drone: "Falcon-1", droneSerial: "DRN-0031-FC1", componentType: "LiPo Battery Pack (6S)", oldSerial: "BAT-FC1-004", newSerial: "BAT-FC1-009", reason: "Cell degradation >15%", replacedAt: "2026-07-27 09:15", replacedBy: "Tech. C. Nguyen", orderId: "RO-0891" },
  ],
  "RO-0899": [],
};

const REPLACEMENTS: ComponentReplacement[] = [
  { id: "CR-0551", drone: "Raptor-7", droneSerial: "DRN-0047-RX7", componentType: "Motor Controller Board", oldSerial: "MCB-2241-A", newSerial: "MCB-2290-B", reason: "Thermal failure", replacedAt: "2026-07-30 08:10", replacedBy: "Tech. M. Vasquez", orderId: "RO-0901" },
  { id: "CR-0544", drone: "Falcon-1", droneSerial: "DRN-0031-FC1", componentType: "LiPo Battery Pack (6S)", oldSerial: "BAT-FC1-004", newSerial: "BAT-FC1-009", reason: "Cell degradation >15%", replacedAt: "2026-07-27 09:15", replacedBy: "Tech. C. Nguyen", orderId: "RO-0891" },
  { id: "CR-0538", drone: "Specter-12", droneSerial: "DRN-0052-SP12", componentType: "GPS Antenna", oldSerial: "GPS-ANT-0044", newSerial: "GPS-ANT-0061", reason: "Signal drift, connector corrosion", replacedAt: "2026-07-24 13:00", replacedBy: "Tech. A. Kim" },
  { id: "CR-0531", drone: "Ghost-3", droneSerial: "DRN-0038-GH3", componentType: "Gimbal Stabilizer (3-axis)", oldSerial: "GBL-0038-02", newSerial: "GBL-0038-03", reason: "Persistent pitch bias post-calibration", replacedAt: "2026-07-21 10:45", replacedBy: "Tech. S. Patel", orderId: "RO-0871" },
  { id: "CR-0522", drone: "Raptor-4", droneSerial: "DRN-0029-RX4", componentType: "Propeller Guard (Port)", oldSerial: "PG-0029-PL", newSerial: "PG-0029-PL2", reason: "Structural crack", replacedAt: "2026-07-18 09:30", replacedBy: "Tech. C. Nguyen" },
];

const DRONES = ["Raptor-7", "Specter-12", "Ghost-3", "Falcon-1", "Specter-9", "Raptor-4", "Raptor-2"];
const TECHNICIANS = ["Tech. M. Vasquez", "Tech. A. Kim", "Tech. S. Patel", "Tech. C. Nguyen", "Sgt. R. Torres"];

// ─── Utility ──────────────────────────────────────────────────────────────────

const severityConfig: Record<Severity, { color: string; bg: string; label: string }> = {
  Low: { color: "#8A94A6", bg: "rgba(138,148,166,0.12)", label: "LOW" },
  Medium: { color: "#C8A24A", bg: "rgba(200,162,74,0.12)", label: "MED" },
  High: { color: "#F0883E", bg: "rgba(240,136,62,0.12)", label: "HIGH" },
  Critical: { color: "#E5484D", bg: "rgba(229,72,77,0.14)", label: "CRIT" },
};

const defectStatusConfig: Record<DefectStatus, { color: string; bg: string; dot: string }> = {
  "Reported": { color: "#8A94A6", bg: "rgba(138,148,166,0.12)", dot: "#8A94A6" },
  "In Progress": { color: "#C8A24A", bg: "rgba(200,162,74,0.12)", dot: "#C8A24A" },
  "Fixed": { color: "#4C8DFF", bg: "rgba(76,141,255,0.12)", dot: "#4C8DFF" },
  "Verified": { color: "#3FB950", bg: "rgba(63,185,80,0.12)", dot: "#3FB950" },
};

const orderStatusConfig: Record<OrderStatus, { color: string; bg: string; dot: string }> = {
  "Pending": { color: "#8A94A6", bg: "rgba(138,148,166,0.12)", dot: "#8A94A6" },
  "In Progress": { color: "#C8A24A", bg: "rgba(200,162,74,0.12)", dot: "#C8A24A" },
  "Completed": { color: "#3FB950", bg: "rgba(63,185,80,0.12)", dot: "#3FB950" },
  "Cancelled": { color: "#E5484D", bg: "rgba(229,72,77,0.12)", dot: "#E5484D" },
};

// ─── Pill Components ──────────────────────────────────────────────────────────

function SeverityPill({ severity }: { severity: Severity }) {
  const cfg = severityConfig[severity];
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold tracking-wider font-mono"
      style={{ color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.color}22` }}
    >
      {cfg.label}
    </span>
  );
}

function DefectStatusPill({ status }: { status: DefectStatus }) {
  const cfg = defectStatusConfig[status];
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[12px] font-medium"
      style={{ color: cfg.color, background: cfg.bg }}
    >
      <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: cfg.dot }} />
      {status}
    </span>
  );
}

function OrderStatusPill({ status }: { status: OrderStatus }) {
  const cfg = orderStatusConfig[status];
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[12px] font-medium"
      style={{ color: cfg.color, background: cfg.bg }}
    >
      <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: cfg.dot }} />
      {status}
    </span>
  );
}

// ─── Shared UI ────────────────────────────────────────────────────────────────

function Input({ className = "", ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={`bg-[#1A2230] border border-white/10 text-[#E6EAF0] placeholder-[#4A5568] rounded-lg px-3 py-2 text-[13px] outline-none focus:border-[#C8A24A]/60 focus:ring-1 focus:ring-[#C8A24A]/30 transition-all ${className}`}
      {...props}
    />
  );
}

function Select({ className = "", children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={`bg-[#1A2230] border border-white/10 text-[#E6EAF0] rounded-lg px-3 py-2 text-[13px] outline-none focus:border-[#C8A24A]/60 focus:ring-1 focus:ring-[#C8A24A]/30 transition-all appearance-none cursor-pointer ${className}`}
      {...props}
    >
      {children}
    </select>
  );
}

function Textarea({ className = "", ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={`bg-[#1A2230] border border-white/10 text-[#E6EAF0] placeholder-[#4A5568] rounded-lg px-3 py-2 text-[13px] outline-none focus:border-[#C8A24A]/60 focus:ring-1 focus:ring-[#C8A24A]/30 transition-all resize-none ${className}`}
      {...props}
    />
  );
}

function Label({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <label className={`block text-[11px] font-semibold uppercase tracking-widest text-[#8A94A6] mb-1.5 ${className}`}>
      {children}
    </label>
  );
}

function PrimaryButton({ children, onClick, className = "", disabled = false }: {
  children: React.ReactNode; onClick?: () => void; className?: string; disabled?: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex items-center gap-2 bg-[#C8A24A] text-[#0B0F14] px-4 py-2 rounded-lg text-[13px] font-semibold hover:bg-[#D9B35C] active:bg-[#B8922A] transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
    >
      {children}
    </button>
  );
}

function GhostButton({ children, onClick, className = "" }: {
  children: React.ReactNode; onClick?: () => void; className?: string
}) {
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-2 bg-transparent border border-white/10 text-[#8A94A6] hover:text-[#E6EAF0] hover:border-white/20 px-4 py-2 rounded-lg text-[13px] font-medium transition-all ${className}`}
    >
      {children}
    </button>
  );
}

function FilterChip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-1.5 bg-[#C8A24A]/10 border border-[#C8A24A]/30 text-[#C8A24A] px-2.5 py-1 rounded-full text-[12px] font-medium">
      {label}
      <button onClick={onRemove} className="hover:text-[#E6EAF0] transition-colors">
        <X size={11} />
      </button>
    </span>
  );
}

// ─── Modal / Drawer overlay ───────────────────────────────────────────────────

function Overlay({ onClick }: { onClick: () => void }) {
  return (
    <div
      className="fixed inset-0 bg-black/50 z-40 backdrop-blur-sm"
      onClick={onClick}
    />
  );
}

// ─── Status Transition Modal ──────────────────────────────────────────────────

function StatusTransitionModal({
  title, currentStatus, options, onConfirm, onClose
}: {
  title: string;
  currentStatus: string;
  options: string[];
  onConfirm: (to: string, note: string) => void;
  onClose: () => void;
}) {
  const [to, setTo] = useState(options[0]);
  const [note, setNote] = useState("");

  return (
    <>
      <Overlay onClick={onClose} />
      <div className="fixed inset-0 flex items-center justify-center z-50 pointer-events-none">
        <div className="bg-[#161D26] border border-white/10 rounded-xl shadow-2xl w-full max-w-md pointer-events-auto mx-4">
          <div className="flex items-center justify-between p-5 border-b border-white/8">
            <h3 className="text-[15px] font-semibold text-[#E6EAF0]">{title}</h3>
            <button onClick={onClose} className="text-[#8A94A6] hover:text-[#E6EAF0] transition-colors">
              <X size={18} />
            </button>
          </div>
          <div className="p-5 space-y-4">
            <div className="flex items-center gap-3">
              <span className="text-[13px] text-[#8A94A6] bg-[#1A2230] px-3 py-1.5 rounded-lg border border-white/8">{currentStatus}</span>
              <ArrowRight size={14} className="text-[#8A94A6]" />
              <Select value={to} onChange={e => setTo(e.target.value)} className="flex-1">
                {options.map(o => <option key={o}>{o}</option>)}
              </Select>
            </div>
            <div>
              <Label>Transition Note</Label>
              <Textarea
                rows={3}
                value={note}
                onChange={e => setNote(e.target.value)}
                placeholder="Optional — describe what was done or observed..."
                className="w-full"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 p-5 border-t border-white/8">
            <GhostButton onClick={onClose}>Cancel</GhostButton>
            <PrimaryButton onClick={() => onConfirm(to, note)}>Apply Transition</PrimaryButton>
          </div>
        </div>
      </div>
    </>
  );
}

// ─── Event History Timeline ───────────────────────────────────────────────────

function EventTimeline({ events }: { events: HistoryEvent[] }) {
  return (
    <div className="space-y-0">
      {events.map((ev, i) => (
        <div key={ev.id} className="flex gap-3">
          <div className="flex flex-col items-center">
            <div className="w-2 h-2 rounded-full bg-[#C8A24A] flex-shrink-0 mt-1" />
            {i < events.length - 1 && <div className="w-px flex-1 bg-white/8 my-1" />}
          </div>
          <div className="pb-4 flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              {ev.from && ev.to ? (
                <>
                  <span className="text-[11px] font-medium text-[#8A94A6]">{ev.from}</span>
                  <ArrowRight size={10} className="text-[#8A94A6]" />
                  <span className="text-[11px] font-medium text-[#E6EAF0]">{ev.to}</span>
                </>
              ) : (
                <span className="text-[11px] font-medium text-[#E6EAF0]">{ev.to}</span>
              )}
              <span className="text-[11px] text-[#8A94A6] ml-auto font-mono">{ev.timestamp}</span>
            </div>
            <div className="text-[12px] text-[#8A94A6]">{ev.actor}</div>
            {ev.note && <div className="mt-1 text-[12px] text-[#B0BAC8] italic">&ldquo;{ev.note}&rdquo;</div>}
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Defect Detail Drawer ─────────────────────────────────────────────────────

function DefectDrawer({ defect, onClose, onStatusUpdate }: {
  defect: Defect;
  onClose: () => void;
  onStatusUpdate: (id: string, to: DefectStatus, note: string) => void;
}) {
  const [showTransition, setShowTransition] = useState(false);
  const isCritical = defect.severity === "Critical";

  const nextStatuses: DefectStatus[] = (["Reported", "In Progress", "Fixed", "Verified"] as DefectStatus[])
    .filter(s => s !== defect.status);

  return (
    <>
      <Overlay onClick={onClose} />
      <div className="fixed right-0 top-0 bottom-0 w-full max-w-[520px] bg-[#161D26] border-l border-white/10 z-50 flex flex-col shadow-2xl">
        {isCritical && (
          <div className="bg-[#E5484D]/10 border-b border-[#E5484D]/30 px-5 py-2.5 flex items-center gap-2">
            <AlertTriangle size={14} className="text-[#E5484D]" />
            <span className="text-[12px] font-semibold text-[#E5484D] uppercase tracking-wider">Critical Severity — Priority Response Required</span>
          </div>
        )}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/8">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[12px] font-mono text-[#C8A24A]">{defect.id}</span>
              <SeverityPill severity={defect.severity} />
            </div>
            <h2 className="text-[16px] font-semibold text-[#E6EAF0]">{defect.defectType}</h2>
          </div>
          <button onClick={onClose} className="text-[#8A94A6] hover:text-[#E6EAF0] transition-colors p-1">
            <X size={20} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Drone", value: defect.drone },
              { label: "Serial", value: defect.droneSerial, mono: true },
              { label: "Reporter", value: defect.reporter },
              { label: "Detected", value: defect.detectedAt, mono: true },
            ].map(({ label, value, mono }) => (
              <div key={label} className="bg-[#0E1419] rounded-lg px-3 py-2.5">
                <div className="text-[10px] uppercase tracking-widest text-[#8A94A6] font-semibold mb-1">{label}</div>
                <div className={`text-[13px] text-[#E6EAF0] ${mono ? "font-mono" : ""}`}>{value}</div>
              </div>
            ))}
          </div>
          <div>
            <Label>Current Status</Label>
            <DefectStatusPill status={defect.status} />
          </div>
          <div>
            <Label>Description</Label>
            <p className="text-[13px] text-[#B0BAC8] leading-relaxed">{defect.description}</p>
          </div>
          <div className="border-t border-white/8 pt-4">
            <Label>Update Status</Label>
            <button
              onClick={() => setShowTransition(true)}
              className="inline-flex items-center gap-2 border border-[#C8A24A]/40 text-[#C8A24A] hover:bg-[#C8A24A]/10 px-4 py-2 rounded-lg text-[13px] font-medium transition-all"
            >
              <RefreshCw size={13} />
              Transition Status
            </button>
          </div>
          <div className="border-t border-white/8 pt-4">
            <Label>Event History</Label>
            <EventTimeline events={defect.history} />
          </div>
        </div>
      </div>
      {showTransition && (
        <StatusTransitionModal
          title={`Update Status — ${defect.id}`}
          currentStatus={defect.status}
          options={nextStatuses}
          onConfirm={(to, note) => {
            onStatusUpdate(defect.id, to as DefectStatus, note);
            setShowTransition(false);
          }}
          onClose={() => setShowTransition(false)}
        />
      )}
    </>
  );
}

// ─── Report Defect Form ───────────────────────────────────────────────────────

function ReportDefectModal({ onClose, onSubmit }: {
  onClose: () => void;
  onSubmit: (data: Partial<Defect>) => void;
}) {
  const [form, setForm] = useState({
    drone: DRONES[0], droneSerial: "", defectType: "", severity: "Medium" as Severity,
    description: "", reporter: TECHNICIANS[0]
  });

  return (
    <>
      <Overlay onClick={onClose} />
      <div className="fixed inset-0 flex items-center justify-center z-50 pointer-events-none">
        <div className="bg-[#161D26] border border-white/10 rounded-xl shadow-2xl w-full max-w-lg pointer-events-auto mx-4 max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-5 border-b border-white/8 sticky top-0 bg-[#161D26] z-10">
            <h3 className="text-[15px] font-semibold text-[#E6EAF0]">Report Defect</h3>
            <button onClick={onClose} className="text-[#8A94A6] hover:text-[#E6EAF0] transition-colors"><X size={18} /></button>
          </div>
          <div className="p-5 space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Drone</Label>
                <Select value={form.drone} onChange={e => setForm(f => ({ ...f, drone: e.target.value }))} className="w-full">
                  {DRONES.map(d => <option key={d}>{d}</option>)}
                </Select>
              </div>
              <div>
                <Label>Severity</Label>
                <Select value={form.severity} onChange={e => setForm(f => ({ ...f, severity: e.target.value as Severity }))} className="w-full">
                  {(["Low", "Medium", "High", "Critical"] as Severity[]).map(s => <option key={s}>{s}</option>)}
                </Select>
              </div>
            </div>
            <div>
              <Label>Defect Type</Label>
              <Input value={form.defectType} onChange={e => setForm(f => ({ ...f, defectType: e.target.value }))} placeholder="e.g. Motor Failure, GPS Drift, Frame Damage..." className="w-full" />
            </div>
            <div>
              <Label>Reporter</Label>
              <Select value={form.reporter} onChange={e => setForm(f => ({ ...f, reporter: e.target.value }))} className="w-full">
                {TECHNICIANS.map(t => <option key={t}>{t}</option>)}
              </Select>
            </div>
            <div>
              <Label>Description</Label>
              <Textarea
                rows={4}
                value={form.description}
                onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                placeholder="Describe the defect in detail — conditions observed, flight data, symptoms..."
                className="w-full"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 p-5 border-t border-white/8">
            <GhostButton onClick={onClose}>Cancel</GhostButton>
            <PrimaryButton onClick={() => { onSubmit(form); onClose(); }}>
              <Plus size={14} />
              Submit Defect
            </PrimaryButton>
          </div>
        </div>
      </div>
    </>
  );
}

// ─── New Order Form ───────────────────────────────────────────────────────────

function NewOrderModal({ defects, onClose, onSubmit }: {
  defects: Defect[];
  onClose: () => void;
  onSubmit: (data: Partial<RepairOrder>) => void;
}) {
  const [form, setForm] = useState({
    drone: DRONES[0], defectId: defects[0]?.id ?? "", assignedTo: TECHNICIANS[0], notes: ""
  });

  return (
    <>
      <Overlay onClick={onClose} />
      <div className="fixed inset-0 flex items-center justify-center z-50 pointer-events-none">
        <div className="bg-[#161D26] border border-white/10 rounded-xl shadow-2xl w-full max-w-md pointer-events-auto mx-4">
          <div className="flex items-center justify-between p-5 border-b border-white/8">
            <h3 className="text-[15px] font-semibold text-[#E6EAF0]">New Repair Order</h3>
            <button onClick={onClose} className="text-[#8A94A6] hover:text-[#E6EAF0] transition-colors"><X size={18} /></button>
          </div>
          <div className="p-5 space-y-4">
            <div>
              <Label>Drone</Label>
              <Select value={form.drone} onChange={e => setForm(f => ({ ...f, drone: e.target.value }))} className="w-full">
                {DRONES.map(d => <option key={d}>{d}</option>)}
              </Select>
            </div>
            <div>
              <Label>Linked Defect</Label>
              <Select value={form.defectId} onChange={e => setForm(f => ({ ...f, defectId: e.target.value }))} className="w-full">
                {defects.map(d => <option key={d.id} value={d.id}>{d.id} — {d.defectType}</option>)}
              </Select>
            </div>
            <div>
              <Label>Assign To</Label>
              <Select value={form.assignedTo} onChange={e => setForm(f => ({ ...f, assignedTo: e.target.value }))} className="w-full">
                {TECHNICIANS.map(t => <option key={t}>{t}</option>)}
              </Select>
            </div>
            <div>
              <Label>Notes</Label>
              <Textarea rows={3} value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} placeholder="Work scope, parts needed, constraints..." className="w-full" />
            </div>
          </div>
          <div className="flex justify-end gap-2 p-5 border-t border-white/8">
            <GhostButton onClick={onClose}>Cancel</GhostButton>
            <PrimaryButton onClick={() => { onSubmit(form); onClose(); }}>
              <Plus size={14} />
              Create Order
            </PrimaryButton>
          </div>
        </div>
      </div>
    </>
  );
}

// ─── Order Detail Drawer ──────────────────────────────────────────────────────

function OrderDrawer({ order, defects, replacements, onClose, onStatusUpdate }: {
  order: RepairOrder;
  defects: Defect[];
  replacements: ComponentReplacement[];
  onClose: () => void;
  onStatusUpdate: (id: string, to: OrderStatus, note: string) => void;
}) {
  const [showTransition, setShowTransition] = useState(false);
  const linkedDefect = defects.find(d => d.id === order.defectId);
  const orderReplacements = replacements.filter(r => r.orderId === order.id);
  const nextStatuses = (["Pending", "In Progress", "Completed", "Cancelled"] as OrderStatus[]).filter(s => s !== order.status);

  return (
    <>
      <Overlay onClick={onClose} />
      <div className="fixed right-0 top-0 bottom-0 w-full max-w-[520px] bg-[#161D26] border-l border-white/10 z-50 flex flex-col shadow-2xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/8">
          <div>
            <div className="text-[12px] font-mono text-[#C8A24A] mb-1">{order.id}</div>
            <h2 className="text-[16px] font-semibold text-[#E6EAF0]">{order.drone} Repair Order</h2>
          </div>
          <button onClick={onClose} className="text-[#8A94A6] hover:text-[#E6EAF0] transition-colors p-1"><X size={20} /></button>
        </div>
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Drone Serial", value: order.droneSerial, mono: true },
              { label: "Assigned To", value: order.assignedTo },
              { label: "Created", value: order.createdAt, mono: true },
              { label: "Last Updated", value: order.updatedAt, mono: true },
            ].map(({ label, value, mono }) => (
              <div key={label} className="bg-[#0E1419] rounded-lg px-3 py-2.5">
                <div className="text-[10px] uppercase tracking-widest text-[#8A94A6] font-semibold mb-1">{label}</div>
                <div className={`text-[13px] text-[#E6EAF0] ${mono ? "font-mono" : ""}`}>{value}</div>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <div>
              <Label>Status</Label>
              <OrderStatusPill status={order.status} />
            </div>
          </div>
          {linkedDefect && (
            <div className="border border-white/8 rounded-lg p-4 bg-[#0E1419]">
              <Label>Linked Defect</Label>
              <div className="flex items-center gap-3 mt-2">
                <span className="font-mono text-[13px] text-[#C8A24A]">{linkedDefect.id}</span>
                <SeverityPill severity={linkedDefect.severity} />
                <DefectStatusPill status={linkedDefect.status} />
              </div>
              <div className="text-[13px] text-[#E6EAF0] mt-2">{linkedDefect.defectType}</div>
            </div>
          )}
          {order.notes && (
            <div>
              <Label>Notes</Label>
              <p className="text-[13px] text-[#B0BAC8] leading-relaxed">{order.notes}</p>
            </div>
          )}
          <div className="border-t border-white/8 pt-4">
            <Label>Update Status</Label>
            <button
              onClick={() => setShowTransition(true)}
              className="inline-flex items-center gap-2 border border-[#C8A24A]/40 text-[#C8A24A] hover:bg-[#C8A24A]/10 px-4 py-2 rounded-lg text-[13px] font-medium transition-all"
            >
              <RefreshCw size={13} />
              Transition Status
            </button>
          </div>
          <div className="border-t border-white/8 pt-4">
            <Label>Component Replacements ({orderReplacements.length})</Label>
            {orderReplacements.length === 0 ? (
              <div className="text-[13px] text-[#8A94A6] py-2">No replacements logged for this order.</div>
            ) : (
              <div className="space-y-2">
                {orderReplacements.map(r => (
                  <div key={r.id} className="bg-[#0E1419] rounded-lg p-3 border border-white/6">
                    <div className="text-[12px] font-semibold text-[#E6EAF0] mb-1">{r.componentType}</div>
                    <div className="flex items-center gap-2 text-[11px] font-mono">
                      <span className="text-[#8A94A6]">{r.oldSerial}</span>
                      <ArrowRight size={10} className="text-[#8A94A6]" />
                      <span className="text-[#C8A24A]">{r.newSerial}</span>
                    </div>
                    <div className="text-[11px] text-[#8A94A6] mt-1">{r.replacedBy} · {r.replacedAt}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
      {showTransition && (
        <StatusTransitionModal
          title={`Update Order — ${order.id}`}
          currentStatus={order.status}
          options={nextStatuses}
          onConfirm={(to, note) => {
            onStatusUpdate(order.id, to as OrderStatus, note);
            setShowTransition(false);
          }}
          onClose={() => setShowTransition(false)}
        />
      )}
    </>
  );
}

// ─── Log Replacement Form ─────────────────────────────────────────────────────

function LogReplacementModal({ orders, onClose, onSubmit }: {
  orders: RepairOrder[];
  onClose: () => void;
  onSubmit: (data: Partial<ComponentReplacement>) => void;
}) {
  const [form, setForm] = useState({
    drone: DRONES[0], componentType: "", oldSerial: "", newSerial: "",
    reason: "", replacedBy: TECHNICIANS[0], orderId: ""
  });

  return (
    <>
      <Overlay onClick={onClose} />
      <div className="fixed inset-0 flex items-center justify-center z-50 pointer-events-none">
        <div className="bg-[#161D26] border border-white/10 rounded-xl shadow-2xl w-full max-w-lg pointer-events-auto mx-4 max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-5 border-b border-white/8 sticky top-0 bg-[#161D26]">
            <h3 className="text-[15px] font-semibold text-[#E6EAF0]">Log Component Replacement</h3>
            <button onClick={onClose} className="text-[#8A94A6] hover:text-[#E6EAF0] transition-colors"><X size={18} /></button>
          </div>
          <div className="p-5 space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Drone</Label>
                <Select value={form.drone} onChange={e => setForm(f => ({ ...f, drone: e.target.value }))} className="w-full">
                  {DRONES.map(d => <option key={d}>{d}</option>)}
                </Select>
              </div>
              <div>
                <Label>Linked Repair Order</Label>
                <Select value={form.orderId} onChange={e => setForm(f => ({ ...f, orderId: e.target.value }))} className="w-full">
                  <option value="">— None —</option>
                  {orders.map(o => <option key={o.id} value={o.id}>{o.id}</option>)}
                </Select>
              </div>
            </div>
            <div>
              <Label>Component Type</Label>
              <Input value={form.componentType} onChange={e => setForm(f => ({ ...f, componentType: e.target.value }))} placeholder="e.g. Motor Controller Board, LiPo Battery Pack..." className="w-full" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Old Serial</Label>
                <Input value={form.oldSerial} onChange={e => setForm(f => ({ ...f, oldSerial: e.target.value }))} placeholder="MCB-XXXX-X" className="w-full font-mono" />
              </div>
              <div>
                <Label>New Serial</Label>
                <Input value={form.newSerial} onChange={e => setForm(f => ({ ...f, newSerial: e.target.value }))} placeholder="MCB-XXXX-X" className="w-full font-mono" />
              </div>
            </div>
            <div>
              <Label>Replaced By</Label>
              <Select value={form.replacedBy} onChange={e => setForm(f => ({ ...f, replacedBy: e.target.value }))} className="w-full">
                {TECHNICIANS.map(t => <option key={t}>{t}</option>)}
              </Select>
            </div>
            <div>
              <Label>Reason</Label>
              <Textarea rows={2} value={form.reason} onChange={e => setForm(f => ({ ...f, reason: e.target.value }))} placeholder="Failure mode, condition, justification..." className="w-full" />
            </div>
          </div>
          <div className="flex justify-end gap-2 p-5 border-t border-white/8">
            <GhostButton onClick={onClose}>Cancel</GhostButton>
            <PrimaryButton onClick={() => { onSubmit(form); onClose(); }}>
              <Plus size={14} />
              Log Replacement
            </PrimaryButton>
          </div>
        </div>
      </div>
    </>
  );
}

// ─── Tab: Defects ─────────────────────────────────────────────────────────────

function DefectsTab() {
  const [defects, setDefects] = useState<Defect[]>(DEFECTS);
  const [search, setSearch] = useState("");
  const [filterSeverity, setFilterSeverity] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterDrone, setFilterDrone] = useState("");
  const [selectedRow, setSelectedRow] = useState<Defect | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [sortField, setSortField] = useState<string>("detectedAt");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const chips: { label: string; clear: () => void }[] = [
    ...(filterSeverity ? [{ label: `Severity: ${filterSeverity}`, clear: () => setFilterSeverity("") }] : []),
    ...(filterStatus ? [{ label: `Status: ${filterStatus}`, clear: () => setFilterStatus("") }] : []),
    ...(filterDrone ? [{ label: `Drone: ${filterDrone}`, clear: () => setFilterDrone("") }] : []),
  ];

  const filtered = defects
    .filter(d => !search || d.id.includes(search) || d.drone.toLowerCase().includes(search.toLowerCase()) || d.defectType.toLowerCase().includes(search.toLowerCase()))
    .filter(d => !filterSeverity || d.severity === filterSeverity)
    .filter(d => !filterStatus || d.status === filterStatus)
    .filter(d => !filterDrone || d.drone === filterDrone)
    .sort((a, b) => {
      const mul = sortDir === "asc" ? 1 : -1;
      return a[sortField as keyof Defect] > b[sortField as keyof Defect] ? mul : -mul;
    });

  const toggleSort = (field: string) => {
    if (sortField === field) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortField(field); setSortDir("desc"); }
  };

  const SortIcon = ({ field }: { field: string }) => {
    if (sortField !== field) return <ChevronDown size={11} className="text-[#8A94A6]/40" />;
    return sortDir === "asc" ? <ChevronUp size={11} className="text-[#C8A24A]" /> : <ChevronDown size={11} className="text-[#C8A24A]" />;
  };

  const handleStatusUpdate = (id: string, to: DefectStatus, note: string) => {
    setDefects(prev => prev.map(d => {
      if (d.id !== id) return d;
      const ev: HistoryEvent = {
        id: `h${Date.now()}`, timestamp: new Date().toISOString().slice(0, 16).replace("T", " "),
        actor: "Current User", from: d.status, to, note
      };
      return { ...d, status: to, history: [...d.history, ev] };
    }));
    if (selectedRow?.id === id) {
      setSelectedRow(prev => {
        if (!prev) return null;
        const ev: HistoryEvent = {
          id: `h${Date.now()}`, timestamp: new Date().toISOString().slice(0, 16).replace("T", " "),
          actor: "Current User", from: prev.status, to, note
        };
        return { ...prev, status: to, history: [...prev.history, ev] };
      });
    }
  };

  const handleNewDefect = (data: Partial<Defect>) => {
    const id = `DEF-${2250 + Math.floor(Math.random() * 100)}`;
    setDefects(prev => [{
      id, drone: data.drone!, droneSerial: `DRN-00XX-${data.drone?.slice(0, 2).toUpperCase()}`,
      defectType: data.defectType!, severity: data.severity!, status: "Reported",
      detectedAt: new Date().toISOString().slice(0, 16).replace("T", " "),
      reporter: data.reporter!, description: data.description!,
      history: [{ id: "h1", timestamp: new Date().toISOString().slice(0, 16).replace("T", " "), actor: data.reporter!, from: "", to: "Reported", note: "" }]
    }, ...prev]);
  };

  const colH = "text-[11px] uppercase tracking-widest font-semibold text-[#8A94A6] select-none cursor-pointer hover:text-[#E6EAF0] transition-colors";

  return (
    <div className="flex flex-col gap-4">
      {/* Filter bar */}
      <div className="flex items-center gap-2 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-[300px]">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8A94A6]" />
          <Input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search defect ID, drone, type..." className="w-full pl-8" />
        </div>
        <div className="relative">
          <Select value={filterSeverity} onChange={e => setFilterSeverity(e.target.value)} className="pr-8">
            <option value="">All Severities</option>
            {(["Low", "Medium", "High", "Critical"] as Severity[]).map(s => <option key={s}>{s}</option>)}
          </Select>
        </div>
        <div className="relative">
          <Select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="pr-8">
            <option value="">All Statuses</option>
            {(["Reported", "In Progress", "Fixed", "Verified"] as DefectStatus[]).map(s => <option key={s}>{s}</option>)}
          </Select>
        </div>
        <div className="relative">
          <Select value={filterDrone} onChange={e => setFilterDrone(e.target.value)} className="pr-8">
            <option value="">All Drones</option>
            {DRONES.map(d => <option key={d}>{d}</option>)}
          </Select>
        </div>
        <div className="ml-auto">
          <PrimaryButton onClick={() => setShowForm(true)}>
            <Plus size={14} />
            Report Defect
          </PrimaryButton>
        </div>
      </div>

      {/* Filter chips */}
      {chips.length > 0 && (
        <div className="flex items-center gap-2">
          <Filter size={12} className="text-[#8A94A6]" />
          {chips.map(c => <FilterChip key={c.label} label={c.label} onRemove={c.clear} />)}
          <button onClick={() => { setFilterSeverity(""); setFilterStatus(""); setFilterDrone(""); }} className="text-[12px] text-[#8A94A6] hover:text-[#E6EAF0] ml-1 transition-colors">
            Clear all
          </button>
        </div>
      )}

      {/* Table */}
      <div className="bg-[#161D26] border border-white/8 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-white/8 bg-[#0E1419]">
                {[
                  { key: "drone", label: "Drone" },
                  { key: "defectType", label: "Defect Type" },
                  { key: "severity", label: "Severity" },
                  { key: "status", label: "Status" },
                  { key: "detectedAt", label: "Detected At" },
                  { key: "reporter", label: "Reporter" },
                  { key: "", label: "" },
                ].map(({ key, label }) => (
                  <th key={label} onClick={() => key && toggleSort(key)}
                    className={`text-left px-4 py-3 ${key ? colH : ""} whitespace-nowrap`}
                  >
                    <span className="inline-flex items-center gap-1">
                      {label}
                      {key && <SortIcon field={key} />}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-16 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <Wrench size={28} className="text-[#8A94A6]/40" />
                      <div className="text-[13px] text-[#8A94A6]">No defects match the current filters</div>
                    </div>
                  </td>
                </tr>
              ) : (
                filtered.map(d => (
                  <tr
                    key={d.id}
                    onClick={() => setSelectedRow(d)}
                    className={`border-b border-white/5 cursor-pointer transition-colors group
                      ${d.severity === "Critical" ? "hover:bg-[#E5484D]/5" : "hover:bg-white/[0.03]"}
                      ${selectedRow?.id === d.id ? "bg-[#C8A24A]/5" : ""}`}
                  >
                    <td className="px-4 py-3">
                      <div className="text-[13px] font-medium text-[#E6EAF0]">{d.drone}</div>
                      <div className="text-[11px] font-mono text-[#8A94A6]">{d.droneSerial}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-[13px] text-[#E6EAF0]">{d.defectType}</div>
                      <div className="text-[11px] font-mono text-[#8A94A6]">{d.id}</div>
                    </td>
                    <td className="px-4 py-3"><SeverityPill severity={d.severity} /></td>
                    <td className="px-4 py-3"><DefectStatusPill status={d.status} /></td>
                    <td className="px-4 py-3 font-mono text-[12px] text-[#8A94A6]">{d.detectedAt}</td>
                    <td className="px-4 py-3 text-[13px] text-[#8A94A6]">{d.reporter}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={e => { e.stopPropagation(); setSelectedRow(d); }}
                        className="text-[#8A94A6] hover:text-[#C8A24A] transition-colors opacity-0 group-hover:opacity-100"
                      >
                        <ChevronRight size={16} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="px-4 py-2.5 border-t border-white/5 flex items-center justify-between">
          <span className="text-[12px] text-[#8A94A6]">{filtered.length} defect{filtered.length !== 1 ? "s" : ""}</span>
          <span className="text-[11px] text-[#8A94A6]/60 font-mono">DEFECTS / {new Date().toISOString().slice(0, 10)}</span>
        </div>
      </div>

      {selectedRow && (
        <DefectDrawer
          defect={selectedRow}
          onClose={() => setSelectedRow(null)}
          onStatusUpdate={handleStatusUpdate}
        />
      )}
      {showForm && <ReportDefectModal onClose={() => setShowForm(false)} onSubmit={handleNewDefect} />}
    </div>
  );
}

// ─── Tab: Repair Orders ───────────────────────────────────────────────────────

function RepairOrdersTab({ defects }: { defects: Defect[] }) {
  const [orders, setOrders] = useState<RepairOrder[]>(ORDERS);
  const [filterStatus, setFilterStatus] = useState("");
  const [filterAssigned, setFilterAssigned] = useState("");
  const [filterDrone, setFilterDrone] = useState("");
  const [selectedOrder, setSelectedOrder] = useState<RepairOrder | null>(null);
  const [showForm, setShowForm] = useState(false);

  const chips = [
    ...(filterStatus ? [{ label: `Status: ${filterStatus}`, clear: () => setFilterStatus("") }] : []),
    ...(filterAssigned ? [{ label: `Assigned: ${filterAssigned}`, clear: () => setFilterAssigned("") }] : []),
    ...(filterDrone ? [{ label: `Drone: ${filterDrone}`, clear: () => setFilterDrone("") }] : []),
  ];

  const filtered = orders
    .filter(o => !filterStatus || o.status === filterStatus)
    .filter(o => !filterAssigned || o.assignedTo === filterAssigned)
    .filter(o => !filterDrone || o.drone === filterDrone)
    .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));

  const handleStatusUpdate = (id: string, to: OrderStatus, _note: string) => {
    setOrders(prev => prev.map(o => o.id === id ? { ...o, status: to, updatedAt: new Date().toISOString().slice(0, 16).replace("T", " ") } : o));
    setSelectedOrder(prev => prev && prev.id === id ? { ...prev, status: to, updatedAt: new Date().toISOString().slice(0, 16).replace("T", " ") } : prev);
  };

  const handleNewOrder = (data: Partial<RepairOrder>) => {
    const id = `RO-${910 + Math.floor(Math.random() * 10)}`;
    const now = new Date().toISOString().slice(0, 16).replace("T", " ");
    setOrders(prev => [{
      id, drone: data.drone!, droneSerial: `DRN-00XX-${data.drone?.slice(0, 2).toUpperCase()}`,
      defectId: data.defectId ?? "", status: "Pending", assignedTo: data.assignedTo!,
      createdAt: now, updatedAt: now, notes: data.notes ?? ""
    }, ...prev]);
  };

  const colH = "text-[11px] uppercase tracking-widest font-semibold text-[#8A94A6] select-none cursor-pointer hover:text-[#E6EAF0] transition-colors whitespace-nowrap";

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 flex-wrap">
        <Select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
          <option value="">All Statuses</option>
          {(["Pending", "In Progress", "Completed", "Cancelled"] as OrderStatus[]).map(s => <option key={s}>{s}</option>)}
        </Select>
        <Select value={filterAssigned} onChange={e => setFilterAssigned(e.target.value)}>
          <option value="">All Technicians</option>
          {TECHNICIANS.map(t => <option key={t}>{t}</option>)}
        </Select>
        <Select value={filterDrone} onChange={e => setFilterDrone(e.target.value)}>
          <option value="">All Drones</option>
          {DRONES.map(d => <option key={d}>{d}</option>)}
        </Select>
        <div className="ml-auto">
          <PrimaryButton onClick={() => setShowForm(true)}>
            <Plus size={14} />
            New Order
          </PrimaryButton>
        </div>
      </div>

      {chips.length > 0 && (
        <div className="flex items-center gap-2">
          <Filter size={12} className="text-[#8A94A6]" />
          {chips.map(c => <FilterChip key={c.label} label={c.label} onRemove={c.clear} />)}
        </div>
      )}

      <div className="bg-[#161D26] border border-white/8 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-white/8 bg-[#0E1419]">
                {["Order ID", "Drone", "Linked Defect", "Status", "Assigned To", "Created", "Updated", ""].map(label => (
                  <th key={label} className={`text-left px-4 py-3 ${label ? colH : ""}`}>{label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-16 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <FileText size={28} className="text-[#8A94A6]/40" />
                      <div className="text-[13px] text-[#8A94A6]">No repair orders found</div>
                    </div>
                  </td>
                </tr>
              ) : (
                filtered.map(o => (
                  <tr
                    key={o.id}
                    onClick={() => setSelectedOrder(o)}
                    className={`border-b border-white/5 cursor-pointer transition-colors group hover:bg-white/[0.03] ${selectedOrder?.id === o.id ? "bg-[#C8A24A]/5" : ""}`}
                  >
                    <td className="px-4 py-3 font-mono text-[13px] text-[#C8A24A]">{o.id}</td>
                    <td className="px-4 py-3">
                      <div className="text-[13px] font-medium text-[#E6EAF0]">{o.drone}</div>
                      <div className="text-[11px] font-mono text-[#8A94A6]">{o.droneSerial}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-mono text-[12px] text-[#8A94A6] hover:text-[#C8A24A] transition-colors">{o.defectId || "—"}</span>
                    </td>
                    <td className="px-4 py-3"><OrderStatusPill status={o.status} /></td>
                    <td className="px-4 py-3 text-[13px] text-[#8A94A6]">{o.assignedTo}</td>
                    <td className="px-4 py-3 font-mono text-[12px] text-[#8A94A6]">{o.createdAt}</td>
                    <td className="px-4 py-3 font-mono text-[12px] text-[#8A94A6]">{o.updatedAt}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={e => { e.stopPropagation(); setSelectedOrder(o); }}
                        className="text-[#8A94A6] hover:text-[#C8A24A] transition-colors opacity-0 group-hover:opacity-100"
                      >
                        <ChevronRight size={16} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="px-4 py-2.5 border-t border-white/5 flex items-center justify-between">
          <span className="text-[12px] text-[#8A94A6]">{filtered.length} order{filtered.length !== 1 ? "s" : ""}</span>
          <span className="text-[11px] text-[#8A94A6]/60 font-mono">ORDERS / {new Date().toISOString().slice(0, 10)}</span>
        </div>
      </div>

      {selectedOrder && (
        <OrderDrawer
          order={selectedOrder}
          defects={defects}
          replacements={[...REPLACEMENTS, ...(ORDER_REPLACEMENTS[selectedOrder.id] ?? [])]}
          onClose={() => setSelectedOrder(null)}
          onStatusUpdate={handleStatusUpdate}
        />
      )}
      {showForm && <NewOrderModal defects={defects} onClose={() => setShowForm(false)} onSubmit={handleNewOrder} />}
    </div>
  );
}

// ─── Tab: Component Replacements ──────────────────────────────────────────────

function ComponentReplacementsTab({ orders }: { orders: RepairOrder[] }) {
  const [replacements, setReplacements] = useState<ComponentReplacement[]>(REPLACEMENTS);
  const [showForm, setShowForm] = useState(false);
  const [exporting, setExporting] = useState(false);

  const handleExport = () => {
    setExporting(true);
    setTimeout(() => {
      const header = "ID,Drone,Serial,Component,Old Serial,New Serial,Reason,Replaced At,Replaced By,Order ID";
      const rows = replacements.map(r =>
        [r.id, r.drone, r.droneSerial, r.componentType, r.oldSerial, r.newSerial, `"${r.reason}"`, r.replacedAt, r.replacedBy, r.orderId ?? ""].join(",")
      );
      const csv = [header, ...rows].join("\n");
      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `component-replacements-${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      setExporting(false);
    }, 800);
  };

  const handleLog = (data: Partial<ComponentReplacement>) => {
    const id = `CR-${560 + Math.floor(Math.random() * 10)}`;
    const now = new Date().toISOString().slice(0, 16).replace("T", " ");
    setReplacements(prev => [{
      id, drone: data.drone!, droneSerial: `DRN-00XX-${data.drone?.slice(0, 2).toUpperCase()}`,
      componentType: data.componentType!, oldSerial: data.oldSerial!, newSerial: data.newSerial!,
      reason: data.reason!, replacedAt: now, replacedBy: data.replacedBy!, orderId: data.orderId || undefined
    }, ...prev]);
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 flex-wrap">
        <div className="ml-auto flex items-center gap-2">
          <GhostButton onClick={handleExport} className={exporting ? "opacity-70" : ""}>
            {exporting ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
            Export CSV
          </GhostButton>
          <PrimaryButton onClick={() => setShowForm(true)}>
            <Plus size={14} />
            Log Replacement
          </PrimaryButton>
        </div>
      </div>

      <div className="bg-[#161D26] border border-white/8 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-white/8 bg-[#0E1419]">
                {["Drone", "Component Type", "Serial Change", "Reason", "Replaced At", "Replaced By", "Order"].map(label => (
                  <th key={label} className="text-left px-4 py-3 text-[11px] uppercase tracking-widest font-semibold text-[#8A94A6] whitespace-nowrap">{label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {replacements.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-16 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <Cpu size={28} className="text-[#8A94A6]/40" />
                      <div className="text-[13px] text-[#8A94A6]">No component replacements logged</div>
                    </div>
                  </td>
                </tr>
              ) : (
                replacements.map(r => (
                  <tr key={r.id} className="border-b border-white/5 hover:bg-white/[0.03] transition-colors group">
                    <td className="px-4 py-3">
                      <div className="text-[13px] font-medium text-[#E6EAF0]">{r.drone}</div>
                      <div className="text-[11px] font-mono text-[#8A94A6]">{r.droneSerial}</div>
                    </td>
                    <td className="px-4 py-3 text-[13px] text-[#E6EAF0]">{r.componentType}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 font-mono text-[12px]">
                        <span className="text-[#8A94A6] line-through decoration-[#8A94A6]/40">{r.oldSerial}</span>
                        <ArrowRight size={11} className="text-[#8A94A6] flex-shrink-0" />
                        <span className="text-[#C8A24A]">{r.newSerial}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-[13px] text-[#8A94A6] max-w-[200px]">
                      <span className="truncate block">{r.reason}</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-[12px] text-[#8A94A6]">{r.replacedAt}</td>
                    <td className="px-4 py-3 text-[13px] text-[#8A94A6]">{r.replacedBy}</td>
                    <td className="px-4 py-3">
                      {r.orderId ? (
                        <span className="font-mono text-[12px] text-[#C8A24A]/80">{r.orderId}</span>
                      ) : (
                        <span className="text-[12px] text-[#8A94A6]/40">—</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="px-4 py-2.5 border-t border-white/5 flex items-center justify-between">
          <span className="text-[12px] text-[#8A94A6]">{replacements.length} replacement{replacements.length !== 1 ? "s" : ""}</span>
          <span className="text-[11px] text-[#8A94A6]/60 font-mono">REPLACEMENTS / {new Date().toISOString().slice(0, 10)}</span>
        </div>
      </div>

      {showForm && <LogReplacementModal orders={orders} onClose={() => setShowForm(false)} onSubmit={handleLog} />}
    </div>
  );
}

// ─── App Shell ────────────────────────────────────────────────────────────────

const NAV_ITEMS = [
  { icon: LayoutDashboard, label: "Dashboard", active: false },
  { icon: Radio, label: "Fleet Status", active: false },
  { icon: Wrench, label: "Maintenance", active: true },
  { icon: FileText, label: "Mission Logs", active: false },
  { icon: Shield, label: "Compliance", active: false },
  { icon: Users, label: "Personnel", active: false },
  { icon: Settings, label: "System", active: false },
];

const TABS = ["Defects", "Repair Orders", "Component Replacements"];

export default function App() {
  const [activeTab, setActiveTab] = useState(0);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="flex h-screen bg-[#0B0F14] text-[#E6EAF0] overflow-hidden" style={{ fontFamily: "'Inter', sans-serif" }}>
      {/* Sidebar */}
      <aside
        className={`flex flex-col flex-shrink-0 bg-[#0E1419] border-r border-white/6 transition-all duration-200 ${sidebarCollapsed ? "w-14" : "w-56"}`}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-4 border-b border-white/6">
          <div className="w-7 h-7 rounded-lg bg-[#C8A24A] flex items-center justify-center flex-shrink-0">
            <Radio size={14} className="text-[#0B0F14]" />
          </div>
          {!sidebarCollapsed && (
            <div>
              <div className="text-[13px] font-bold text-[#E6EAF0] leading-none tracking-wide">MISSION</div>
              <div className="text-[10px] font-semibold text-[#C8A24A] tracking-widest leading-none mt-0.5">CONTROL</div>
            </div>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-3 space-y-0.5">
          {NAV_ITEMS.map(({ icon: Icon, label, active }) => (
            <button
              key={label}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 transition-all group relative
                ${active
                  ? "bg-[#C8A24A]/10 text-[#C8A24A]"
                  : "text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/[0.04]"
                }`}
            >
              {active && <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-[#C8A24A] rounded-r" />}
              <Icon size={16} className="flex-shrink-0" />
              {!sidebarCollapsed && <span className="text-[13px] font-medium">{label}</span>}
            </button>
          ))}
        </nav>

        {/* Bottom */}
        <div className="border-t border-white/6 p-3 space-y-0.5">
          <button className="w-full flex items-center gap-3 px-2.5 py-2 text-[#8A94A6] hover:text-[#E6EAF0] transition-colors">
            <Bell size={15} />
            {!sidebarCollapsed && <span className="text-[13px]">Alerts</span>}
          </button>
          <button className="w-full flex items-center gap-3 px-2.5 py-2 text-[#8A94A6] hover:text-[#E6EAF0] transition-colors">
            <HelpCircle size={15} />
            {!sidebarCollapsed && <span className="text-[13px]">Help</span>}
          </button>
          {/* User */}
          <div className={`flex items-center gap-2.5 px-2.5 py-2 mt-2 border-t border-white/6 pt-3 ${sidebarCollapsed ? "justify-center" : ""}`}>
            <div className="w-7 h-7 rounded-full bg-[#C8A24A]/20 border border-[#C8A24A]/30 flex items-center justify-center flex-shrink-0">
              <span className="text-[11px] font-bold text-[#C8A24A]">MV</span>
            </div>
            {!sidebarCollapsed && (
              <div className="min-w-0">
                <div className="text-[12px] font-semibold text-[#E6EAF0] truncate">M. Vasquez</div>
                <div className="text-[10px] text-[#8A94A6]">Technician</div>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex items-center justify-between px-6 py-3 border-b border-white/6 bg-[#0E1419] flex-shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarCollapsed(c => !c)}
              className="text-[#8A94A6] hover:text-[#E6EAF0] transition-colors"
            >
              <MoreHorizontal size={18} />
            </button>
            <div className="flex items-center gap-1.5 text-[12px] text-[#8A94A6]">
              <span>Fleet</span>
              <ChevronRight size={12} />
              <span className="text-[#E6EAF0]">Maintenance</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-[12px] font-mono text-[#8A94A6]">
              <Clock size={12} />
              <span className="text-[#C8A24A]">LIVE</span>
              <span>{new Date().toISOString().slice(0, 16).replace("T", " ")} UTC</span>
            </div>
            <div className="h-4 w-px bg-white/10" />
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-[#3FB950] animate-pulse" />
              <span className="text-[12px] text-[#8A94A6]">7 drones active</span>
            </div>
            <div className="h-4 w-px bg-white/10" />
            <button className="relative text-[#8A94A6] hover:text-[#E6EAF0] transition-colors">
              <Bell size={16} />
              <span className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-[#E5484D] text-[8px] font-bold text-white flex items-center justify-center">2</span>
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <div className="px-6 pt-5 pb-3">
            {/* Page header */}
            <div className="flex items-start justify-between mb-5">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Wrench size={18} className="text-[#C8A24A]" />
                  <h1 className="text-[22px] font-semibold text-[#E6EAF0] tracking-tight">Repairs &amp; Maintenance</h1>
                </div>
                <p className="text-[13px] text-[#8A94A6]">Defect tracking, repair orders, and component lifecycle management</p>
              </div>
              {/* Stat pills */}
              <div className="flex items-center gap-2 flex-wrap justify-end">
                {[
                  { label: "Open Defects", value: DEFECTS.filter(d => d.status !== "Verified").length, color: "#C8A24A" },
                  { label: "Critical", value: DEFECTS.filter(d => d.severity === "Critical").length, color: "#E5484D" },
                  { label: "Active Orders", value: ORDERS.filter(o => o.status === "In Progress").length, color: "#4C8DFF" },
                ].map(({ label, value, color }) => (
                  <div key={label} className="bg-[#161D26] border border-white/8 rounded-lg px-3 py-2 text-center min-w-[80px]">
                    <div className="text-[18px] font-bold" style={{ color }}>{value}</div>
                    <div className="text-[10px] uppercase tracking-wider text-[#8A94A6] font-semibold">{label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Tab bar */}
            <div className="flex items-end gap-0 border-b border-white/8 mb-5">
              {TABS.map((tab, i) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(i)}
                  className={`relative px-5 py-2.5 text-[13px] font-medium transition-all ${
                    activeTab === i
                      ? "text-[#C8A24A]"
                      : "text-[#8A94A6] hover:text-[#E6EAF0]"
                  }`}
                >
                  {tab}
                  {activeTab === i && (
                    <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#C8A24A] rounded-t" />
                  )}
                </button>
              ))}
            </div>

            {/* Tab content */}
            {activeTab === 0 && <DefectsTab />}
            {activeTab === 1 && <RepairOrdersTab defects={DEFECTS} />}
            {activeTab === 2 && <ComponentReplacementsTab orders={ORDERS} />}
          </div>
        </main>
      </div>
    </div>
  );
}
