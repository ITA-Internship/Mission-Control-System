import { useState } from "react";
import {
  LayoutDashboard, Plane, Crosshair, Building2, BarChart2, Settings,
  ChevronRight, MoreHorizontal, Edit2, AlertTriangle, X, ArrowRight,
  Bell, Search, Shield, History, FileText, Plus, Save, Clock, User,
  Check, ChevronDown, Activity, Cpu, Camera, Zap, SortAsc,
  LogOut, UserCircle, HelpCircle, Radio, ExternalLink, ArrowUpDown,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────
type DroneStatus =
  | "active" | "in_mission" | "maintenance" | "damaged"
  | "lost" | "decommissioned" | "sold" | "transferred" | "written_off";
type Classification = "unclassified" | "confidential" | "secret" | "top_secret";
type TabId = "specs" | "status_history" | "spec_changes" | "writeoffs";

// ─── Constants ────────────────────────────────────────────────────────────────
const STATUS_CFG: Record<DroneStatus, { label: string; color: string; bg: string }> = {
  active:        { label: "Active",          color: "#3FB950", bg: "rgba(63,185,80,0.10)" },
  in_mission:    { label: "In Mission",      color: "#4C8DFF", bg: "rgba(76,141,255,0.10)" },
  maintenance:   { label: "Maintenance",     color: "#C8A24A", bg: "rgba(200,162,74,0.10)" },
  damaged:       { label: "Damaged",         color: "#E5484D", bg: "rgba(229,72,77,0.10)" },
  lost:          { label: "Lost",            color: "#8A94A6", bg: "rgba(138,148,166,0.10)" },
  decommissioned:{ label: "Decommissioned",  color: "#8A94A6", bg: "rgba(138,148,166,0.10)" },
  sold:          { label: "Sold",            color: "#8A94A6", bg: "rgba(138,148,166,0.10)" },
  transferred:   { label: "Transferred",     color: "#8A94A6", bg: "rgba(138,148,166,0.10)" },
  written_off:   { label: "Written Off",     color: "#8A94A6", bg: "rgba(138,148,166,0.10)" },
};

const CLASS_CFG: Record<Classification, { label: string; color: string }> = {
  unclassified: { label: "UNCLASSIFIED", color: "#3FB950" },
  confidential: { label: "CONFIDENTIAL", color: "#4C8DFF" },
  secret:       { label: "SECRET",       color: "#C8A24A" },
  top_secret:   { label: "TOP SECRET",   color: "#E5484D" },
};

const TRANSITIONS: Record<DroneStatus, DroneStatus[]> = {
  active:        ["in_mission", "maintenance", "decommissioned"],
  in_mission:    ["active", "damaged", "lost"],
  maintenance:   ["active", "damaged", "decommissioned"],
  damaged:       ["maintenance", "written_off", "decommissioned"],
  lost:          ["active", "written_off"],
  decommissioned:[], sold:[], transferred:[], written_off:[],
};

// ─── Mock Data ────────────────────────────────────────────────────────────────
const DRONE = {
  name: "Eagle-7 Alpha",
  serial: "DRN-2024-0847-MIL",
  inventory: "INV-MIL-0847",
  status: "active" as DroneStatus,
  classification: "secret" as Classification,
  model: "MQ-9B SkyGuardian",
  manufacturer: "General Atomics Aeronautical Systems",
  unit: "3rd Reconnaissance Bn, 1st ISR Brigade",
  acquired: "15 Mar 2023",
  lastUpdated: "18 Nov 2024 — 14:22 UTC",
};

const SPEC_GROUPS = [
  {
    id: "hardware", label: "Hardware", icon: Cpu,
    specs: [
      { key: "wingspan",    label: "Wingspan",              value: "24.0 m" },
      { key: "length",      label: "Length",                value: "11.7 m" },
      { key: "mtow",        label: "Max Take-Off Weight",   value: "5,670 kg" },
      { key: "fuel",        label: "Fuel Capacity",         value: "1,800 kg" },
      { key: "engine",      label: "Engine",                value: "Honeywell TPE331-10GD" },
      { key: "powerplant",  label: "Powerplant",            value: "Single turboprop" },
      { key: "endurance",   label: "Endurance",             value: "40+ hours" },
      { key: "ferry_range", label: "Ferry Range",           value: "1,900 km" },
    ],
  },
  {
    id: "firmware", label: "Firmware & Software", icon: Zap,
    specs: [
      { key: "fw_ver",     label: "Firmware Version",       value: "v4.7.2-MIL" },
      { key: "fw_date",    label: "Last Updated",           value: "02 Nov 2024" },
      { key: "autopilot",  label: "Autopilot System",       value: "GA-ASI SATCOM Link v3" },
      { key: "gcs",        label: "Ground Control Station", value: "GCS-MQ9B-R2" },
      { key: "datalink",   label: "Datalink Protocol",      value: "CDL-MIL-STD-1553B" },
    ],
  },
  {
    id: "performance", label: "Performance & Range", icon: Activity,
    specs: [
      { key: "ceiling",    label: "Service Ceiling",        value: "15,240 m (50,000 ft)" },
      { key: "cruise",     label: "Cruise Speed",           value: "240 km/h" },
      { key: "max_spd",    label: "Max Speed",              value: "408 km/h" },
      { key: "stall",      label: "Stall Speed",            value: "130 km/h" },
      { key: "climb",      label: "Rate of Climb",          value: "366 m/min" },
      { key: "com_range",  label: "Comms Range",            value: "6,000 km (SATCOM)" },
    ],
  },
  {
    id: "payload", label: "Payload & Sensors", icon: Camera,
    specs: [
      { key: "payload",    label: "Payload Capacity",       value: "2,177 kg" },
      { key: "hardpoints", label: "Hardpoints",             value: "7 (6 wing, 1 center)" },
      { key: "eoir",       label: "EO/IR Sensor",           value: "MTS-B Multi-Spectral Targeting" },
      { key: "radar",      label: "Radar",                  value: "Lynx Multi-mode SAR/GMTI" },
      { key: "aesa",       label: "AESA Radar",             value: "Installed" },
      { key: "elint",      label: "ELINT Package",          value: "Installed" },
      { key: "relay",      label: "Comms Relay",            value: "ROVER-compatible" },
    ],
  },
];

const STATUS_HISTORY = [
  { id:"sh-1", from:"maintenance" as DroneStatus, to:"active" as DroneStatus,    actor:"CPT. Rivera, M.", ts:"18 Nov 2024 — 14:22 UTC", note:"Maintenance complete. Post-inspection passed. Cleared for operational duty." },
  { id:"sh-2", from:"in_mission"  as DroneStatus, to:"maintenance" as DroneStatus, actor:"SGT. Kowalski, P.", ts:"04 Nov 2024 — 08:45 UTC", note:"Returned from OP DARK HORIZON. Minor EO sensor calibration required. Routed to depot." },
  { id:"sh-3", from:"active"      as DroneStatus, to:"in_mission" as DroneStatus,  actor:"MAJ. Chen, L.",    ts:"28 Oct 2024 — 22:00 UTC", note:"Tasked for OP DARK HORIZON. Mission order #MO-2024-0287 issued." },
  { id:"sh-4", from:"maintenance" as DroneStatus, to:"active" as DroneStatus,    actor:"CPT. Rivera, M.", ts:"15 Sep 2024 — 09:10 UTC", note:"Scheduled 500-hr airframe inspection complete. All systems nominal." },
  { id:"sh-5", from:"active"      as DroneStatus, to:"maintenance" as DroneStatus, actor:"SYSTEM",           ts:"10 Sep 2024 — 06:00 UTC", note:"Auto-triggered: 500-hour scheduled maintenance threshold reached." },
];

const SPEC_CHANGES = [
  { id:"sc-1", field:"Firmware Version",      old:"v4.6.8-MIL",                      nw:"v4.7.2-MIL",                       by:"CPT. Rivera, M.", ts:"02 Nov 2024 — 11:34 UTC" },
  { id:"sc-2", field:"EO/IR Sensor",          old:"MTS-A Multi-Spectral Targeting",  nw:"MTS-B Multi-Spectral Targeting",   by:"SGT. Kowalski, P.", ts:"04 Nov 2024 — 09:02 UTC" },
  { id:"sc-3", field:"Last Updated",          old:"15 Sep 2024",                     nw:"02 Nov 2024",                      by:"CPT. Rivera, M.", ts:"02 Nov 2024 — 11:34 UTC" },
  { id:"sc-4", field:"Ground Control Station",old:"GCS-MQ9B-R1",                     nw:"GCS-MQ9B-R2",                      by:"MAJ. Chen, L.",   ts:"15 Sep 2024 — 10:20 UTC" },
  { id:"sc-5", field:"Datalink Protocol",     old:"CDL-MIL-STD-1553A",               nw:"CDL-MIL-STD-1553B",                by:"MAJ. Chen, L.",   ts:"15 Sep 2024 — 10:18 UTC" },
];

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard",  icon: LayoutDashboard },
  { id: "drones",    label: "Drones",     icon: Plane, active: true },
  { id: "missions",  label: "Missions",   icon: Crosshair },
  { id: "units",     label: "Units",      icon: Building2 },
  { id: "reports",   label: "Reports",    icon: BarChart2 },
];

// ─── Small Components ─────────────────────────────────────────────────────────

function StatusBadge({ status, size = "md" }: { status: DroneStatus; size?: "sm" | "md" | "lg" }) {
  const { label, color, bg } = STATUS_CFG[status];
  const cls = { sm: "text-[10px] px-2 py-0.5 gap-1", md: "text-xs px-2.5 py-1 gap-1.5", lg: "text-sm px-3 py-1.5 gap-2" }[size];
  const dot = { sm: "w-1.5 h-1.5", md: "w-1.5 h-1.5", lg: "w-2 h-2" }[size];
  return (
    <span className={`inline-flex items-center rounded-full font-mono font-medium whitespace-nowrap ${cls}`}
      style={{ color, backgroundColor: bg, border: `1px solid ${color}30` }}>
      <span className={`${dot} rounded-full flex-shrink-0`} style={{ backgroundColor: color }} />
      {label}
    </span>
  );
}

function ClassPill({ cls }: { cls: Classification }) {
  const { label, color } = CLASS_CFG[cls];
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full text-[9px] font-bold tracking-[0.14em] px-3 py-1 font-mono whitespace-nowrap"
      style={{ color, border: `1px solid ${color}35`, backgroundColor: `${color}0A` }}>
      <Shield size={9} />
      {label}
    </span>
  );
}

function Btn({
  children, variant = "secondary", size = "md", disabled = false, onClick, className = "",
}: {
  children: React.ReactNode;
  variant?: "primary" | "secondary" | "ghost" | "destructive";
  size?: "sm" | "md";
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
}) {
  const base = "inline-flex items-center gap-2 font-medium rounded-lg transition-all duration-150 cursor-pointer select-none whitespace-nowrap";
  const sizes = { sm: "text-xs px-3 py-1.5", md: "text-sm px-4 py-2" };
  const variants = {
    primary:     "bg-primary text-primary-foreground hover:bg-[#D9B05C] active:bg-[#B8923E]",
    secondary:   "bg-secondary text-foreground border border-border hover:bg-[#243040] active:bg-[#1A2535]",
    ghost:       "text-muted-foreground hover:text-foreground hover:bg-secondary",
    destructive: "bg-[#E5484D]/10 text-[#E5484D] border border-[#E5484D]/25 hover:bg-[#E5484D]/20",
  };
  const dis = "opacity-40 cursor-not-allowed pointer-events-none";
  return (
    <button
      className={`${base} ${sizes[size]} ${variants[variant]} ${disabled ? dis : ""} ${className}`}
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}

function FieldRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-4 py-2 border-b border-border/50 last:border-0">
      <span className="text-[13px] text-muted-foreground flex-shrink-0 w-44">{label}</span>
      <span className={`text-[14px] text-foreground text-right ${mono ? "font-mono" : ""}`}>{value}</span>
    </div>
  );
}

function FieldInput({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div className="flex items-center justify-between gap-4 py-2 border-b border-border/50 last:border-0">
      <span className="text-[13px] text-muted-foreground flex-shrink-0 w-44">{label}</span>
      <input
        className="flex-1 text-[13px] text-right bg-secondary border border-border rounded-md px-2.5 py-1 text-foreground focus:outline-none focus:ring-1 focus:ring-primary min-w-0"
        value={value}
        onChange={e => onChange(e.target.value)}
      />
    </div>
  );
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────
function Sidebar() {
  return (
    <aside className="w-56 flex-shrink-0 flex flex-col border-r border-border bg-sidebar h-full">
      {/* Logo */}
      <div className="h-14 flex items-center px-5 border-b border-sidebar-border flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-primary/15 flex items-center justify-center border border-primary/30">
            <Radio size={14} className="text-primary" />
          </div>
          <div>
            <div className="text-[11px] font-bold tracking-[0.12em] text-foreground font-mono uppercase">Mission</div>
            <div className="text-[9px] tracking-[0.14em] text-muted-foreground font-mono uppercase">Control System</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group ${
              item.active
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:text-foreground hover:bg-secondary"
            }`}
          >
            <item.icon size={16} className={item.active ? "text-primary" : "text-muted-foreground group-hover:text-foreground"} />
            {item.label}
            {item.active && <span className="ml-auto w-1.5 h-1.5 rounded-full bg-primary" />}
          </button>
        ))}
      </nav>

      {/* Bottom */}
      <div className="border-t border-sidebar-border px-3 py-3 space-y-0.5 flex-shrink-0">
        <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition-all">
          <Settings size={15} />
          Settings
        </button>
        <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition-all">
          <HelpCircle size={15} />
          Help & Docs
        </button>
        <div className="mt-2 pt-2 border-t border-sidebar-border flex items-center gap-2.5 px-2">
          <div className="w-7 h-7 rounded-full bg-secondary border border-border flex items-center justify-center flex-shrink-0">
            <UserCircle size={16} className="text-muted-foreground" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-medium text-foreground truncate">MAJ. Chen, L.</div>
            <div className="text-[10px] text-muted-foreground truncate">Fleet Commander</div>
          </div>
          <button className="text-muted-foreground hover:text-foreground transition-colors">
            <LogOut size={13} />
          </button>
        </div>
      </div>
    </aside>
  );
}

// ─── Top Bar ──────────────────────────────────────────────────────────────────
function TopBar() {
  return (
    <header className="h-14 flex items-center px-6 border-b border-border bg-background/95 backdrop-blur-sm flex-shrink-0 gap-4">
      <div className="flex-1 flex items-center gap-2 max-w-xs">
        <div className="flex-1 flex items-center gap-2 bg-secondary border border-border rounded-lg px-3 py-1.5">
          <Search size={13} className="text-muted-foreground flex-shrink-0" />
          <input
            className="flex-1 text-sm bg-transparent text-foreground placeholder:text-muted-foreground focus:outline-none"
            placeholder="Search assets, missions, units..."
          />
        </div>
      </div>
      <div className="flex items-center gap-2 ml-auto">
        <button className="relative p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary transition-all">
          <Bell size={16} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-[#E5484D]" />
        </button>
        <div className="h-5 w-px bg-border" />
        <div className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-secondary transition-all cursor-pointer">
          <div className="w-6 h-6 rounded-full bg-primary/15 border border-primary/30 flex items-center justify-center">
            <span className="text-[10px] font-bold text-primary font-mono">LC</span>
          </div>
          <span className="text-sm font-medium text-foreground">MAJ. Chen</span>
          <ChevronDown size={12} className="text-muted-foreground" />
        </div>
      </div>
    </header>
  );
}

// ─── Change Status Modal ──────────────────────────────────────────────────────
function ChangeStatusModal({
  currentStatus, onClose, onConfirm,
}: {
  currentStatus: DroneStatus;
  onClose: () => void;
  onConfirm: (to: DroneStatus, note: string) => void;
}) {
  const allowed = TRANSITIONS[currentStatus];
  const [selected, setSelected] = useState<DroneStatus | null>(null);
  const [note, setNote] = useState("");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      <div
        className="relative bg-card border border-border rounded-xl shadow-2xl w-full max-w-md"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h3 className="text-base font-semibold text-foreground">Change Status</h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors">
            <X size={16} />
          </button>
        </div>

        <div className="p-6 space-y-5">
          <div>
            <div className="text-xs text-muted-foreground mb-2 font-mono uppercase tracking-wider">Current Status</div>
            <StatusBadge status={currentStatus} size="lg" />
          </div>

          <div>
            <div className="text-xs text-muted-foreground mb-3 font-mono uppercase tracking-wider">Transition To</div>
            {allowed.length === 0 ? (
              <p className="text-sm text-muted-foreground italic">No transitions available from this state.</p>
            ) : (
              <div className="space-y-2">
                {allowed.map(s => (
                  <button
                    key={s}
                    onClick={() => setSelected(s)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg border transition-all duration-150 text-left ${
                      selected === s
                        ? "border-primary bg-primary/10"
                        : "border-border bg-secondary hover:border-border/80 hover:bg-[#1E2A38]/70"
                    }`}
                  >
                    <div className="flex-1">
                      <StatusBadge status={s} size="sm" />
                    </div>
                    {selected === s && <Check size={14} className="text-primary flex-shrink-0" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {selected && (
            <div>
              <div className="text-xs text-muted-foreground mb-2 font-mono uppercase tracking-wider">Transition Summary</div>
              <div className="flex items-center gap-2 mb-4">
                <StatusBadge status={currentStatus} size="sm" />
                <ArrowRight size={14} className="text-muted-foreground flex-shrink-0" />
                <StatusBadge status={selected} size="sm" />
              </div>
              <label className="block text-xs text-muted-foreground mb-1.5">Note / Justification</label>
              <textarea
                className="w-full bg-secondary border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                rows={3}
                placeholder="Provide reason for status change..."
                value={note}
                onChange={e => setNote(e.target.value)}
              />
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border">
          <Btn variant="ghost" onClick={onClose}>Cancel</Btn>
          <Btn
            variant="primary"
            disabled={!selected}
            onClick={() => selected && onConfirm(selected, note)}
          >
            <Check size={14} />
            Confirm Change
          </Btn>
        </div>
      </div>
    </div>
  );
}

// ─── Specs Tab ────────────────────────────────────────────────────────────────
function SpecsTab({ canEdit }: { canEdit: boolean }) {
  const [editing, setEditing] = useState(false);
  const [editVals, setEditVals] = useState<Record<string, string>>(() => {
    const vals: Record<string, string> = {};
    SPEC_GROUPS.forEach(g => g.specs.forEach(s => { vals[s.key] = s.value; }));
    return vals;
  });
  const [saved, setSaved] = useState(false);

  function handleSave() {
    setSaved(true);
    setEditing(false);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div>
      {/* Tab header actions */}
      <div className="flex items-center justify-between mb-6">
        <p className="text-sm text-muted-foreground">
          Technical specifications for this asset. Last updated <span className="text-foreground font-mono">02 Nov 2024</span>.
        </p>
        <div className="flex items-center gap-2">
          {saved && (
            <span className="flex items-center gap-1.5 text-xs text-[#3FB950]">
              <Check size={12} /> Saved
            </span>
          )}
          {editing ? (
            <>
              <Btn variant="ghost" size="sm" onClick={() => setEditing(false)}>
                <X size={13} />Cancel
              </Btn>
              <Btn variant="primary" size="sm" onClick={handleSave}>
                <Save size={13} />Save Changes
              </Btn>
            </>
          ) : (
            <Btn variant="secondary" size="sm" disabled={!canEdit} onClick={() => setEditing(true)}>
              <Edit2 size={13} />Edit Specs
            </Btn>
          )}
        </div>
      </div>

      {/* Spec groups in two-column grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {SPEC_GROUPS.map(group => (
          <div key={group.id} className="bg-card border border-border rounded-xl overflow-hidden">
            <div className="flex items-center gap-2.5 px-5 py-3.5 border-b border-border bg-muted/50">
              <group.icon size={14} className="text-primary" />
              <span className="text-[13px] font-semibold text-foreground tracking-wide">{group.label}</span>
            </div>
            <div className="px-5 py-3">
              {group.specs.map(spec => (
                editing
                  ? <FieldInput
                      key={spec.key}
                      label={spec.label}
                      value={editVals[spec.key]}
                      onChange={v => setEditVals(prev => ({ ...prev, [spec.key]: v }))}
                    />
                  : <FieldRow key={spec.key} label={spec.label} value={spec.value} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Status History Tab ───────────────────────────────────────────────────────
function StatusHistoryTab() {
  if (STATUS_HISTORY.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <History size={32} className="text-muted-foreground/40 mb-3" />
        <p className="text-sm text-muted-foreground">No status transitions recorded yet.</p>
        <p className="text-xs text-muted-foreground/60 mt-1">Status changes will appear here once this asset is updated.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <p className="text-sm text-muted-foreground">
          Immutable record of all lifecycle status transitions. <span className="text-foreground">{STATUS_HISTORY.length} events</span>.
        </p>
        <Btn variant="secondary" size="sm">
          <ExternalLink size={12} />Export
        </Btn>
      </div>

      <div className="relative">
        {/* Timeline vertical line */}
        <div className="absolute left-[19px] top-5 bottom-5 w-px bg-border" />

        <div className="space-y-0">
          {STATUS_HISTORY.map((item, i) => (
            <div key={item.id} className="relative flex gap-5 group">
              {/* Dot */}
              <div className="relative z-10 flex-shrink-0">
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center border-2 mt-3"
                  style={{
                    backgroundColor: STATUS_CFG[item.to].bg,
                    borderColor: `${STATUS_CFG[item.to].color}50`,
                  }}
                >
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: STATUS_CFG[item.to].color }} />
                </div>
              </div>

              {/* Content */}
              <div className={`flex-1 bg-card border border-border rounded-xl p-4 mb-3 transition-all duration-150 group-hover:border-border/80`}>
                {/* From → To */}
                <div className="flex items-center gap-2 flex-wrap mb-3">
                  <StatusBadge status={item.from} size="sm" />
                  <ArrowRight size={12} className="text-muted-foreground flex-shrink-0" />
                  <StatusBadge status={item.to} size="sm" />
                  {i === 0 && (
                    <span className="ml-2 text-[10px] font-mono font-medium text-primary bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20">
                      LATEST
                    </span>
                  )}
                </div>

                {/* Note */}
                {item.note && (
                  <p className="text-[13px] text-foreground/80 mb-3 leading-relaxed">{item.note}</p>
                )}

                {/* Meta */}
                <div className="flex items-center gap-4 text-[11px] text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <User size={11} />{item.actor}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Clock size={11} /><span className="font-mono">{item.ts}</span>
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Spec Changes Tab ─────────────────────────────────────────────────────────
function SpecChangesTab() {
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const sorted = [...SPEC_CHANGES].sort((a, b) =>
    sortDir === "desc"
      ? b.ts.localeCompare(a.ts)
      : a.ts.localeCompare(b.ts)
  );

  if (SPEC_CHANGES.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <FileText size={32} className="text-muted-foreground/40 mb-3" />
        <p className="text-sm text-muted-foreground">No specification changes recorded.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <p className="text-sm text-muted-foreground">
          Audit trail of all field-level spec edits. <span className="text-foreground">{SPEC_CHANGES.length} records</span>.
        </p>
        <div className="flex items-center gap-2">
          <Btn variant="ghost" size="sm">
            <ArrowUpDown size={12} />Filter
          </Btn>
          <Btn variant="secondary" size="sm">
            <ExternalLink size={12} />Export
          </Btn>
        </div>
      </div>

      <div className="bg-card border border-border rounded-xl overflow-hidden">
        {/* Table header */}
        <div className="grid grid-cols-[2fr_2.5fr_2.5fr_1.5fr_1.8fr] gap-4 px-5 py-3 border-b border-border text-[11px] font-mono font-medium text-muted-foreground uppercase tracking-wider bg-muted/40">
          <span>Field</span>
          <span>Previous Value</span>
          <span>New Value</span>
          <span>Changed By</span>
          <button
            className="flex items-center gap-1 hover:text-foreground transition-colors"
            onClick={() => setSortDir(d => d === "desc" ? "asc" : "desc")}
          >
            Timestamp
            <SortAsc size={11} className={sortDir === "asc" ? "text-primary" : ""} />
          </button>
        </div>

        {/* Rows */}
        {sorted.map((row, i) => (
          <div
            key={row.id}
            className={`grid grid-cols-[2fr_2.5fr_2.5fr_1.5fr_1.8fr] gap-4 px-5 py-3.5 items-center text-sm transition-colors hover:bg-muted/30 ${
              i < sorted.length - 1 ? "border-b border-border/60" : ""
            }`}
          >
            <span className="font-medium text-foreground text-[13px]">{row.field}</span>
            <span className="font-mono text-[12px] text-muted-foreground line-through decoration-[#E5484D]/50">{row.old}</span>
            <span className="font-mono text-[12px] text-[#3FB950]">{row.nw}</span>
            <span className="text-[12px] text-muted-foreground">{row.by}</span>
            <span className="font-mono text-[11px] text-muted-foreground">{row.ts}</span>
          </div>
        ))}

        {/* Pagination */}
        <div className="flex items-center justify-between px-5 py-3 border-t border-border bg-muted/20">
          <span className="text-xs text-muted-foreground">
            Showing 1–{sorted.length} of {sorted.length} records
          </span>
          <div className="flex items-center gap-1">
            {["1"].map(p => (
              <button key={p} className="w-7 h-7 rounded-md text-xs font-mono bg-primary text-primary-foreground">
                {p}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Write-offs Tab ───────────────────────────────────────────────────────────
function WriteoffsTab({ canWriteoff }: { canWriteoff: boolean }) {
  const [submitted, setSubmitted] = useState(false);
  const [form, setForm] = useState({
    reason: "",
    authorized_by: "",
    mission: "",
    doc_number: "",
    date: "",
  });

  const isComplete = form.reason && form.authorized_by && form.doc_number && form.date;

  function handleSubmit() {
    if (!isComplete) return;
    setSubmitted(true);
  }

  return (
    <div>
      {/* Prior records notice */}
      {!submitted && (
        <div className="flex items-center gap-3 mb-6 px-4 py-3 bg-muted/40 border border-border rounded-lg">
          <div className="w-1.5 h-1.5 rounded-full bg-[#3FB950] flex-shrink-0" />
          <p className="text-sm text-muted-foreground">
            No write-off records on file for this asset. Asset is currently operational.
          </p>
        </div>
      )}

      {/* Immutable record card (post-submit) */}
      {submitted && (
        <div className="mb-8 bg-card border border-[#8A94A6]/30 rounded-xl overflow-hidden">
          <div className="flex items-center gap-3 px-5 py-3.5 border-b border-border bg-muted/40">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-[#8A94A6]" />
              <span className="text-[13px] font-semibold text-foreground">Write-off Record</span>
            </div>
            <span className="ml-auto text-[11px] font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded border border-border">
              IMMUTABLE
            </span>
          </div>
          <div className="px-5 py-4 space-y-0">
            <FieldRow label="Document Number"     value={form.doc_number}    mono />
            <FieldRow label="Write-off Date"      value={form.date}          mono />
            <FieldRow label="Authorized By"       value={form.authorized_by}       />
            <FieldRow label="Related Mission"     value={form.mission || "N/A"}    />
            <FieldRow label="Reason"              value={form.reason}              />
          </div>
          <div className="flex items-center justify-between px-5 py-3 border-t border-border bg-muted/20">
            <span className="text-[11px] text-muted-foreground font-mono">
              Recorded by MAJ. Chen, L. — {new Date().toUTCString().replace(" GMT", " UTC")}
            </span>
            <button className="flex items-center gap-1.5 text-xs text-primary hover:underline transition-colors">
              <ExternalLink size={11} />View Full Report
            </button>
          </div>
        </div>
      )}

      {/* Create write-off form */}
      {!submitted && (
        <div className="bg-card border border-[#E5484D]/20 rounded-xl overflow-hidden">
          <div className="flex items-center gap-3 px-5 py-3.5 border-b border-[#E5484D]/20 bg-[#E5484D]/5">
            <AlertTriangle size={14} className="text-[#E5484D] flex-shrink-0" />
            <span className="text-[13px] font-semibold text-foreground">Create Write-off Record</span>
            <span className="ml-auto text-[11px] text-muted-foreground">Irreversible once submitted</span>
          </div>

          <div className="p-5 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-muted-foreground mb-1.5 font-mono uppercase tracking-wider">
                  Document Number <span className="text-[#E5484D]">*</span>
                </label>
                <input
                  className="w-full bg-secondary border border-border rounded-lg px-3 py-2.5 text-sm font-mono text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  placeholder="WO-2024-XXXX"
                  value={form.doc_number}
                  onChange={e => setForm(f => ({ ...f, doc_number: e.target.value }))}
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1.5 font-mono uppercase tracking-wider">
                  Write-off Date <span className="text-[#E5484D]">*</span>
                </label>
                <input
                  type="date"
                  className="w-full bg-secondary border border-border rounded-lg px-3 py-2.5 text-sm font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-primary [color-scheme:dark]"
                  value={form.date}
                  onChange={e => setForm(f => ({ ...f, date: e.target.value }))}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs text-muted-foreground mb-1.5 font-mono uppercase tracking-wider">
                Authorized By <span className="text-[#E5484D]">*</span>
              </label>
              <input
                className="w-full bg-secondary border border-border rounded-lg px-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                placeholder="Full name and rank of authorizing officer"
                value={form.authorized_by}
                onChange={e => setForm(f => ({ ...f, authorized_by: e.target.value }))}
              />
            </div>

            <div>
              <label className="block text-xs text-muted-foreground mb-1.5 font-mono uppercase tracking-wider">
                Related Mission / Operation
              </label>
              <input
                className="w-full bg-secondary border border-border rounded-lg px-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                placeholder="Operation name or mission ID (optional)"
                value={form.mission}
                onChange={e => setForm(f => ({ ...f, mission: e.target.value }))}
              />
            </div>

            <div>
              <label className="block text-xs text-muted-foreground mb-1.5 font-mono uppercase tracking-wider">
                Reason / Justification <span className="text-[#E5484D]">*</span>
              </label>
              <textarea
                className="w-full bg-secondary border border-border rounded-lg px-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                rows={4}
                placeholder="Provide a detailed justification for the write-off..."
                value={form.reason}
                onChange={e => setForm(f => ({ ...f, reason: e.target.value }))}
              />
            </div>

            {/* Warning */}
            <div className="flex items-start gap-3 px-4 py-3 bg-[#E5484D]/5 border border-[#E5484D]/20 rounded-lg">
              <AlertTriangle size={14} className="text-[#E5484D] flex-shrink-0 mt-0.5" />
              <p className="text-[12px] text-muted-foreground leading-relaxed">
                Write-off records are <strong className="text-foreground">immutable</strong> once submitted and cannot be modified or deleted.
                This action will also trigger a status change to <span className="font-mono text-[#8A94A6]">Written Off</span>.
                Ensure all information is accurate before proceeding.
              </p>
            </div>

            <div className="flex justify-end gap-3 pt-1">
              <Btn variant="ghost" size="sm">Cancel</Btn>
              <Btn
                variant="destructive"
                disabled={!canWriteoff || !isComplete}
                onClick={handleSubmit}
              >
                <AlertTriangle size={13} />
                Submit Write-off
              </Btn>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>("specs");
  const [drone, setDrone] = useState(DRONE);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [showOverflow, setShowOverflow] = useState(false);

  const canEdit     = true;  // Role: Fleet Commander
  const canWriteoff = true;

  const TABS: { id: TabId; label: string; icon: React.ElementType }[] = [
    { id: "specs",          label: "Specs",              icon: Cpu },
    { id: "status_history", label: "Status History",     icon: History },
    { id: "spec_changes",   label: "Spec Change History",icon: FileText },
    { id: "writeoffs",      label: "Write-offs",         icon: AlertTriangle },
  ];

  function handleStatusChange(to: DroneStatus, _note: string) {
    setDrone(d => ({ ...d, status: to }));
    setShowStatusModal(false);
  }

  return (
    <div className="dark flex h-screen w-screen overflow-hidden bg-background text-foreground" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
      <Sidebar />

      {/* Right pane */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <TopBar />

        {/* Scrollable main area */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto px-6 py-6">

            {/* ── Breadcrumb ── */}
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-5 font-mono">
              <span className="hover:text-foreground cursor-pointer transition-colors">Drones</span>
              <ChevronRight size={12} />
              <span className="text-foreground">{drone.serial}</span>
            </div>

            {/* ── Page Header ── */}
            <div className="mb-6">
              {/* Title row */}
              <div className="flex items-start justify-between gap-4 mb-4 flex-wrap">
                <div className="flex items-center gap-4 flex-wrap min-w-0">
                  <h1 className="text-2xl font-semibold text-foreground leading-tight">{drone.name}</h1>
                  <span className="text-base text-muted-foreground font-mono tracking-wide">{drone.serial}</span>
                  <StatusBadge status={drone.status} size="lg" />
                  <ClassPill cls={drone.classification} />
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  <Btn variant="secondary" size="sm" disabled={!canEdit}>
                    <Edit2 size={13} />Edit
                  </Btn>
                  <Btn
                    variant="primary"
                    size="sm"
                    disabled={TRANSITIONS[drone.status].length === 0}
                    onClick={() => setShowStatusModal(true)}
                  >
                    <ArrowRight size={13} />Change Status
                  </Btn>
                  <Btn variant="destructive" size="sm" disabled={!canWriteoff} onClick={() => setActiveTab("writeoffs")}>
                    <AlertTriangle size={13} />Write-off
                  </Btn>
                  <div className="relative">
                    <button
                      className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary border border-border transition-all"
                      onClick={() => setShowOverflow(v => !v)}
                    >
                      <MoreHorizontal size={15} />
                    </button>
                    {showOverflow && (
                      <>
                        <div className="fixed inset-0 z-40" onClick={() => setShowOverflow(false)} />
                        <div className="absolute right-0 top-full mt-1.5 z-50 w-44 bg-card border border-border rounded-xl shadow-2xl py-1 overflow-hidden">
                          {[
                            { label: "Duplicate Asset", icon: FileText },
                            { label: "Export Record", icon: ExternalLink },
                            { label: "Transfer Unit", icon: ArrowRight },
                          ].map(item => (
                            <button key={item.label} className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition-all text-left">
                              <item.icon size={13} />
                              {item.label}
                            </button>
                          ))}
                          <div className="h-px bg-border my-1" />
                          <button className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-[#E5484D] hover:bg-[#E5484D]/10 transition-all text-left">
                            <AlertTriangle size={13} />
                            Decommission
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Summary strip */}
              <div className="flex flex-wrap items-center gap-0 bg-card border border-border rounded-xl overflow-hidden">
                {[
                  { label: "Model",       value: drone.model,        mono: false },
                  { label: "Manufacturer",value: drone.manufacturer, mono: false },
                  { label: "Unit",        value: drone.unit,         mono: false },
                  { label: "Acquired",    value: drone.acquired,     mono: true },
                  { label: "Last Updated",value: drone.lastUpdated,  mono: true },
                ].map((item, i) => (
                  <div
                    key={item.label}
                    className={`flex flex-col px-5 py-3.5 ${i < 4 ? "border-r border-border" : ""} min-w-0`}
                  >
                    <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider mb-0.5">{item.label}</span>
                    <span className={`text-[13px] font-medium text-foreground truncate ${item.mono ? "font-mono" : ""}`}>{item.value}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* ── Tab Bar ── */}
            <div className="flex items-end gap-0 border-b border-border mb-6">
              {TABS.map(tab => {
                const active = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-5 py-3 text-sm font-medium transition-all duration-150 border-b-2 -mb-px ${
                      active
                        ? "border-primary text-primary"
                        : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                    }`}
                  >
                    <tab.icon size={14} />
                    {tab.label}
                  </button>
                );
              })}
            </div>

            {/* ── Tab Content ── */}
            <div className="pb-12">
              {activeTab === "specs"          && <SpecsTab canEdit={canEdit} />}
              {activeTab === "status_history" && <StatusHistoryTab />}
              {activeTab === "spec_changes"   && <SpecChangesTab />}
              {activeTab === "writeoffs"      && <WriteoffsTab canWriteoff={canWriteoff} />}
            </div>
          </div>
        </main>
      </div>

      {/* ── Change Status Modal ── */}
      {showStatusModal && (
        <ChangeStatusModal
          currentStatus={drone.status}
          onClose={() => setShowStatusModal(false)}
          onConfirm={handleStatusChange}
        />
      )}
    </div>
  );
}
