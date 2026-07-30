import { useState, useRef } from "react";
import {
  ChevronRight,
  Edit3,
  MoreHorizontal,
  MapPin,
  Clock,
  User,
  Users,
  Shield,
  Activity,
  Layers,
  FileText,
  Video,
  Upload,
  Download,
  Plus,
  Check,
  X,
  AlertTriangle,
  ChevronDown,
  Zap,
  Settings,
  BarChart2,
  Navigation,
  Radio,
  Target,
  ArrowRight,
  Image,
  Film,
  Paperclip,
  Trash2,
  Eye,
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────

type MissionStatus = "planned" | "active" | "completed" | "aborted";
type MissionResult = "success" | "failure" | null;
type ConditionAfter = "ok" | "damaged" | "lost" | null;
type UploadState = "idle" | "dragging" | "uploading" | "success" | "error";
type VideoStatus = "ready" | "uploading" | "failed";

interface TransitionRecord {
  id: string;
  from: MissionStatus;
  to: MissionStatus;
  by: string;
  at: string;
  note: string;
}

interface Assignment {
  id: string;
  drone: string;
  droneSerial: string;
  operator: string;
  flightStart: string;
  flightEnd: string;
  condition: ConditionAfter;
}

interface Artifact {
  id: string;
  title: string;
  type: string;
  size: string;
  uploadedBy: string;
  uploadedAt: string;
  ext: string;
}

interface VideoRecord {
  id: string;
  title: string;
  drone: string;
  status: VideoStatus;
  duration: string;
  size: string;
}

// ── Constants ──────────────────────────────────────────────────────────────

const STATUS_META: Record<MissionStatus, { label: string; color: string; bg: string }> = {
  planned:   { label: "Planned",   color: "#8A94A6", bg: "rgba(138,148,166,0.12)" },
  active:    { label: "Active",    color: "#3FB950", bg: "rgba(63,185,80,0.12)"   },
  completed: { label: "Completed", color: "#4C8DFF", bg: "rgba(76,141,255,0.12)"  },
  aborted:   { label: "Aborted",   color: "#E5484D", bg: "rgba(229,72,77,0.12)"   },
};

const VALID_TRANSITIONS: Record<MissionStatus, MissionStatus[]> = {
  planned:   ["active"],
  active:    ["completed", "aborted"],
  completed: [],
  aborted:   [],
};

const CONDITION_META: Record<string, { label: string; color: string; bg: string }> = {
  ok:      { label: "OK",      color: "#3FB950", bg: "rgba(63,185,80,0.12)"   },
  damaged: { label: "Damaged", color: "#C8A24A", bg: "rgba(200,162,74,0.12)"  },
  lost:    { label: "Lost",    color: "#E5484D", bg: "rgba(229,72,77,0.12)"   },
};

// ── Sidebar ────────────────────────────────────────────────────────────────

const NAV_ITEMS = [
  { icon: Activity,   label: "Dashboard",   active: false },
  { icon: Target,     label: "Missions",    active: true  },
  { icon: Navigation, label: "Fleet",       active: false },
  { icon: Users,      label: "Operators",   active: false },
  { icon: Radio,      label: "Telemetry",   active: false },
  { icon: BarChart2,  label: "Reports",     active: false },
  { icon: Layers,     label: "Artifacts",   active: false },
];

function Sidebar() {
  return (
    <aside
      className="flex flex-col h-full w-16 shrink-0 border-r"
      style={{ background: "#0D1219", borderColor: "rgba(255,255,255,0.06)" }}
    >
      {/* Logo */}
      <div className="flex items-center justify-center h-14 border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        <div className="w-8 h-8 flex items-center justify-center rounded" style={{ background: "rgba(200,162,74,0.15)" }}>
          <Shield size={16} style={{ color: "#C8A24A" }} />
        </div>
      </div>
      {/* Nav */}
      <nav className="flex-1 flex flex-col items-center gap-1 py-3">
        {NAV_ITEMS.map(({ icon: Icon, label, active }) => (
          <button
            key={label}
            title={label}
            className="w-10 h-10 flex items-center justify-center rounded-lg transition-all duration-150 group relative"
            style={{
              background: active ? "rgba(200,162,74,0.15)" : "transparent",
              color: active ? "#C8A24A" : "#4A5568",
            }}
            onMouseEnter={e => { if (!active) (e.currentTarget as HTMLElement).style.color = "#8A94A6"; (e.currentTarget as HTMLElement).style.background = active ? "rgba(200,162,74,0.15)" : "rgba(255,255,255,0.05)"; }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = active ? "#C8A24A" : "#4A5568"; (e.currentTarget as HTMLElement).style.background = active ? "rgba(200,162,74,0.15)" : "transparent"; }}
          >
            {active && <span className="absolute left-0 top-2 bottom-2 w-0.5 rounded-r" style={{ background: "#C8A24A" }} />}
            <Icon size={17} />
          </button>
        ))}
      </nav>
      {/* Settings */}
      <div className="flex flex-col items-center pb-4 gap-2">
        <button
          className="w-10 h-10 flex items-center justify-center rounded-lg transition-all"
          style={{ color: "#4A5568" }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = "#8A94A6"; (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)"; }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = "#4A5568"; (e.currentTarget as HTMLElement).style.background = "transparent"; }}
        >
          <Settings size={17} />
        </button>
        <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold" style={{ background: "rgba(200,162,74,0.2)", color: "#C8A24A" }}>
          KL
        </div>
      </div>
    </aside>
  );
}

// ── TopBar ─────────────────────────────────────────────────────────────────

function TopBar() {
  return (
    <header
      className="flex items-center justify-between h-14 px-6 border-b shrink-0"
      style={{ background: "#0B0F14", borderColor: "rgba(255,255,255,0.06)" }}
    >
      <div className="flex items-center gap-2 text-sm" style={{ fontFamily: "IBM Plex Sans, sans-serif" }}>
        <span style={{ color: "#4A5568" }}>Mission Control</span>
        <ChevronRight size={13} style={{ color: "#4A5568" }} />
        <span style={{ color: "#8A94A6" }}>Missions</span>
        <ChevronRight size={13} style={{ color: "#4A5568" }} />
        <span style={{ color: "#E6EAF0" }}>OPS-2247 Nightfall Recon</span>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: "#3FB950" }} />
          <span className="text-xs" style={{ color: "#8A94A6", fontFamily: "IBM Plex Mono, monospace" }}>SYSTEM NOMINAL</span>
        </div>
        <div className="text-xs" style={{ color: "#4A5568", fontFamily: "IBM Plex Mono, monospace" }}>
          UTC 2025-07-14 · 04:32:18Z
        </div>
      </div>
    </header>
  );
}

// ── Pills ──────────────────────────────────────────────────────────────────

function StatusPill({ status }: { status: MissionStatus }) {
  const m = STATUS_META[status];
  return (
    <span
      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold tracking-wide uppercase"
      style={{ color: m.color, background: m.bg, fontFamily: "IBM Plex Sans, sans-serif", letterSpacing: "0.06em" }}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: m.color }} />
      {m.label}
    </span>
  );
}

function ResultPill({ result }: { result: "success" | "failure" }) {
  const isSuccess = result === "success";
  return (
    <span
      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold tracking-wide uppercase"
      style={{
        color: isSuccess ? "#3FB950" : "#E5484D",
        background: isSuccess ? "rgba(63,185,80,0.12)" : "rgba(229,72,77,0.12)",
        fontFamily: "IBM Plex Sans, sans-serif",
        letterSpacing: "0.06em",
      }}
    >
      {isSuccess ? <Check size={11} /> : <X size={11} />}
      {isSuccess ? "Success" : "Failure"}
    </span>
  );
}

function ConditionPill({ condition }: { condition: ConditionAfter }) {
  if (!condition) return <span style={{ color: "#4A5568", fontSize: 12 }}>—</span>;
  const m = CONDITION_META[condition];
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
      style={{ color: m.color, background: m.bg }}
    >
      {m.label}
    </span>
  );
}

// ── MapPreview ─────────────────────────────────────────────────────────────

function MapPreview({ lat, lng }: { lat: number; lng: number }) {
  return (
    <div
      className="relative rounded-lg overflow-hidden"
      style={{ height: 200, background: "#0D1219", border: "1px solid rgba(255,255,255,0.08)" }}
    >
      {/* Grid lines */}
      <svg className="absolute inset-0 w-full h-full opacity-20" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
            <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#4C8DFF" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>
      {/* Topographic rings */}
      <svg className="absolute inset-0 w-full h-full opacity-10" xmlns="http://www.w3.org/2000/svg">
        {[60, 90, 120, 150].map(r => (
          <ellipse key={r} cx="50%" cy="50%" rx={r} ry={r * 0.6} fill="none" stroke="#4C8DFF" strokeWidth="1" />
        ))}
      </svg>
      {/* Scan lines */}
      <div className="absolute inset-0 opacity-5" style={{
        backgroundImage: "repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(76,141,255,0.3) 3px, rgba(76,141,255,0.3) 4px)"
      }} />
      {/* Marker */}
      <div className="absolute" style={{ left: "50%", top: "50%", transform: "translate(-50%, -100%)" }}>
        <div className="relative flex flex-col items-center">
          <div className="w-4 h-4 rounded-full border-2 flex items-center justify-center" style={{ borderColor: "#C8A24A", background: "rgba(200,162,74,0.3)" }}>
            <div className="w-1.5 h-1.5 rounded-full" style={{ background: "#C8A24A" }} />
          </div>
          <div className="w-px h-3" style={{ background: "#C8A24A" }} />
        </div>
      </div>
      {/* Pulse rings */}
      <div className="absolute" style={{ left: "50%", top: "50%", transform: "translate(-50%,-50%)" }}>
        <div className="absolute rounded-full animate-ping" style={{ width: 40, height: 40, margin: -20, border: "1px solid rgba(200,162,74,0.4)" }} />
      </div>
      {/* Corner markers */}
      {[
        ["top-2 left-2", "border-t border-l"],
        ["top-2 right-2", "border-t border-r"],
        ["bottom-2 left-2", "border-b border-l"],
        ["bottom-2 right-2", "border-b border-r"],
      ].map(([pos, border]) => (
        <div key={pos} className={`absolute w-3 h-3 ${pos} ${border}`} style={{ borderColor: "rgba(200,162,74,0.4)" }} />
      ))}
      {/* Coords overlay */}
      <div className="absolute bottom-2 left-3 right-3 flex justify-between items-end">
        <span className="text-xs" style={{ color: "#4C8DFF", fontFamily: "IBM Plex Mono, monospace" }}>
          {lat.toFixed(4)}°N · {Math.abs(lng).toFixed(4)}°E
        </span>
        <span className="text-xs" style={{ color: "#4A5568", fontFamily: "IBM Plex Mono, monospace" }}>
          MGRS 38T MQ
        </span>
      </div>
      <div className="absolute top-2 right-8 text-xs" style={{ color: "#8A94A6", fontFamily: "IBM Plex Mono, monospace" }}>
        OP AREA
      </div>
    </div>
  );
}

// ── StateMachine Stepper ───────────────────────────────────────────────────

const STATUS_ORDER: MissionStatus[] = ["planned", "active", "completed"];

function StateStepper({
  current,
  onTransition,
}: {
  current: MissionStatus;
  onTransition: (to: MissionStatus) => void;
}) {
  const [showModal, setShowModal] = useState(false);
  const [targetState, setTargetState] = useState<MissionStatus | null>(null);
  const [note, setNote] = useState("");

  const isAborted = current === "aborted";
  const nexts = VALID_TRANSITIONS[current];

  const displaySteps: MissionStatus[] = isAborted ? ["planned", "active", "aborted"] : STATUS_ORDER;

  function handleClick(to: MissionStatus) {
    setTargetState(to);
    setNote("");
    setShowModal(true);
  }

  function handleConfirm() {
    if (targetState) onTransition(targetState);
    setShowModal(false);
    setTargetState(null);
    setNote("");
  }

  const stepIndex = (s: MissionStatus) => {
    if (isAborted) {
      return { planned: 0, active: 1, aborted: 2 }[s] ?? -1;
    }
    return { planned: 0, active: 1, completed: 2 }[s] ?? -1;
  };

  const currentIdx = stepIndex(current);

  return (
    <>
      {/* Stepper visual */}
      <div className="flex items-center gap-0 mb-8">
        {displaySteps.map((step, i) => {
          const idx = stepIndex(step);
          const done = idx < currentIdx;
          const active = step === current;
          const meta = STATUS_META[step];
          return (
            <div key={step} className="flex items-center flex-1">
              <div className="flex flex-col items-center gap-2">
                <div
                  className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold transition-all"
                  style={{
                    background: active ? meta.bg : done ? "rgba(63,185,80,0.15)" : "rgba(255,255,255,0.05)",
                    border: `2px solid ${active ? meta.color : done ? "#3FB950" : "rgba(255,255,255,0.1)"}`,
                    color: active ? meta.color : done ? "#3FB950" : "#4A5568",
                  }}
                >
                  {done ? <Check size={14} /> : i + 1}
                </div>
                <span className="text-xs font-medium whitespace-nowrap" style={{ color: active ? meta.color : done ? "#8A94A6" : "#4A5568" }}>
                  {meta.label}
                </span>
              </div>
              {i < displaySteps.length - 1 && (
                <div
                  className="flex-1 h-px mx-2 mt-[-18px]"
                  style={{ background: done ? "#3FB950" : "rgba(255,255,255,0.08)" }}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Transition actions */}
      {nexts.length > 0 && (
        <div className="rounded-lg p-4 mb-6" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
          <p className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: "#8A94A6" }}>
            Available Transitions
          </p>
          <div className="flex gap-3">
            {nexts.map(to => {
              const m = STATUS_META[to];
              const isDestructive = to === "aborted";
              return (
                <button
                  key={to}
                  onClick={() => handleClick(to)}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-150"
                  style={{
                    background: isDestructive ? "rgba(229,72,77,0.15)" : "rgba(200,162,74,0.15)",
                    color: isDestructive ? "#E5484D" : "#C8A24A",
                    border: `1px solid ${isDestructive ? "rgba(229,72,77,0.3)" : "rgba(200,162,74,0.3)"}`,
                  }}
                  onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = isDestructive ? "rgba(229,72,77,0.25)" : "rgba(200,162,74,0.25)"; }}
                  onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = isDestructive ? "rgba(229,72,77,0.15)" : "rgba(200,162,74,0.15)"; }}
                >
                  <Zap size={13} />
                  Advance to {m.label}
                </button>
              );
            })}
          </div>
        </div>
      )}
      {(current === "completed" || current === "aborted") && (
        <div className="flex items-center gap-2 text-sm mb-6" style={{ color: "#8A94A6" }}>
          <Check size={14} style={{ color: "#3FB950" }} />
          Mission is in a terminal state — no further transitions available.
        </div>
      )}

      {/* Transition modal */}
      {showModal && targetState && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: "rgba(0,0,0,0.7)" }}>
          <div className="w-full max-w-md rounded-xl p-6" style={{ background: "#161D26", border: "1px solid rgba(255,255,255,0.1)" }}>
            <h3 className="text-base font-semibold mb-1" style={{ color: "#E6EAF0" }}>Confirm Transition</h3>
            <p className="text-sm mb-5" style={{ color: "#8A94A6" }}>
              Advance mission status from{" "}
              <span style={{ color: STATUS_META[current].color }}>{STATUS_META[current].label}</span>
              {" "}→{" "}
              <span style={{ color: STATUS_META[targetState].color }}>{STATUS_META[targetState].label}</span>
            </p>
            <label className="block text-xs font-medium mb-2" style={{ color: "#8A94A6" }}>Transition Note (optional)</label>
            <textarea
              className="w-full rounded-lg px-3 py-2 text-sm resize-none outline-none"
              rows={3}
              placeholder="Add context or reason for this transition..."
              value={note}
              onChange={e => setNote(e.target.value)}
              style={{
                background: "#0D1219",
                border: "1px solid rgba(255,255,255,0.1)",
                color: "#E6EAF0",
                fontFamily: "IBM Plex Sans, sans-serif",
              }}
            />
            <div className="flex gap-3 mt-5 justify-end">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 rounded-lg text-sm font-medium transition-all"
                style={{ background: "rgba(255,255,255,0.05)", color: "#8A94A6", border: "1px solid rgba(255,255,255,0.08)" }}
              >
                Cancel
              </button>
              <button
                onClick={handleConfirm}
                className="px-4 py-2 rounded-lg text-sm font-semibold transition-all"
                style={{ background: "#C8A24A", color: "#0B0F14" }}
              >
                Confirm Transition
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ── Transition History ─────────────────────────────────────────────────────

function TransitionHistory({ history }: { history: TransitionRecord[] }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wider mb-4" style={{ color: "#8A94A6" }}>Transition History</p>
      {history.length === 0 ? (
        <p className="text-sm" style={{ color: "#4A5568" }}>No transitions recorded yet.</p>
      ) : (
        <div className="flex flex-col gap-2">
          {history.map(r => (
            <div key={r.id} className="flex items-start gap-4 py-3 px-4 rounded-lg" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)" }}>
              <div className="flex items-center gap-2 pt-0.5">
                <span className="text-xs font-medium px-2 py-0.5 rounded" style={{ background: STATUS_META[r.from].bg, color: STATUS_META[r.from].color }}>{STATUS_META[r.from].label}</span>
                <ArrowRight size={12} style={{ color: "#4A5568" }} />
                <span className="text-xs font-medium px-2 py-0.5 rounded" style={{ background: STATUS_META[r.to].bg, color: STATUS_META[r.to].color }}>{STATUS_META[r.to].label}</span>
              </div>
              <div className="flex-1 min-w-0">
                {r.note && <p className="text-sm" style={{ color: "#E6EAF0" }}>{r.note}</p>}
                <div className="flex gap-3 mt-1">
                  <span className="text-xs" style={{ color: "#4A5568" }}>by {r.by}</span>
                  <span className="text-xs font-mono" style={{ color: "#4A5568", fontFamily: "IBM Plex Mono, monospace" }}>{r.at}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── AssignmentsTab ─────────────────────────────────────────────────────────

const DRONE_OPTIONS = ["UAV-HAWK-01 · HWK-001", "UAV-HAWK-02 · HWK-002", "UAV-RAVEN-03 · RVN-003", "UAV-GHOST-04 · GHT-004"];
const OPERATOR_OPTIONS = ["Sgt. M. Torres", "Cpl. D. Reyes", "Lt. A. Chen", "Sgt. K. Park"];

function AssignmentsTab({ status }: { status: MissionStatus }) {
  const [assignments, setAssignments] = useState<Assignment[]>([
    { id: "a1", drone: "UAV-HAWK-01", droneSerial: "HWK-001", operator: "Sgt. M. Torres", flightStart: "2025-07-14 01:15Z", flightEnd: "2025-07-14 03:47Z", condition: "ok" },
    { id: "a2", drone: "UAV-RAVEN-03", droneSerial: "RVN-003", operator: "Lt. A. Chen", flightStart: "2025-07-14 01:30Z", flightEnd: "2025-07-14 03:55Z", condition: "damaged" },
  ]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ drone: "", operator: "" });
  const [condModal, setCondModal] = useState<string | null>(null);
  const [condValue, setCondValue] = useState<ConditionAfter>(null);

  const isTerminal = status === "completed" || status === "aborted";

  function handleAdd() {
    if (!form.drone || !form.operator) return;
    const parts = form.drone.split(" · ");
    setAssignments(prev => [...prev, {
      id: `a${Date.now()}`,
      drone: parts[0],
      droneSerial: parts[1] || "",
      operator: form.operator,
      flightStart: "—",
      flightEnd: "—",
      condition: null,
    }]);
    setShowForm(false);
    setForm({ drone: "", operator: "" });
  }

  function handleSetCondition(id: string) {
    setAssignments(prev => prev.map(a => a.id === id ? { ...a, condition: condValue } : a));
    setCondModal(null);
    setCondValue(null);
  }

  return (
    <div>
      {/* Action row */}
      <div className="flex items-center justify-between mb-5">
        <p className="text-sm font-medium" style={{ color: "#8A94A6" }}>{assignments.length} drone{assignments.length !== 1 ? "s" : ""} assigned</p>
        {!isTerminal && (
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all"
            style={{ background: "rgba(200,162,74,0.15)", color: "#C8A24A", border: "1px solid rgba(200,162,74,0.3)" }}
          >
            <Plus size={14} /> Assign Drone / Operator
          </button>
        )}
      </div>

      {/* Form */}
      {showForm && (
        <div className="rounded-xl p-5 mb-5" style={{ background: "#1A2230", border: "1px solid rgba(200,162,74,0.2)" }}>
          <p className="text-sm font-semibold mb-4" style={{ color: "#E6EAF0" }}>New Assignment</p>
          <div className="grid grid-cols-2 gap-4 mb-4">
            {[
              { label: "Drone", key: "drone", options: DRONE_OPTIONS },
              { label: "Operator", key: "operator", options: OPERATOR_OPTIONS },
            ].map(({ label, key, options }) => (
              <div key={key}>
                <label className="block text-xs font-medium mb-1.5" style={{ color: "#8A94A6" }}>{label}</label>
                <div className="relative">
                  <select
                    value={(form as any)[key]}
                    onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                    className="w-full appearance-none rounded-lg px-3 py-2 text-sm outline-none pr-8"
                    style={{ background: "#0D1219", border: "1px solid rgba(255,255,255,0.1)", color: "#E6EAF0", fontFamily: "IBM Plex Sans, sans-serif" }}
                  >
                    <option value="">Select {label}</option>
                    {options.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                  <ChevronDown size={13} className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: "#4A5568" }} />
                </div>
              </div>
            ))}
          </div>
          <div className="flex gap-3 justify-end">
            <button onClick={() => setShowForm(false)} className="px-4 py-2 rounded-lg text-sm" style={{ color: "#8A94A6", background: "rgba(255,255,255,0.05)" }}>Cancel</button>
            <button onClick={handleAdd} className="px-4 py-2 rounded-lg text-sm font-semibold" style={{ background: "#C8A24A", color: "#0B0F14" }}>Assign</button>
          </div>
        </div>
      )}

      {/* Table */}
      {assignments.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 rounded-xl" style={{ border: "1px dashed rgba(255,255,255,0.08)" }}>
          <Users size={32} style={{ color: "#2E3A4A" }} className="mb-3" />
          <p className="text-sm font-medium mb-1" style={{ color: "#4A5568" }}>No assignments yet</p>
          <p className="text-xs" style={{ color: "#2E3A4A" }}>Assign a drone and operator to get started.</p>
        </div>
      ) : (
        <div className="rounded-xl overflow-hidden" style={{ border: "1px solid rgba(255,255,255,0.06)" }}>
          <table className="w-full text-sm">
            <thead>
              <tr style={{ background: "rgba(255,255,255,0.03)", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                {["Drone", "Serial", "Operator", "Flight Start", "Flight End", "Condition", ""].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wider" style={{ color: "#4A5568" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {assignments.map((a, i) => (
                <tr key={a.id} style={{ borderBottom: i < assignments.length - 1 ? "1px solid rgba(255,255,255,0.04)" : "none" }}>
                  <td className="px-4 py-3 font-medium" style={{ color: "#E6EAF0" }}>{a.drone}</td>
                  <td className="px-4 py-3" style={{ color: "#8A94A6", fontFamily: "IBM Plex Mono, monospace", fontSize: 12 }}>{a.droneSerial}</td>
                  <td className="px-4 py-3" style={{ color: "#E6EAF0" }}>{a.operator}</td>
                  <td className="px-4 py-3" style={{ color: "#8A94A6", fontFamily: "IBM Plex Mono, monospace", fontSize: 12 }}>{a.flightStart}</td>
                  <td className="px-4 py-3" style={{ color: "#8A94A6", fontFamily: "IBM Plex Mono, monospace", fontSize: 12 }}>{a.flightEnd}</td>
                  <td className="px-4 py-3"><ConditionPill condition={a.condition} /></td>
                  <td className="px-4 py-3">
                    {!isTerminal && (
                      <button
                        onClick={() => { setCondModal(a.id); setCondValue(a.condition); }}
                        className="text-xs px-2 py-1 rounded transition-all"
                        style={{ color: "#8A94A6", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)" }}
                      >
                        Set Condition
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Condition modal */}
      {condModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: "rgba(0,0,0,0.7)" }}>
          <div className="w-80 rounded-xl p-6" style={{ background: "#161D26", border: "1px solid rgba(255,255,255,0.1)" }}>
            <h3 className="text-base font-semibold mb-4" style={{ color: "#E6EAF0" }}>Record Post-Mission Condition</h3>
            <div className="flex flex-col gap-2 mb-5">
              {(["ok", "damaged", "lost"] as ConditionAfter[]).filter(Boolean).map(c => {
                const m = CONDITION_META[c!];
                return (
                  <button
                    key={c}
                    onClick={() => setCondValue(c)}
                    className="flex items-center justify-between px-4 py-3 rounded-lg text-sm font-medium transition-all"
                    style={{
                      background: condValue === c ? m.bg : "rgba(255,255,255,0.03)",
                      border: `1px solid ${condValue === c ? m.color : "rgba(255,255,255,0.06)"}`,
                      color: condValue === c ? m.color : "#8A94A6",
                    }}
                  >
                    {m.label}
                    {condValue === c && <Check size={14} />}
                  </button>
                );
              })}
            </div>
            <div className="flex gap-3 justify-end">
              <button onClick={() => setCondModal(null)} className="px-4 py-2 rounded-lg text-sm" style={{ color: "#8A94A6", background: "rgba(255,255,255,0.05)" }}>Cancel</button>
              <button onClick={() => handleSetCondition(condModal)} className="px-4 py-2 rounded-lg text-sm font-semibold" style={{ background: "#C8A24A", color: "#0B0F14" }}>Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── OutcomeTab ─────────────────────────────────────────────────────────────

function OutcomeTab({ status, result, onSaveResult }: {
  status: MissionStatus;
  result: MissionResult;
  onSaveResult: (r: MissionResult) => void;
}) {
  const [localResult, setLocalResult] = useState<MissionResult>(result);
  const [notes, setNotes] = useState(
    result === "success"
      ? "All objectives achieved. No casualties reported. Two drones returned with minor sensor wear. Intelligence package secured and transmitted to HQ at 04:12Z."
      : ""
  );
  const [saved, setSaved] = useState(!!result);
  const isTerminal = status === "completed" || status === "aborted";
  const isReadOnly = saved && isTerminal;

  function handleSave() {
    onSaveResult(localResult);
    setSaved(true);
  }

  if (isReadOnly && result) {
    return (
      <div>
        <div className="rounded-xl p-6 mb-6" style={{ background: "#1A2230", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ background: result === "success" ? "rgba(63,185,80,0.15)" : "rgba(229,72,77,0.15)" }}>
              {result === "success" ? <Check size={18} style={{ color: "#3FB950" }} /> : <X size={18} style={{ color: "#E5484D" }} />}
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider mb-0.5" style={{ color: "#4A5568" }}>Mission Result</p>
              <ResultPill result={result} />
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: "#4A5568" }}>Incident Notes</p>
            <p className="text-sm leading-relaxed" style={{ color: "#E6EAF0" }}>{notes || "No incident notes recorded."}</p>
          </div>
          <div className="mt-4 pt-4 flex items-center gap-3 text-xs" style={{ borderTop: "1px solid rgba(255,255,255,0.06)", color: "#4A5568" }}>
            <User size={12} />
            <span>Recorded by Col. R. Vasquez</span>
            <span style={{ fontFamily: "IBM Plex Mono, monospace" }}>· 2025-07-14 04:20Z</span>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs" style={{ color: "#4A5568" }}>
          <Shield size={12} />
          Outcome is locked — mission is in terminal state.
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-xl">
      <p className="text-sm mb-5" style={{ color: "#8A94A6" }}>Record the final outcome of this mission. This can be edited until the mission reaches a terminal state.</p>
      <div className="mb-5">
        <label className="block text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: "#4A5568" }}>Mission Result</label>
        <div className="flex gap-3">
          {(["success", "failure"] as const).map(r => (
            <button
              key={r}
              onClick={() => setLocalResult(r)}
              className="flex-1 py-3 rounded-xl text-sm font-semibold transition-all"
              style={{
                background: localResult === r
                  ? r === "success" ? "rgba(63,185,80,0.15)" : "rgba(229,72,77,0.15)"
                  : "rgba(255,255,255,0.03)",
                border: `1px solid ${localResult === r
                  ? r === "success" ? "#3FB950" : "#E5484D"
                  : "rgba(255,255,255,0.06)"}`,
                color: localResult === r
                  ? r === "success" ? "#3FB950" : "#E5484D"
                  : "#4A5568",
              }}
            >
              {r === "success" ? "✓ Success" : "✗ Failure"}
            </button>
          ))}
        </div>
      </div>
      <div className="mb-6">
        <label className="block text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: "#4A5568" }}>Incident Notes</label>
        <textarea
          rows={5}
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="Document any incidents, deviations from plan, equipment issues, or operational notes..."
          className="w-full rounded-xl px-4 py-3 text-sm resize-none outline-none"
          style={{ background: "#0D1219", border: "1px solid rgba(255,255,255,0.08)", color: "#E6EAF0", fontFamily: "IBM Plex Sans, sans-serif", lineHeight: 1.6 }}
        />
      </div>
      <button
        onClick={handleSave}
        disabled={!localResult}
        className="px-6 py-2.5 rounded-lg text-sm font-semibold transition-all"
        style={{
          background: localResult ? "#C8A24A" : "rgba(255,255,255,0.05)",
          color: localResult ? "#0B0F14" : "#4A5568",
          cursor: localResult ? "pointer" : "not-allowed",
        }}
      >
        Save Outcome
      </button>
    </div>
  );
}

// ── ArtifactsTab ───────────────────────────────────────────────────────────

const EXT_COLORS: Record<string, string> = {
  mp4: "#4C8DFF", pdf: "#E5484D", csv: "#3FB950", jpg: "#C8A24A", png: "#C8A24A", zip: "#8A94A6",
};

function DropZone({ label, onUpload }: { label: string; onUpload: () => void }) {
  const [state, setState] = useState<UploadState>("idle");

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setState("uploading");
    setTimeout(() => setState("success"), 1800);
  }

  function handleChange() {
    setState("uploading");
    setTimeout(() => setState("success"), 1800);
  }

  const inputRef = useRef<HTMLInputElement>(null);

  const bgColor = state === "dragging" ? "rgba(200,162,74,0.08)" : state === "error" ? "rgba(229,72,77,0.08)" : "rgba(255,255,255,0.02)";
  const borderColor = state === "dragging" ? "rgba(200,162,74,0.5)" : state === "error" ? "rgba(229,72,77,0.5)" : "rgba(255,255,255,0.08)";
  const textColor = state === "dragging" ? "#C8A24A" : state === "error" ? "#E5484D" : "#8A94A6";

  return (
    <div
      className="rounded-xl p-6 flex flex-col items-center justify-center text-center cursor-pointer transition-all"
      style={{ background: bgColor, border: `2px dashed ${borderColor}`, minHeight: 120 }}
      onDragOver={e => { e.preventDefault(); setState("dragging"); }}
      onDragLeave={() => setState("idle")}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
    >
      <input ref={inputRef} type="file" className="hidden" onChange={handleChange} multiple />
      {state === "uploading" ? (
        <div className="flex flex-col items-center gap-2">
          <div className="w-6 h-6 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: "#C8A24A", borderTopColor: "transparent" }} />
          <span className="text-sm" style={{ color: "#C8A24A" }}>Uploading...</span>
        </div>
      ) : state === "success" ? (
        <div className="flex flex-col items-center gap-2">
          <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ background: "rgba(63,185,80,0.15)" }}>
            <Check size={16} style={{ color: "#3FB950" }} />
          </div>
          <span className="text-sm" style={{ color: "#3FB950" }}>Upload complete</span>
          <button className="text-xs mt-1" style={{ color: "#8A94A6" }} onClick={e => { e.stopPropagation(); setState("idle"); }}>Upload another</button>
        </div>
      ) : (
        <>
          <Upload size={22} className="mb-2" style={{ color: textColor }} />
          <p className="text-sm font-medium" style={{ color: textColor }}>{label}</p>
          <p className="text-xs mt-1" style={{ color: "#4A5568" }}>Drag and drop or click to browse</p>
        </>
      )}
    </div>
  );
}

function ArtifactsTab() {
  const [artifacts] = useState<Artifact[]>([
    { id: "ar1", title: "Thermal Scan — Sector 7", type: "Image", size: "4.2 MB", uploadedBy: "Sgt. M. Torres", uploadedAt: "2025-07-14 03:55Z", ext: "jpg" },
    { id: "ar2", title: "Telemetry Export — HWK-001", type: "Data", size: "1.1 MB", uploadedBy: "Lt. A. Chen", uploadedAt: "2025-07-14 04:00Z", ext: "csv" },
    { id: "ar3", title: "Mission Debrief Report", type: "Document", size: "820 KB", uploadedBy: "Col. R. Vasquez", uploadedAt: "2025-07-14 04:20Z", ext: "pdf" },
    { id: "ar4", title: "Imagery Package", type: "Archive", size: "238 MB", uploadedBy: "Sgt. M. Torres", uploadedAt: "2025-07-14 04:25Z", ext: "zip" },
  ]);

  const [videos] = useState<VideoRecord[]>([
    { id: "v1", title: "HWK-001 Full Flight Recording", drone: "UAV-HAWK-01", status: "ready", duration: "2h 32m", size: "14.8 GB" },
    { id: "v2", title: "RVN-003 Sector Sweep", drone: "UAV-RAVEN-03", status: "ready", duration: "2h 25m", size: "11.2 GB" },
    { id: "v3", title: "Thermal Overlay Composite", drone: "UAV-HAWK-01", status: "uploading", duration: "—", size: "—" },
  ]);

  return (
    <div>
      {/* Artifacts grid */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold" style={{ color: "#E6EAF0" }}>Artifacts &amp; Data Files</h3>
          <span className="text-xs" style={{ color: "#4A5568" }}>{artifacts.length} files</span>
        </div>
        <div className="grid grid-cols-2 gap-3 mb-4">
          {artifacts.map(a => (
            <div key={a.id} className="flex items-start gap-3 p-4 rounded-xl group" style={{ background: "#1A2230", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0 text-xs font-bold" style={{ background: `${EXT_COLORS[a.ext] || "#8A94A6"}1A`, color: EXT_COLORS[a.ext] || "#8A94A6" }}>
                {a.ext.toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate" style={{ color: "#E6EAF0" }}>{a.title}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs" style={{ color: "#4A5568" }}>{a.type}</span>
                  <span style={{ color: "#2E3A4A" }}>·</span>
                  <span className="text-xs" style={{ color: "#4A5568", fontFamily: "IBM Plex Mono, monospace" }}>{a.size}</span>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs truncate" style={{ color: "#4A5568" }}>{a.uploadedBy}</span>
                  <span className="text-xs" style={{ color: "#2E3A4A", fontFamily: "IBM Plex Mono, monospace" }}>{a.uploadedAt}</span>
                </div>
              </div>
              <button className="opacity-0 group-hover:opacity-100 transition-opacity w-7 h-7 flex items-center justify-center rounded" style={{ color: "#8A94A6", background: "rgba(255,255,255,0.05)" }}>
                <Download size={13} />
              </button>
            </div>
          ))}
        </div>
        <DropZone label="Upload Artifact / Data File" onUpload={() => {}} />
      </div>

      {/* Videos */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold" style={{ color: "#E6EAF0" }}>Mission Videos</h3>
          <span className="text-xs" style={{ color: "#4A5568" }}>{videos.length} recordings</span>
        </div>
        <div className="flex flex-col gap-3 mb-4">
          {videos.map(v => (
            <div key={v.id} className="flex items-center gap-4 p-4 rounded-xl" style={{ background: "#1A2230", border: "1px solid rgba(255,255,255,0.06)" }}>
              {/* Thumbnail placeholder */}
              <div className="w-20 h-12 rounded-lg flex items-center justify-center shrink-0 relative overflow-hidden" style={{ background: "#0D1219" }}>
                <Film size={18} style={{ color: "#2E3A4A" }} />
                {v.status === "uploading" && (
                  <div className="absolute inset-0 flex items-center justify-center" style={{ background: "rgba(0,0,0,0.6)" }}>
                    <div className="w-4 h-4 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: "#C8A24A", borderTopColor: "transparent" }} />
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate" style={{ color: "#E6EAF0" }}>{v.title}</p>
                <div className="flex items-center gap-3 mt-1">
                  <span className="text-xs" style={{ color: "#4A5568" }}>{v.drone}</span>
                  {v.duration !== "—" && <span className="text-xs font-mono" style={{ color: "#4A5568", fontFamily: "IBM Plex Mono, monospace" }}>{v.duration}</span>}
                  {v.size !== "—" && <span className="text-xs font-mono" style={{ color: "#4A5568", fontFamily: "IBM Plex Mono, monospace" }}>{v.size}</span>}
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span
                  className="text-xs px-2 py-0.5 rounded-full font-medium"
                  style={{
                    color: v.status === "ready" ? "#3FB950" : v.status === "uploading" ? "#C8A24A" : "#E5484D",
                    background: v.status === "ready" ? "rgba(63,185,80,0.12)" : v.status === "uploading" ? "rgba(200,162,74,0.12)" : "rgba(229,72,77,0.12)",
                  }}
                >
                  {v.status === "ready" ? "Ready" : v.status === "uploading" ? "Uploading…" : "Failed"}
                </span>
                {v.status === "ready" && (
                  <button className="w-8 h-8 flex items-center justify-center rounded" style={{ color: "#8A94A6", background: "rgba(255,255,255,0.04)" }}>
                    <Eye size={14} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
        <DropZone label="Upload Mission Video" onUpload={() => {}} />
      </div>
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────

const TABS = [
  { id: "status",      label: "Status Control" },
  { id: "assignments", label: "Assignments"     },
  { id: "outcome",     label: "Outcome"         },
  { id: "artifacts",   label: "Artifacts & Videos" },
];

const INITIAL_HISTORY: TransitionRecord[] = [
  { id: "h1", from: "planned", to: "active", by: "Col. R. Vasquez", at: "2025-07-14 01:00Z", note: "All assets confirmed ready. Proceeding with insertion." },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("status");
  const [status, setStatus] = useState<MissionStatus>("active");
  const [result, setResult] = useState<MissionResult>(null);
  const [history, setHistory] = useState<TransitionRecord[]>(INITIAL_HISTORY);

  function handleTransition(to: MissionStatus) {
    const prev = status;
    setStatus(to);
    setHistory(h => [
      {
        id: `h${Date.now()}`,
        from: prev,
        to,
        by: "Col. R. Vasquez",
        at: new Date().toISOString().replace("T", " ").slice(0, 16) + "Z",
        note: "",
      },
      ...h,
    ]);
  }

  const isTerminal = status === "completed" || status === "aborted";

  return (
    <div
      className="flex h-screen w-screen overflow-hidden"
      style={{ fontFamily: "IBM Plex Sans, sans-serif", background: "#0B0F14" }}
    >
      <Sidebar />

      <div className="flex flex-col flex-1 min-w-0">
        <TopBar />

        {/* Scrollable content */}
        <main className="flex-1 overflow-y-auto" style={{ scrollbarWidth: "none" }}>
          <style>{`main::-webkit-scrollbar{display:none}`}</style>
          <div className="max-w-6xl mx-auto px-8 py-7">

            {/* Page header */}
            <div className="mb-6">
              {/* Breadcrumb */}
              <div className="flex items-center gap-1.5 text-xs mb-4" style={{ color: "#4A5568" }}>
                <span style={{ cursor: "pointer", color: "#8A94A6" }}>Missions</span>
                <ChevronRight size={12} />
                <span style={{ color: "#E6EAF0" }}>OPS-2247 Nightfall Recon</span>
              </div>

              {/* Title row */}
              <div className="flex items-start justify-between gap-6 mb-5">
                <div className="flex items-center gap-4 flex-wrap">
                  <h1 className="text-2xl font-semibold" style={{ color: "#E6EAF0", letterSpacing: "-0.02em" }}>
                    OPS-2247 · Nightfall Recon
                  </h1>
                  <StatusPill status={status} />
                  {isTerminal && result && <ResultPill result={result} />}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
                    style={{ background: "rgba(255,255,255,0.05)", color: "#8A94A6", border: "1px solid rgba(255,255,255,0.08)" }}
                    onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = "#E6EAF0"; (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.08)"; }}
                    onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = "#8A94A6"; (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)"; }}
                  >
                    <Edit3 size={13} /> Edit
                  </button>
                  {VALID_TRANSITIONS[status].length > 0 && (
                    <button
                      onClick={() => setActiveTab("status")}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all"
                      style={{ background: "#C8A24A", color: "#0B0F14" }}
                      onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "#D4AE5C"; }}
                      onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = "#C8A24A"; }}
                    >
                      <Zap size={13} /> Advance Status
                    </button>
                  )}
                  <button
                    className="w-9 h-9 flex items-center justify-center rounded-lg transition-all"
                    style={{ background: "rgba(255,255,255,0.05)", color: "#8A94A6", border: "1px solid rgba(255,255,255,0.08)" }}
                  >
                    <MoreHorizontal size={16} />
                  </button>
                </div>
              </div>

              {/* Summary strip */}
              <div className="flex items-center gap-6 flex-wrap py-3 px-4 rounded-xl" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)" }}>
                {[
                  { icon: Shield,  label: "Commander",  value: "Col. R. Vasquez" },
                  { icon: User,    label: "Created By",  value: "Maj. T. Singh" },
                  { icon: Clock,   label: "Started",     value: "2025-07-14 01:00Z", mono: true },
                  { icon: Clock,   label: "Ended",       value: isTerminal ? "2025-07-14 04:05Z" : "—", mono: true },
                  { icon: MapPin,  label: "Location",    value: "36.8219°N · 32.4842°E", mono: true },
                ].map(({ icon: Icon, label, value, mono }) => (
                  <div key={label} className="flex items-center gap-2">
                    <Icon size={13} style={{ color: "#4A5568" }} />
                    <span className="text-xs" style={{ color: "#4A5568" }}>{label}</span>
                    <span
                      className="text-xs font-medium"
                      style={{ color: "#8A94A6", fontFamily: mono ? "IBM Plex Mono, monospace" : "inherit" }}
                    >
                      {value}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Overview panel */}
            <div className="grid grid-cols-3 gap-5 mb-7">
              {/* Map */}
              <div className="col-span-1">
                <div className="rounded-xl p-4" style={{ background: "#161D26", border: "1px solid rgba(255,255,255,0.07)" }}>
                  <div className="flex items-center gap-2 mb-3">
                    <MapPin size={13} style={{ color: "#C8A24A" }} />
                    <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "#8A94A6" }}>Operational Area</span>
                  </div>
                  <MapPreview lat={36.8219} lng={32.4842} />
                  <p className="text-xs mt-3" style={{ color: "#4A5568" }}>Mersin Province, Southern Turkey — Grid 38T MQ 47820 31640</p>
                </div>
              </div>
              {/* Metadata */}
              <div className="col-span-2">
                <div className="rounded-xl p-4 h-full" style={{ background: "#161D26", border: "1px solid rgba(255,255,255,0.07)" }}>
                  <div className="flex items-center gap-2 mb-4">
                    <FileText size={13} style={{ color: "#C8A24A" }} />
                    <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "#8A94A6" }}>Mission Overview</span>
                  </div>
                  <div className="grid grid-cols-2 gap-x-8 gap-y-4 mb-5">
                    {[
                      { label: "Classification",  value: "SECRET // NOFORN" },
                      { label: "Priority",        value: "FLASH" },
                      { label: "Assigned Unit",   value: "3rd UAS Bn / Delta Co." },
                      { label: "Drones Deployed", value: "2 of 4 authorized" },
                      { label: "Flight Hours",    value: "4.88 hrs total" },
                      { label: "Data Collected",  value: "~26 GB" },
                    ].map(({ label, value }) => (
                      <div key={label}>
                        <p className="text-xs mb-1" style={{ color: "#4A5568" }}>{label}</p>
                        <p className="text-sm font-medium" style={{ color: "#E6EAF0" }}>{value}</p>
                      </div>
                    ))}
                  </div>
                  <div>
                    <p className="text-xs mb-2" style={{ color: "#4A5568" }}>Planned Notes</p>
                    <p className="text-sm leading-relaxed" style={{ color: "#8A94A6" }}>
                      Conduct persistent wide-area ISR over designated grid using thermal and EO payloads. Maintain min. 2 drones in orbit at all times. Transmit full imagery package to J2 within 30 min of RTB. Avoid populated areas north of River Line Bravo.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Tabs */}
            <div className="rounded-xl overflow-hidden" style={{ background: "#161D26", border: "1px solid rgba(255,255,255,0.07)" }}>
              {/* Tab bar */}
              <div className="flex border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
                {TABS.map(tab => {
                  const active = activeTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className="relative px-5 py-3.5 text-sm font-medium transition-all"
                      style={{
                        color: active ? "#C8A24A" : "#4A5568",
                        background: active ? "rgba(200,162,74,0.05)" : "transparent",
                      }}
                      onMouseEnter={e => { if (!active) (e.currentTarget as HTMLElement).style.color = "#8A94A6"; }}
                      onMouseLeave={e => { if (!active) (e.currentTarget as HTMLElement).style.color = "#4A5568"; }}
                    >
                      {active && (
                        <span className="absolute bottom-0 left-0 right-0 h-0.5" style={{ background: "#C8A24A" }} />
                      )}
                      {tab.label}
                    </button>
                  );
                })}
              </div>

              {/* Tab content */}
              <div className="p-6">
                {activeTab === "status" && (
                  <div>
                    <StateStepper current={status} onTransition={handleTransition} />
                    <TransitionHistory history={history} />
                  </div>
                )}
                {activeTab === "assignments" && <AssignmentsTab status={status} />}
                {activeTab === "outcome" && (
                  <OutcomeTab
                    status={status}
                    result={result}
                    onSaveResult={r => setResult(r)}
                  />
                )}
                {activeTab === "artifacts" && <ArtifactsTab />}
              </div>
            </div>

            {/* Bottom spacer */}
            <div className="h-8" />
          </div>
        </main>
      </div>
    </div>
  );
}
