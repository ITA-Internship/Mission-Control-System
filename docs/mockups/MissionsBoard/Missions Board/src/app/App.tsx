import { useState, useMemo } from "react";
import {
  LayoutGrid,
  List,
  Plus,
  Search,
  ChevronDown,
  X,
  ChevronUp,
  ChevronsUpDown,
  MapPin,
  Clock,
  Users,
  Eye,
  Pencil,
  ChevronLeft,
  ChevronRight,
  Target,
  Radio,
  Shield,
  Map,
  AlertTriangle,
  Crosshair,
  Navigation,
  Layers,
  Activity,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

type Status = "Planned" | "Active" | "Completed" | "Aborted";
type Result = "Success" | "Failure" | null;
type View = "board" | "list";

interface Mission {
  id: string;
  title: string;
  status: Status;
  commander: string;
  location: string;
  startedAt: string | null;
  endedAt: string | null;
  result: Result;
  droneCount: number;
  operatorCount: number;
  notes: string;
}

// ─── Mock Data ─────────────────────────────────────────────────────────────────

const COMMANDERS = [
  "Maj. R. Harlow",
  "Capt. D. Voss",
  "Lt. Col. A. Mercer",
  "Sgt. K. Osei",
  "Col. P. Stratton",
];

const MISSIONS: Mission[] = [
  {
    id: "MSN-001",
    title: "OPERATION SILENT WATCH",
    status: "Active",
    commander: "Maj. R. Harlow",
    location: "Grid 44T NV 834 621",
    startedAt: "2026-07-28 04:12",
    endedAt: null,
    result: null,
    droneCount: 4,
    operatorCount: 2,
    notes: "Perimeter surveillance of sector 7 industrial complex.",
  },
  {
    id: "MSN-002",
    title: "RECON ALPHA-7",
    status: "Active",
    commander: "Capt. D. Voss",
    location: "Grid 37S QA 112 448",
    startedAt: "2026-07-29 18:30",
    endedAt: null,
    result: null,
    droneCount: 2,
    operatorCount: 1,
    notes: "Forward reconnaissance prior to ground element advance.",
  },
  {
    id: "MSN-003",
    title: "BORDER SENTINEL III",
    status: "Planned",
    commander: "Lt. Col. A. Mercer",
    location: "Grid 55U FG 720 009",
    startedAt: null,
    endedAt: null,
    result: null,
    droneCount: 6,
    operatorCount: 3,
    notes: "Extended border patrol, 72-hour window.",
  },
  {
    id: "MSN-004",
    title: "DUST STORM ECHO",
    status: "Planned",
    commander: "Maj. R. Harlow",
    location: "Grid 38R LM 540 330",
    startedAt: null,
    endedAt: null,
    result: null,
    droneCount: 3,
    operatorCount: 2,
    notes: "Threat assessment following reported movement.",
  },
  {
    id: "MSN-005",
    title: "OPERATION NIGHTFALL",
    status: "Planned",
    commander: "Col. P. Stratton",
    location: "Grid 47N XK 880 150",
    startedAt: null,
    endedAt: null,
    result: null,
    droneCount: 8,
    operatorCount: 4,
    notes: "Coordinated night-ops surveillance, multi-vector.",
  },
  {
    id: "MSN-006",
    title: "HAMMER STRIKE II",
    status: "Completed",
    commander: "Sgt. K. Osei",
    location: "Grid 29Q BN 340 780",
    startedAt: "2026-07-20 06:00",
    endedAt: "2026-07-21 14:45",
    result: "Success",
    droneCount: 5,
    operatorCount: 3,
    notes: "Strike coordination and BDA assessment completed.",
  },
  {
    id: "MSN-007",
    title: "FALCON EYE SURVEY",
    status: "Completed",
    commander: "Capt. D. Voss",
    location: "Grid 51T KP 200 560",
    startedAt: "2026-07-15 09:30",
    endedAt: "2026-07-15 17:10",
    result: "Success",
    droneCount: 2,
    operatorCount: 1,
    notes: "Infrastructure damage assessment post-engagement.",
  },
  {
    id: "MSN-008",
    title: "GHOST TRAIL",
    status: "Aborted",
    commander: "Lt. Col. A. Mercer",
    location: "Grid 33P WS 610 200",
    startedAt: "2026-07-25 22:00",
    endedAt: "2026-07-25 22:47",
    result: "Failure",
    droneCount: 4,
    operatorCount: 2,
    notes: "Aborted due to signal jamming in sector. Assets recovered.",
  },
  {
    id: "MSN-009",
    title: "COLD RIDGE WATCH",
    status: "Completed",
    commander: "Col. P. Stratton",
    location: "Grid 60V ZA 050 820",
    startedAt: "2026-07-10 03:15",
    endedAt: "2026-07-13 12:00",
    result: "Success",
    droneCount: 6,
    operatorCount: 4,
    notes: "72-hour persistent ISR over ridge corridor.",
  },
  {
    id: "MSN-010",
    title: "OPERATION ANVIL",
    status: "Aborted",
    commander: "Maj. R. Harlow",
    location: "Grid 41S QR 880 440",
    startedAt: "2026-07-18 12:00",
    endedAt: "2026-07-18 14:22",
    result: "Failure",
    droneCount: 3,
    operatorCount: 2,
    notes: "Mission abort due to adverse weather conditions.",
  },
];

// ─── Status / Result helpers ───────────────────────────────────────────────────

const STATUS_META: Record<Status, { color: string; bg: string; label: string }> = {
  Planned: { color: "#8A94A6", bg: "rgba(138,148,166,0.15)", label: "PLANNED" },
  Active: { color: "#3FB950", bg: "rgba(63,185,80,0.15)", label: "ACTIVE" },
  Completed: { color: "#4C8DFF", bg: "rgba(76,141,255,0.15)", label: "COMPLETED" },
  Aborted: { color: "#E5484D", bg: "rgba(229,72,77,0.15)", label: "ABORTED" },
};

const RESULT_META: Record<NonNullable<Result>, { color: string; bg: string }> = {
  Success: { color: "#3FB950", bg: "rgba(63,185,80,0.15)" },
  Failure: { color: "#E5484D", bg: "rgba(229,72,77,0.15)" },
};

function StatusPill({ status }: { status: Status }) {
  const m = STATUS_META[status];
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium tracking-widest"
      style={{ color: m.color, background: m.bg, border: `1px solid ${m.color}30` }}
    >
      <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ background: m.color }} />
      {m.label}
    </span>
  );
}

function ResultPill({ result }: { result: Result }) {
  if (!result) return <span className="text-[#8A94A6] text-[11px] font-mono">—</span>;
  const m = RESULT_META[result];
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium tracking-widest"
      style={{ color: m.color, background: m.bg, border: `1px solid ${m.color}30` }}
    >
      {result === "Success" ? "✓" : "✗"} {result.toUpperCase()}
    </span>
  );
}

// ─── Sidebar ───────────────────────────────────────────────────────────────────

const NAV_ITEMS = [
  { icon: Activity, label: "Dashboard", active: false },
  { icon: Target, label: "Missions", active: true },
  { icon: Layers, label: "Drone Fleet", active: false },
  { icon: Users, label: "Operators", active: false },
  { icon: Map, label: "Live Map", active: false },
  { icon: Radio, label: "Telemetry", active: false },
  { icon: Shield, label: "Access Control", active: false },
];

function Sidebar() {
  return (
    <aside
      className="flex flex-col w-[220px] shrink-0 border-r h-full"
      style={{ background: "#0D1219", borderColor: "rgba(255,255,255,0.06)" }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-5 border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        <div
          className="w-8 h-8 rounded flex items-center justify-center"
          style={{ background: "#C8A24A" }}
        >
          <Crosshair size={16} color="#0B0F14" strokeWidth={2.5} />
        </div>
        <div>
          <div className="text-[13px] font-semibold text-[#E6EAF0] tracking-wide leading-none">MISSION</div>
          <div className="text-[10px] font-mono text-[#8A94A6] tracking-widest leading-none mt-0.5">CONTROL SYS</div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 px-2">
        {NAV_ITEMS.map(({ icon: Icon, label, active }) => (
          <button
            key={label}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg mb-0.5 text-left transition-all duration-150"
            style={{
              background: active ? "rgba(200,162,74,0.12)" : "transparent",
              color: active ? "#C8A24A" : "#8A94A6",
            }}
            onMouseEnter={e => {
              if (!active) {
                (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.04)";
                (e.currentTarget as HTMLElement).style.color = "#E6EAF0";
              }
            }}
            onMouseLeave={e => {
              if (!active) {
                (e.currentTarget as HTMLElement).style.background = "transparent";
                (e.currentTarget as HTMLElement).style.color = "#8A94A6";
              }
            }}
          >
            <Icon size={15} />
            <span className="text-[13px] font-medium">{label}</span>
            {active && (
              <span className="ml-auto w-1 h-1 rounded-full" style={{ background: "#C8A24A" }} />
            )}
          </button>
        ))}
      </nav>

      {/* User */}
      <div className="border-t px-4 py-3.5" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        <div className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-bold"
            style={{ background: "rgba(200,162,74,0.2)", color: "#C8A24A" }}
          >
            PS
          </div>
          <div>
            <div className="text-[12px] font-semibold text-[#E6EAF0]">Col. P. Stratton</div>
            <div className="text-[10px] font-mono text-[#8A94A6] tracking-wide">COMMANDER</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

// ─── Top Bar ───────────────────────────────────────────────────────────────────

function TopBar() {
  return (
    <header
      className="flex items-center justify-between px-6 h-[52px] border-b shrink-0"
      style={{ background: "#0D1219", borderColor: "rgba(255,255,255,0.06)" }}
    >
      <div className="flex items-center gap-2 text-[11px] font-mono text-[#8A94A6] tracking-wide">
        <span>MCS</span>
        <span className="text-[#3a4455]">/</span>
        <span className="text-[#C8A24A]">MISSIONS</span>
      </div>
      <div className="flex items-center gap-3">
        <div
          className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[11px] font-mono"
          style={{ background: "rgba(63,185,80,0.1)", color: "#3FB950", border: "1px solid rgba(63,185,80,0.2)" }}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[#3FB950] animate-pulse" />
          DATALINK ACTIVE
        </div>
        <div className="text-[11px] font-mono text-[#8A94A6]">UTC 2026-07-30 · 09:41:22</div>
      </div>
    </header>
  );
}

// ─── Filter Chip ───────────────────────────────────────────────────────────────

interface Chip {
  key: string;
  label: string;
}

function FilterChip({ chip, onRemove }: { chip: Chip; onRemove: () => void }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono"
      style={{
        background: "rgba(200,162,74,0.12)",
        color: "#C8A24A",
        border: "1px solid rgba(200,162,74,0.25)",
      }}
    >
      {chip.label}
      <button
        onClick={onRemove}
        className="hover:opacity-70 transition-opacity"
        aria-label="Remove filter"
      >
        <X size={10} />
      </button>
    </span>
  );
}

// ─── Filter Bar ────────────────────────────────────────────────────────────────

interface Filters {
  search: string;
  status: Status | "";
  commander: string;
  result: Result | "";
}

function FilterBar({
  filters,
  setFilters,
  chips,
  removeChip,
}: {
  filters: Filters;
  setFilters: (f: Filters) => void;
  chips: Chip[];
  removeChip: (key: string) => void;
}) {
  const [statusOpen, setStatusOpen] = useState(false);
  const [cmdOpen, setCmdOpen] = useState(false);
  const [resultOpen, setResultOpen] = useState(false);

  const dropdownClass =
    "absolute top-full left-0 mt-1 min-w-[160px] rounded-lg border py-1 z-50";
  const dropdownStyle = {
    background: "#1E2733",
    borderColor: "rgba(255,255,255,0.1)",
    boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
  };
  const optClass =
    "flex items-center gap-2 w-full text-left px-3 py-2 text-[12px] font-mono text-[#E6EAF0] hover:bg-white/5 transition-colors";

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 flex-wrap">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8A94A6]" />
          <input
            type="text"
            placeholder="Search title or location…"
            value={filters.search}
            onChange={e => setFilters({ ...filters, search: e.target.value })}
            className="w-full pl-8 pr-3 py-2 rounded-lg text-[13px] font-mono text-[#E6EAF0] placeholder-[#8A94A6] outline-none focus:ring-1 focus:ring-[#C8A24A]/40 transition-all"
            style={{ background: "#161D26", border: "1px solid rgba(255,255,255,0.08)" }}
          />
        </div>

        {/* Status dropdown */}
        <div className="relative">
          <button
            onClick={() => { setStatusOpen(o => !o); setCmdOpen(false); setResultOpen(false); }}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-[12px] font-mono text-[#8A94A6] hover:text-[#E6EAF0] transition-colors"
            style={{ background: "#161D26", border: "1px solid rgba(255,255,255,0.08)" }}
          >
            Status {filters.status && <span className="text-[#C8A24A]">·</span>}
            {filters.status || "All"}
            <ChevronDown size={11} />
          </button>
          {statusOpen && (
            <div className={dropdownClass} style={dropdownStyle}>
              {(["", "Planned", "Active", "Completed", "Aborted"] as const).map(s => (
                <button
                  key={s || "all"}
                  className={optClass}
                  onClick={() => { setFilters({ ...filters, status: s }); setStatusOpen(false); }}
                >
                  {s ? <span className="w-1.5 h-1.5 rounded-full" style={{ background: STATUS_META[s].color }} /> : <span className="w-1.5 h-1.5" />}
                  {s || "All Statuses"}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Commander dropdown */}
        <div className="relative">
          <button
            onClick={() => { setCmdOpen(o => !o); setStatusOpen(false); setResultOpen(false); }}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-[12px] font-mono text-[#8A94A6] hover:text-[#E6EAF0] transition-colors"
            style={{ background: "#161D26", border: "1px solid rgba(255,255,255,0.08)" }}
          >
            Commander {filters.commander && <span className="text-[#C8A24A]">·</span>}
            {filters.commander ? filters.commander.split(" ").slice(-1)[0] : "All"}
            <ChevronDown size={11} />
          </button>
          {cmdOpen && (
            <div className={dropdownClass} style={dropdownStyle}>
              <button className={optClass} onClick={() => { setFilters({ ...filters, commander: "" }); setCmdOpen(false); }}>
                All Commanders
              </button>
              {COMMANDERS.map(c => (
                <button key={c} className={optClass} onClick={() => { setFilters({ ...filters, commander: c }); setCmdOpen(false); }}>
                  {c}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Result dropdown */}
        <div className="relative">
          <button
            onClick={() => { setResultOpen(o => !o); setStatusOpen(false); setCmdOpen(false); }}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-[12px] font-mono text-[#8A94A6] hover:text-[#E6EAF0] transition-colors"
            style={{ background: "#161D26", border: "1px solid rgba(255,255,255,0.08)" }}
          >
            Result {filters.result && <span className="text-[#C8A24A]">·</span>}
            {filters.result || "All"}
            <ChevronDown size={11} />
          </button>
          {resultOpen && (
            <div className={dropdownClass} style={dropdownStyle}>
              {(["", "Success", "Failure"] as const).map(r => (
                <button
                  key={r || "all"}
                  className={optClass}
                  onClick={() => { setFilters({ ...filters, result: r }); setResultOpen(false); }}
                >
                  {r || "All Results"}
                </button>
              ))}
            </div>
          )}
        </div>

        {chips.length > 0 && (
          <button
            onClick={() => setFilters({ search: "", status: "", commander: "", result: "" })}
            className="text-[11px] font-mono text-[#8A94A6] hover:text-[#E5484D] transition-colors"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Active chips */}
      {chips.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          {chips.map(chip => (
            <FilterChip key={chip.key} chip={chip} onRemove={() => removeChip(chip.key)} />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Mission Card ──────────────────────────────────────────────────────────────

function MissionCard({ mission, onClick }: { mission: Mission; onClick: () => void }) {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="rounded-xl p-3.5 cursor-pointer transition-all duration-150 select-none"
      style={{
        background: hovered ? "#1E2733" : "#161D26",
        border: `1px solid ${hovered ? "rgba(200,162,74,0.25)" : "rgba(255,255,255,0.07)"}`,
        boxShadow: hovered ? "0 0 0 1px rgba(200,162,74,0.1)" : "none",
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2.5">
        <div>
          <div className="text-[11px] font-mono text-[#8A94A6] mb-0.5">{mission.id}</div>
          <div className="text-[13px] font-semibold text-[#E6EAF0] leading-snug tracking-wide">
            {mission.title}
          </div>
        </div>
        <StatusPill status={mission.status} />
      </div>

      {/* Meta */}
      <div className="flex flex-col gap-1.5 mb-3">
        <div className="flex items-center gap-1.5 text-[11px] text-[#8A94A6]">
          <Users size={10} className="shrink-0" />
          <span className="font-mono">{mission.commander}</span>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-[#8A94A6]">
          <MapPin size={10} className="shrink-0" />
          <span className="font-mono truncate">{mission.location}</span>
        </div>
        {mission.startedAt && (
          <div className="flex items-center gap-1.5 text-[11px] text-[#8A94A6]">
            <Clock size={10} className="shrink-0" />
            <span className="font-mono">{mission.startedAt}</span>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-2.5 border-t" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 text-[11px] font-mono text-[#8A94A6]">
            <Navigation size={10} />
            {mission.droneCount}
          </span>
          <span className="flex items-center gap-1 text-[11px] font-mono text-[#8A94A6]">
            <Users size={10} />
            {mission.operatorCount}
          </span>
        </div>
        {mission.result && <ResultPill result={mission.result} />}
      </div>
    </div>
  );
}

// ─── Kanban Column ─────────────────────────────────────────────────────────────

function KanbanColumn({
  status,
  missions,
  onCardClick,
}: {
  status: Status;
  missions: Mission[];
  onCardClick: (m: Mission) => void;
}) {
  const m = STATUS_META[status];
  return (
    <div
      className="flex flex-col rounded-xl min-w-[280px] max-w-[300px] flex-1"
      style={{
        background: "rgba(11,15,20,0.6)",
        border: "1px solid rgba(255,255,255,0.06)",
      }}
    >
      {/* Column header */}
      <div
        className="flex items-center justify-between px-4 py-3 rounded-t-xl border-b"
        style={{ borderColor: "rgba(255,255,255,0.06)" }}
      >
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: m.color }} />
          <span className="text-[12px] font-mono font-medium tracking-widest" style={{ color: m.color }}>
            {m.label}
          </span>
        </div>
        <span
          className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded-full"
          style={{ background: m.bg, color: m.color }}
        >
          {missions.length}
        </span>
      </div>

      {/* Cards */}
      <div className="flex-1 flex flex-col gap-2.5 p-3 overflow-y-auto" style={{ maxHeight: "calc(100vh - 280px)" }}>
        {missions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 gap-2">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: "rgba(255,255,255,0.04)" }}
            >
              <Target size={14} color="#8A94A6" />
            </div>
            <span className="text-[11px] font-mono text-[#8A94A6]">No missions</span>
          </div>
        ) : (
          missions.map(mission => (
            <MissionCard key={mission.id} mission={mission} onClick={() => onCardClick(mission)} />
          ))
        )}
      </div>
    </div>
  );
}

// ─── Data Table ────────────────────────────────────────────────────────────────

type SortKey = keyof Mission;
type SortDir = "asc" | "desc";

function DataTable({
  missions,
  onView,
  onEdit,
}: {
  missions: Mission[];
  onView: (m: Mission) => void;
  onEdit: (m: Mission) => void;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("startedAt");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [selected, setSelected] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const perPage = 6;

  const sorted = useMemo(() => {
    return [...missions].sort((a, b) => {
      const av = a[sortKey] ?? "";
      const bv = b[sortKey] ?? "";
      if (av < bv) return sortDir === "asc" ? -1 : 1;
      if (av > bv) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
  }, [missions, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / perPage));
  const pageData = sorted.slice((page - 1) * perPage, page * perPage);

  function handleSort(key: SortKey) {
    if (sortKey === key) setSortDir(d => (d === "asc" ? "desc" : "asc"));
    else { setSortKey(key); setSortDir("asc"); }
  }

  function SortIcon({ col }: { col: SortKey }) {
    if (sortKey !== col) return <ChevronsUpDown size={11} className="text-[#3a4455]" />;
    return sortDir === "asc" ? <ChevronUp size={11} className="text-[#C8A24A]" /> : <ChevronDown size={11} className="text-[#C8A24A]" />;
  }

  const thClass = "px-4 py-3 text-left text-[10px] font-mono font-medium tracking-widest text-[#8A94A6] select-none cursor-pointer hover:text-[#E6EAF0] transition-colors whitespace-nowrap";

  return (
    <div className="flex flex-col gap-3">
      <div
        className="rounded-xl overflow-hidden"
        style={{ border: "1px solid rgba(255,255,255,0.07)" }}
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px]">
            <thead>
              <tr style={{ background: "#0F1621", borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
                <th className={thClass} onClick={() => handleSort("title")}>
                  <div className="flex items-center gap-1.5">MISSION <SortIcon col="title" /></div>
                </th>
                <th className={thClass} onClick={() => handleSort("status")}>
                  <div className="flex items-center gap-1.5">STATUS <SortIcon col="status" /></div>
                </th>
                <th className={thClass} onClick={() => handleSort("commander")}>
                  <div className="flex items-center gap-1.5">COMMANDER <SortIcon col="commander" /></div>
                </th>
                <th className={thClass} onClick={() => handleSort("location")}>
                  <div className="flex items-center gap-1.5">LOCATION <SortIcon col="location" /></div>
                </th>
                <th className={thClass} onClick={() => handleSort("startedAt")}>
                  <div className="flex items-center gap-1.5">STARTED <SortIcon col="startedAt" /></div>
                </th>
                <th className={thClass} onClick={() => handleSort("endedAt")}>
                  <div className="flex items-center gap-1.5">ENDED <SortIcon col="endedAt" /></div>
                </th>
                <th className={thClass} onClick={() => handleSort("result")}>
                  <div className="flex items-center gap-1.5">RESULT <SortIcon col="result" /></div>
                </th>
                <th className={thClass} onClick={() => handleSort("droneCount")}>
                  <div className="flex items-center gap-1.5">DRONES <SortIcon col="droneCount" /></div>
                </th>
                <th className="px-4 py-3 text-left text-[10px] font-mono font-medium tracking-widest text-[#8A94A6]">ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {pageData.length === 0 ? (
                <tr>
                  <td colSpan={9}>
                    <div className="flex flex-col items-center justify-center py-16 gap-3">
                      <AlertTriangle size={24} color="#8A94A6" />
                      <div className="text-[13px] font-mono text-[#8A94A6]">No missions match your filters</div>
                    </div>
                  </td>
                </tr>
              ) : (
                pageData.map((mission, i) => {
                  const isSelected = selected === mission.id;
                  return (
                    <tr
                      key={mission.id}
                      onClick={() => setSelected(isSelected ? null : mission.id)}
                      className="cursor-pointer transition-colors duration-100"
                      style={{
                        background: isSelected
                          ? "rgba(200,162,74,0.08)"
                          : i % 2 === 0
                          ? "#161D26"
                          : "#131920",
                        borderBottom: "1px solid rgba(255,255,255,0.04)",
                      }}
                      onMouseEnter={e => {
                        if (!isSelected) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)";
                      }}
                      onMouseLeave={e => {
                        if (!isSelected) (e.currentTarget as HTMLElement).style.background = i % 2 === 0 ? "#161D26" : "#131920";
                      }}
                    >
                      <td className="px-4 py-3">
                        <div>
                          <div className="text-[10px] font-mono text-[#8A94A6]">{mission.id}</div>
                          <div className="text-[13px] font-semibold text-[#E6EAF0] tracking-wide">{mission.title}</div>
                        </div>
                      </td>
                      <td className="px-4 py-3"><StatusPill status={mission.status} /></td>
                      <td className="px-4 py-3 text-[12px] font-mono text-[#8A94A6] whitespace-nowrap">{mission.commander}</td>
                      <td className="px-4 py-3 text-[11px] font-mono text-[#8A94A6] whitespace-nowrap">{mission.location}</td>
                      <td className="px-4 py-3 text-[11px] font-mono text-[#8A94A6] whitespace-nowrap">{mission.startedAt ?? "—"}</td>
                      <td className="px-4 py-3 text-[11px] font-mono text-[#8A94A6] whitespace-nowrap">{mission.endedAt ?? "—"}</td>
                      <td className="px-4 py-3"><ResultPill result={mission.result} /></td>
                      <td className="px-4 py-3 text-[12px] font-mono text-[#8A94A6]">
                        <span className="flex items-center gap-1"><Navigation size={10} />{mission.droneCount}</span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={e => { e.stopPropagation(); onView(mission); }}
                            className="flex items-center gap-1 px-2.5 py-1.5 rounded text-[11px] font-mono text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/5 transition-all"
                          >
                            <Eye size={11} /> View
                          </button>
                          <button
                            onClick={e => { e.stopPropagation(); onEdit(mission); }}
                            className="flex items-center gap-1 px-2.5 py-1.5 rounded text-[11px] font-mono text-[#8A94A6] hover:text-[#C8A24A] hover:bg-[rgba(200,162,74,0.08)] transition-all"
                          >
                            <Pencil size={11} /> Edit
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-mono text-[#8A94A6]">
          {missions.length === 0 ? "0 missions" : `${(page - 1) * perPage + 1}–${Math.min(page * perPage, sorted.length)} of ${sorted.length} missions`}
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="w-8 h-8 rounded flex items-center justify-center text-[#8A94A6] disabled:opacity-30 hover:text-[#E6EAF0] hover:bg-white/5 transition-all"
          >
            <ChevronLeft size={14} />
          </button>
          {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
            <button
              key={p}
              onClick={() => setPage(p)}
              className="w-8 h-8 rounded text-[12px] font-mono transition-all"
              style={{
                background: p === page ? "rgba(200,162,74,0.15)" : "transparent",
                color: p === page ? "#C8A24A" : "#8A94A6",
                border: p === page ? "1px solid rgba(200,162,74,0.3)" : "1px solid transparent",
              }}
            >
              {p}
            </button>
          ))}
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="w-8 h-8 rounded flex items-center justify-center text-[#8A94A6] disabled:opacity-30 hover:text-[#E6EAF0] hover:bg-white/5 transition-all"
          >
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── New / Edit Mission Modal ──────────────────────────────────────────────────

interface ModalProps {
  mission?: Mission | null;
  onClose: () => void;
  onCreate: (m: Partial<Mission>) => void;
}

function MissionModal({ mission, onClose, onCreate }: ModalProps) {
  const isEdit = !!mission;
  const [form, setForm] = useState({
    title: mission?.title ?? "",
    commander: mission?.commander ?? "",
    location: mission?.location ?? "",
    lat: "-23.5489",
    lng: "46.6388",
    notes: mission?.notes ?? "",
  });

  const inputClass =
    "w-full px-3 py-2.5 rounded-lg text-[13px] font-mono text-[#E6EAF0] placeholder-[#8A94A6] outline-none focus:ring-1 focus:ring-[#C8A24A]/40 transition-all";
  const inputStyle = {
    background: "#1A2230",
    border: "1px solid rgba(255,255,255,0.1)",
  };
  const labelClass = "text-[10px] font-mono font-medium tracking-widest text-[#8A94A6] mb-1.5 block";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(4px)" }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className="w-full max-w-xl mx-4 rounded-2xl flex flex-col max-h-[90vh]"
        style={{
          background: "#161D26",
          border: "1px solid rgba(255,255,255,0.1)",
          boxShadow: "0 24px 80px rgba(0,0,0,0.6)",
        }}
      >
        {/* Modal header */}
        <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: "rgba(255,255,255,0.08)" }}>
          <div>
            <div className="text-[10px] font-mono text-[#8A94A6] tracking-widest mb-0.5">
              {isEdit ? "EDIT MISSION" : "NEW MISSION"}
            </div>
            <div className="text-[16px] font-semibold text-[#E6EAF0]">
              {isEdit ? mission!.title : "Create Mission Brief"}
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/5 transition-all"
          >
            <X size={16} />
          </button>
        </div>

        {/* Form */}
        <div className="flex-1 overflow-y-auto px-6 py-5 flex flex-col gap-4">
          {/* Title */}
          <div>
            <label className={labelClass}>MISSION TITLE</label>
            <input
              type="text"
              className={inputClass}
              style={inputStyle}
              placeholder="e.g. OPERATION SILENT WATCH"
              value={form.title}
              onChange={e => setForm({ ...form, title: e.target.value })}
            />
          </div>

          {/* Commander */}
          <div>
            <label className={labelClass}>COMMANDING OFFICER</label>
            <select
              className={inputClass}
              style={{ ...inputStyle, cursor: "pointer" }}
              value={form.commander}
              onChange={e => setForm({ ...form, commander: e.target.value })}
            >
              <option value="">Select commander…</option>
              {COMMANDERS.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          {/* Location */}
          <div>
            <label className={labelClass}>LOCATION DESCRIPTION</label>
            <input
              type="text"
              className={inputClass}
              style={inputStyle}
              placeholder="e.g. Grid 44T NV 834 621"
              value={form.location}
              onChange={e => setForm({ ...form, location: e.target.value })}
            />
          </div>

          {/* Lat/Lng */}
          <div>
            <label className={labelClass}>COORDINATES</label>
            <div className="flex gap-2">
              <div className="flex-1">
                <input
                  type="text"
                  className={inputClass}
                  style={inputStyle}
                  placeholder="Latitude"
                  value={form.lat}
                  onChange={e => setForm({ ...form, lat: e.target.value })}
                />
              </div>
              <div className="flex-1">
                <input
                  type="text"
                  className={inputClass}
                  style={inputStyle}
                  placeholder="Longitude"
                  value={form.lng}
                  onChange={e => setForm({ ...form, lng: e.target.value })}
                />
              </div>
            </div>
          </div>

          {/* Map Picker placeholder */}
          <div>
            <label className={labelClass}>MAP PICKER</label>
            <div
              className="relative rounded-xl overflow-hidden"
              style={{
                height: "200px",
                background: "#0F1621",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              {/* Grid overlay to simulate map */}
              <svg className="absolute inset-0 w-full h-full opacity-20" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
                    <path d="M 32 0 L 0 0 0 32" fill="none" stroke="#4C8DFF" strokeWidth="0.5" />
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" />
              </svg>
              {/* Topographic contour lines */}
              <svg className="absolute inset-0 w-full h-full opacity-10" xmlns="http://www.w3.org/2000/svg">
                <ellipse cx="50%" cy="50%" rx="60" ry="40" fill="none" stroke="#4C8DFF" strokeWidth="1" />
                <ellipse cx="50%" cy="50%" rx="90" ry="65" fill="none" stroke="#4C8DFF" strokeWidth="0.7" />
                <ellipse cx="50%" cy="50%" rx="120" ry="90" fill="none" stroke="#4C8DFF" strokeWidth="0.5" />
              </svg>
              {/* Crosshair / pin */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="relative">
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-px h-6 bg-[#C8A24A] opacity-60" />
                  <div className="absolute top-3 left-1/2 -translate-x-1/2 w-px h-6 bg-[#C8A24A] opacity-60" />
                  <div className="absolute top-1/2 -left-3 -translate-y-1/2 h-px w-6 bg-[#C8A24A] opacity-60" />
                  <div className="absolute top-1/2 left-3 -translate-y-1/2 h-px w-6 bg-[#C8A24A] opacity-60" />
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ background: "#C8A24A", boxShadow: "0 0 12px rgba(200,162,74,0.8)" }}
                  />
                </div>
              </div>
              {/* Coordinates display */}
              <div
                className="absolute bottom-3 left-3 text-[10px] font-mono px-2 py-1 rounded"
                style={{ background: "rgba(0,0,0,0.6)", color: "#C8A24A" }}
              >
                {form.lat}° N · {form.lng}° E
              </div>
              <div
                className="absolute top-3 right-3 text-[10px] font-mono px-2 py-1 rounded flex items-center gap-1"
                style={{ background: "rgba(0,0,0,0.5)", color: "#8A94A6" }}
              >
                <MapPin size={9} /> Click to set position
              </div>
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className={labelClass}>OPERATIONAL NOTES</label>
            <textarea
              rows={3}
              className={inputClass}
              style={{ ...inputStyle, resize: "vertical" }}
              placeholder="Mission objectives, ROE, special instructions…"
              value={form.notes}
              onChange={e => setForm({ ...form, notes: e.target.value })}
            />
          </div>
        </div>

        {/* Footer */}
        <div
          className="flex items-center justify-end gap-3 px-6 py-4 border-t"
          style={{ borderColor: "rgba(255,255,255,0.08)" }}
        >
          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-lg text-[13px] font-mono text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/5 transition-all"
          >
            Cancel
          </button>
          <button
            onClick={() => { onCreate(form); onClose(); }}
            className="px-5 py-2.5 rounded-lg text-[13px] font-mono font-semibold transition-all"
            style={{
              background: "#C8A24A",
              color: "#0B0F14",
            }}
            onMouseEnter={e => ((e.currentTarget as HTMLElement).style.background = "#d4af5e")}
            onMouseLeave={e => ((e.currentTarget as HTMLElement).style.background = "#C8A24A")}
          >
            {isEdit ? "Save Changes" : "Create Mission"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Mission Detail Drawer ─────────────────────────────────────────────────────

function MissionDetailDrawer({ mission, onClose, onEdit }: { mission: Mission; onClose: () => void; onEdit: () => void }) {
  const statusM = STATUS_META[mission.status];
  return (
    <div
      className="fixed inset-0 z-40 flex"
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
      style={{ background: "rgba(0,0,0,0.5)" }}
    >
      <div
        className="ml-auto h-full w-full max-w-md flex flex-col"
        style={{
          background: "#161D26",
          borderLeft: "1px solid rgba(255,255,255,0.09)",
          boxShadow: "-16px 0 48px rgba(0,0,0,0.5)",
        }}
      >
        {/* Header */}
        <div
          className="px-6 py-5 border-b"
          style={{ borderColor: "rgba(255,255,255,0.07)", borderLeft: `3px solid ${statusM.color}` }}
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-[10px] font-mono text-[#8A94A6] tracking-widest mb-1">{mission.id}</div>
              <div className="text-[17px] font-bold text-[#E6EAF0] tracking-wide leading-tight">{mission.title}</div>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <button
                onClick={onEdit}
                className="px-3 py-1.5 rounded-lg text-[11px] font-mono text-[#C8A24A] hover:bg-[rgba(200,162,74,0.1)] transition-all"
                style={{ border: "1px solid rgba(200,162,74,0.3)" }}
              >
                Edit
              </button>
              <button
                onClick={onClose}
                className="w-7 h-7 rounded-lg flex items-center justify-center text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/5 transition-all"
              >
                <X size={14} />
              </button>
            </div>
          </div>
          <div className="flex items-center gap-2 mt-3">
            <StatusPill status={mission.status} />
            {mission.result && <ResultPill result={mission.result} />}
          </div>
        </div>

        {/* Details */}
        <div className="flex-1 overflow-y-auto px-6 py-5 flex flex-col gap-5">
          {[
            { label: "COMMANDER", value: mission.commander, icon: Users },
            { label: "LOCATION", value: mission.location, icon: MapPin },
            { label: "STARTED", value: mission.startedAt ?? "Not started", icon: Clock },
            { label: "ENDED", value: mission.endedAt ?? "Ongoing", icon: Clock },
          ].map(({ label, value, icon: Icon }) => (
            <div key={label}>
              <div className="text-[9px] font-mono tracking-widest text-[#8A94A6] mb-1">{label}</div>
              <div className="flex items-center gap-1.5 text-[13px] font-mono text-[#E6EAF0]">
                <Icon size={12} className="text-[#8A94A6]" />
                {value}
              </div>
            </div>
          ))}

          {/* Assets */}
          <div>
            <div className="text-[9px] font-mono tracking-widest text-[#8A94A6] mb-2">ASSETS</div>
            <div className="flex gap-3">
              <div
                className="flex-1 rounded-lg px-3 py-3 flex items-center gap-2"
                style={{ background: "#1A2230", border: "1px solid rgba(255,255,255,0.06)" }}
              >
                <Navigation size={14} color="#C8A24A" />
                <div>
                  <div className="text-[18px] font-bold text-[#E6EAF0]">{mission.droneCount}</div>
                  <div className="text-[9px] font-mono text-[#8A94A6] tracking-widest">DRONES</div>
                </div>
              </div>
              <div
                className="flex-1 rounded-lg px-3 py-3 flex items-center gap-2"
                style={{ background: "#1A2230", border: "1px solid rgba(255,255,255,0.06)" }}
              >
                <Users size={14} color="#C8A24A" />
                <div>
                  <div className="text-[18px] font-bold text-[#E6EAF0]">{mission.operatorCount}</div>
                  <div className="text-[9px] font-mono text-[#8A94A6] tracking-widest">OPERATORS</div>
                </div>
              </div>
            </div>
          </div>

          {/* Notes */}
          {mission.notes && (
            <div>
              <div className="text-[9px] font-mono tracking-widest text-[#8A94A6] mb-2">OPERATIONAL NOTES</div>
              <div
                className="rounded-lg px-4 py-3 text-[13px] font-mono text-[#8A94A6] leading-relaxed"
                style={{ background: "#1A2230", border: "1px solid rgba(255,255,255,0.06)" }}
              >
                {mission.notes}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Loading Skeleton ─────────────────────────────────────────────────────────

function Skeleton() {
  return (
    <div className="animate-pulse flex flex-col gap-3">
      {[1, 2, 3].map(i => (
        <div key={i} className="rounded-xl p-4" style={{ background: "#161D26", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="flex justify-between mb-3">
            <div className="h-2 w-16 rounded" style={{ background: "rgba(255,255,255,0.07)" }} />
            <div className="h-4 w-16 rounded-full" style={{ background: "rgba(255,255,255,0.07)" }} />
          </div>
          <div className="h-3 w-3/4 rounded mb-2" style={{ background: "rgba(255,255,255,0.07)" }} />
          <div className="h-2 w-1/2 rounded" style={{ background: "rgba(255,255,255,0.05)" }} />
        </div>
      ))}
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────

export default function App() {
  const [view, setView] = useState<View>("board");
  const [filters, setFilters] = useState<Filters>({ search: "", status: "", commander: "", result: "" });
  const [modalOpen, setModalOpen] = useState(false);
  const [editMission, setEditMission] = useState<Mission | null>(null);
  const [detailMission, setDetailMission] = useState<Mission | null>(null);
  const [missions, setMissions] = useState<Mission[]>(MISSIONS);
  const [loading] = useState(false);

  // Derive active filter chips
  const chips: Chip[] = useMemo(() => {
    const c: Chip[] = [];
    if (filters.search) c.push({ key: "search", label: `"${filters.search}"` });
    if (filters.status) c.push({ key: "status", label: `Status: ${filters.status}` });
    if (filters.commander) c.push({ key: "commander", label: `Cmdr: ${filters.commander.split(" ").slice(-1)[0]}` });
    if (filters.result) c.push({ key: "result", label: `Result: ${filters.result}` });
    return c;
  }, [filters]);

  function removeChip(key: string) {
    setFilters(f => ({ ...f, [key]: "" }));
  }

  // Filtered missions
  const filtered = useMemo(() => {
    return missions.filter(m => {
      const q = filters.search.toLowerCase();
      if (q && !m.title.toLowerCase().includes(q) && !m.location.toLowerCase().includes(q)) return false;
      if (filters.status && m.status !== filters.status) return false;
      if (filters.commander && m.commander !== filters.commander) return false;
      if (filters.result && m.result !== filters.result) return false;
      return true;
    });
  }, [missions, filters]);

  const totalCount = missions.length;

  function handleCreate(data: Partial<Mission>) {
    const newM: Mission = {
      id: `MSN-${String(missions.length + 1).padStart(3, "0")}`,
      title: data.title?.toUpperCase() ?? "UNTITLED MISSION",
      status: "Planned",
      commander: (data as any).commander ?? "",
      location: (data as any).location ?? "",
      startedAt: null,
      endedAt: null,
      result: null,
      droneCount: 0,
      operatorCount: 0,
      notes: (data as any).notes ?? "",
    };
    setMissions(ms => [newM, ...ms]);
  }

  const STATUSES: Status[] = ["Planned", "Active", "Completed", "Aborted"];

  return (
    <div
      className="flex h-screen w-screen overflow-hidden font-[Inter,sans-serif]"
      style={{ background: "#0B0F14" }}
    >
      <Sidebar />

      <div className="flex flex-col flex-1 min-w-0">
        <TopBar />

        {/* Page content */}
        <main className="flex-1 overflow-auto px-6 py-5">
          {/* Page header */}
          <div className="flex items-center justify-between mb-5 gap-4 flex-wrap">
            <div className="flex items-center gap-3">
              <div>
                <h1 className="text-[22px] font-bold text-[#E6EAF0] tracking-wide leading-none">
                  Missions
                </h1>
                <div className="text-[11px] font-mono text-[#8A94A6] mt-1 tracking-wide">
                  {totalCount} total · {missions.filter(m => m.status === "Active").length} active
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* View toggle */}
              <div
                className="flex items-center rounded-lg p-1"
                style={{ background: "#161D26", border: "1px solid rgba(255,255,255,0.08)" }}
              >
                {(["board", "list"] as const).map(v => (
                  <button
                    key={v}
                    onClick={() => setView(v)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[12px] font-mono transition-all duration-150"
                    style={{
                      background: view === v ? "rgba(200,162,74,0.15)" : "transparent",
                      color: view === v ? "#C8A24A" : "#8A94A6",
                      border: view === v ? "1px solid rgba(200,162,74,0.25)" : "1px solid transparent",
                    }}
                  >
                    {v === "board" ? <LayoutGrid size={13} /> : <List size={13} />}
                    {v === "board" ? "Board" : "List"}
                  </button>
                ))}
              </div>

              {/* New Mission */}
              <button
                onClick={() => { setEditMission(null); setModalOpen(true); }}
                className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-[13px] font-mono font-semibold transition-all"
                style={{ background: "#C8A24A", color: "#0B0F14" }}
                onMouseEnter={e => ((e.currentTarget as HTMLElement).style.background = "#d4af5e")}
                onMouseLeave={e => ((e.currentTarget as HTMLElement).style.background = "#C8A24A")}
              >
                <Plus size={14} strokeWidth={2.5} />
                New Mission
              </button>
            </div>
          </div>

          {/* Filter bar */}
          <div className="mb-5">
            <FilterBar filters={filters} setFilters={setFilters} chips={chips} removeChip={removeChip} />
          </div>

          {/* Content */}
          {loading ? (
            <div className="grid grid-cols-4 gap-4">
              {STATUSES.map(s => <Skeleton key={s} />)}
            </div>
          ) : view === "board" ? (
            <div className="flex gap-4 overflow-x-auto pb-4">
              {STATUSES.map(status => (
                <KanbanColumn
                  key={status}
                  status={status}
                  missions={filtered.filter(m => m.status === status)}
                  onCardClick={m => setDetailMission(m)}
                />
              ))}
            </div>
          ) : (
            <DataTable
              missions={filtered}
              onView={m => setDetailMission(m)}
              onEdit={m => { setEditMission(m); setModalOpen(true); }}
            />
          )}
        </main>
      </div>

      {/* Modals & drawers */}
      {modalOpen && (
        <MissionModal
          mission={editMission}
          onClose={() => setModalOpen(false)}
          onCreate={handleCreate}
        />
      )}
      {detailMission && (
        <MissionDetailDrawer
          mission={detailMission}
          onClose={() => setDetailMission(null)}
          onEdit={() => { setEditMission(detailMission); setDetailMission(null); setModalOpen(true); }}
        />
      )}
    </div>
  );
}
