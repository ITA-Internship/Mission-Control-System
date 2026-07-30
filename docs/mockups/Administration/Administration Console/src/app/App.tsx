import { useState, useCallback } from "react";
import {
  Shield,
  Users,
  Building2,
  ScrollText,
  Drone,
  Settings,
  ChevronDown,
  Search,
  X,
  Plus,
  Download,
  ChevronUp,
  ChevronsUpDown,
  MoreHorizontal,
  Check,
  AlertTriangle,
  Edit3,
  ToggleLeft,
  ToggleRight,
  Bell,
  LogOut,
  Home,
  Map,
  Activity,
  Cpu,
  Filter,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

type Role = "Admin" | "Commander" | "Dispatcher" | "Operator" | "Technician" | "Viewer";
type UserStatus = "Active" | "Inactive";
type ResultStatus = "Success" | "Failure";
type Tab = "Users" | "Military Units" | "Audit Log";
type SortDir = "asc" | "desc" | null;

interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  unit: string;
  status: UserStatus;
  createdBy: string;
  lastLogin: string;
}

interface Unit {
  id: string;
  name: string;
  code: string;
  description: string;
  active: boolean;
  drones: number;
  users: number;
}

interface AuditEntry {
  id: string;
  actionType: string;
  actor: string;
  target: string;
  result: ResultStatus;
  ip: string;
  userAgent: string;
  timestamp: string;
}

// ─── Seed Data ────────────────────────────────────────────────────────────────

const SEED_USERS: User[] = [
  { id: "u1", name: "Col. Marcus Hale", email: "m.hale@mcs.mil", role: "Admin", unit: "1st AIR BDE", status: "Active", createdBy: "system", lastLogin: "2026-07-30 08:14" },
  { id: "u2", name: "Maj. Diana Voss", email: "d.voss@mcs.mil", role: "Commander", unit: "1st AIR BDE", status: "Active", createdBy: "m.hale", lastLogin: "2026-07-30 07:42" },
  { id: "u3", name: "Cpt. Leon Reyes", email: "l.reyes@mcs.mil", role: "Dispatcher", unit: "3rd RECON SQN", status: "Active", createdBy: "d.voss", lastLogin: "2026-07-29 22:05" },
  { id: "u4", name: "Sgt. Priya Nair", email: "p.nair@mcs.mil", role: "Operator", unit: "3rd RECON SQN", status: "Active", createdBy: "l.reyes", lastLogin: "2026-07-30 06:30" },
  { id: "u5", name: "Tech. Omar Fadel", email: "o.fadel@mcs.mil", role: "Technician", unit: "MAINT PLT", status: "Active", createdBy: "m.hale", lastLogin: "2026-07-28 14:20" },
  { id: "u6", name: "PFC. Anya Sorel", email: "a.sorel@mcs.mil", role: "Viewer", unit: "HQ STAFF", status: "Inactive", createdBy: "m.hale", lastLogin: "2026-07-10 09:11" },
  { id: "u7", name: "WO1 Takeshi Mori", email: "t.mori@mcs.mil", role: "Operator", unit: "2nd STRIKE SQN", status: "Active", createdBy: "d.voss", lastLogin: "2026-07-30 05:58" },
  { id: "u8", name: "Cpt. Sara Okonkwo", email: "s.okonkwo@mcs.mil", role: "Commander", unit: "2nd STRIKE SQN", status: "Active", createdBy: "m.hale", lastLogin: "2026-07-29 18:47" },
  { id: "u9", name: "Spc. Ben Larkin", email: "b.larkin@mcs.mil", role: "Dispatcher", unit: "HQ STAFF", status: "Inactive", createdBy: "d.voss", lastLogin: "2026-06-14 11:00" },
];

const SEED_UNITS: Unit[] = [
  { id: "un1", name: "1st Air Brigade", code: "1ST-AIR-BDE", description: "Primary aerial strike and reconnaissance brigade.", active: true, drones: 24, users: 18 },
  { id: "un2", name: "2nd Strike Squadron", code: "2ND-STRIKE-SQN", description: "Precision strike mission squadron.", active: true, drones: 12, users: 9 },
  { id: "un3", name: "3rd Recon Squadron", code: "3RD-RECON-SQN", description: "Long-range intelligence and surveillance ops.", active: true, drones: 8, users: 7 },
  { id: "un4", name: "Maintenance Platoon", code: "MAINT-PLT", description: "Fleet servicing and technical support unit.", active: true, drones: 0, users: 4 },
  { id: "un5", name: "HQ Staff", code: "HQ-STAFF", description: "Command and administrative staff element.", active: true, drones: 0, users: 6 },
  { id: "un6", name: "4th Logistics Squadron", code: "4TH-LOG-SQN", description: "Supply chain and operational logistics.", active: false, drones: 2, users: 3 },
];

const SEED_AUDIT: AuditEntry[] = [
  { id: "a1", actionType: "USER_LOGIN", actor: "m.hale@mcs.mil", target: "—", result: "Success", ip: "10.20.1.42", userAgent: "Chrome/126 Win10", timestamp: "2026-07-30 08:14:02" },
  { id: "a2", actionType: "ROLE_CHANGED", actor: "m.hale@mcs.mil", target: "l.reyes@mcs.mil", result: "Success", ip: "10.20.1.42", userAgent: "Chrome/126 Win10", timestamp: "2026-07-30 08:10:11" },
  { id: "a3", actionType: "USER_DEACTIVATED", actor: "m.hale@mcs.mil", target: "a.sorel@mcs.mil", result: "Success", ip: "10.20.1.42", userAgent: "Chrome/126 Win10", timestamp: "2026-07-30 08:08:44" },
  { id: "a4", actionType: "USER_CREATED", actor: "d.voss@mcs.mil", target: "t.mori@mcs.mil", result: "Success", ip: "10.20.4.11", userAgent: "Firefox/127 macOS", timestamp: "2026-07-29 18:50:33" },
  { id: "a5", actionType: "USER_LOGIN", actor: "b.larkin@mcs.mil", target: "—", result: "Failure", ip: "203.0.113.7", userAgent: "curl/7.88.1", timestamp: "2026-07-29 14:22:05" },
  { id: "a6", actionType: "UNIT_CREATED", actor: "m.hale@mcs.mil", target: "4TH-LOG-SQN", result: "Success", ip: "10.20.1.42", userAgent: "Chrome/126 Win10", timestamp: "2026-07-28 10:05:18" },
  { id: "a7", actionType: "USER_LOGIN", actor: "o.fadel@mcs.mil", target: "—", result: "Success", ip: "10.20.8.3", userAgent: "Safari/17 iOS", timestamp: "2026-07-28 14:20:01" },
  { id: "a8", actionType: "USER_ACTIVATED", actor: "m.hale@mcs.mil", target: "p.nair@mcs.mil", result: "Success", ip: "10.20.1.42", userAgent: "Chrome/126 Win10", timestamp: "2026-07-27 09:33:40" },
  { id: "a9", actionType: "EXPORT_CSV", actor: "d.voss@mcs.mil", target: "audit-log", result: "Success", ip: "10.20.4.11", userAgent: "Firefox/127 macOS", timestamp: "2026-07-26 16:11:22" },
  { id: "a10", actionType: "USER_LOGIN", actor: "s.okonkwo@mcs.mil", target: "—", result: "Success", ip: "10.20.6.55", userAgent: "Chrome/126 Linux", timestamp: "2026-07-29 18:47:00" },
  { id: "a11", actionType: "UNIT_DEACTIVATED", actor: "m.hale@mcs.mil", target: "4TH-LOG-SQN", result: "Success", ip: "10.20.1.42", userAgent: "Chrome/126 Win10", timestamp: "2026-07-25 11:20:05" },
  { id: "a12", actionType: "ROLE_CHANGED", actor: "m.hale@mcs.mil", target: "a.sorel@mcs.mil", result: "Failure", ip: "10.20.1.42", userAgent: "Chrome/126 Win10", timestamp: "2026-07-24 13:45:11" },
];

const ROLES: Role[] = ["Admin", "Commander", "Dispatcher", "Operator", "Technician", "Viewer"];
const UNITS_LIST = ["All Units", "1st AIR BDE", "2nd STRIKE SQN", "3rd RECON SQN", "MAINT PLT", "HQ STAFF"];
const AUDIT_ACTION_TYPES = ["All Actions", "USER_LOGIN", "USER_CREATED", "USER_ACTIVATED", "USER_DEACTIVATED", "ROLE_CHANGED", "UNIT_CREATED", "UNIT_DEACTIVATED", "EXPORT_CSV"];

// ─── Style Helpers ────────────────────────────────────────────────────────────

const roleBadge: Record<Role, { bg: string; text: string; border: string }> = {
  Admin:       { bg: "rgba(200,162,74,0.15)",  text: "#C8A24A", border: "rgba(200,162,74,0.35)" },
  Commander:   { bg: "rgba(76,141,255,0.15)",  text: "#4C8DFF", border: "rgba(76,141,255,0.35)" },
  Dispatcher:  { bg: "rgba(45,212,191,0.15)",  text: "#2DD4BF", border: "rgba(45,212,191,0.35)" },
  Operator:    { bg: "rgba(63,185,80,0.15)",   text: "#3FB950", border: "rgba(63,185,80,0.35)" },
  Technician:  { bg: "rgba(240,136,62,0.15)",  text: "#F0883E", border: "rgba(240,136,62,0.35)" },
  Viewer:      { bg: "rgba(138,148,166,0.15)", text: "#8A94A6", border: "rgba(138,148,166,0.35)" },
};

const auditActionStyle: Record<string, { bg: string; text: string }> = {
  USER_LOGIN:       { bg: "rgba(76,141,255,0.12)",  text: "#4C8DFF" },
  USER_CREATED:     { bg: "rgba(63,185,80,0.12)",   text: "#3FB950" },
  USER_ACTIVATED:   { bg: "rgba(63,185,80,0.12)",   text: "#3FB950" },
  USER_DEACTIVATED: { bg: "rgba(229,72,77,0.12)",   text: "#E5484D" },
  ROLE_CHANGED:     { bg: "rgba(200,162,74,0.12)",  text: "#C8A24A" },
  UNIT_CREATED:     { bg: "rgba(45,212,191,0.12)",  text: "#2DD4BF" },
  UNIT_DEACTIVATED: { bg: "rgba(229,72,77,0.12)",   text: "#E5484D" },
  EXPORT_CSV:       { bg: "rgba(138,148,166,0.12)", text: "#8A94A6" },
};

function RoleBadge({ role }: { role: Role }) {
  const s = roleBadge[role];
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold tracking-wide border"
      style={{ background: s.bg, color: s.text, borderColor: s.border }}
    >
      {role.toUpperCase()}
    </span>
  );
}

function StatusPill({ status }: { status: UserStatus | "Active" | "Inactive" }) {
  const active = status === "Active";
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold"
      style={{
        background: active ? "rgba(63,185,80,0.12)" : "rgba(138,148,166,0.12)",
        color: active ? "#3FB950" : "#8A94A6",
      }}
    >
      <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ background: active ? "#3FB950" : "#8A94A6" }} />
      {status}
    </span>
  );
}

function ResultPill({ result }: { result: ResultStatus }) {
  const ok = result === "Success";
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold"
      style={{
        background: ok ? "rgba(63,185,80,0.12)" : "rgba(229,72,77,0.12)",
        color: ok ? "#3FB950" : "#E5484D",
      }}
    >
      <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ background: ok ? "#3FB950" : "#E5484D" }} />
      {result}
    </span>
  );
}

function AuditActionPill({ type }: { type: string }) {
  const s = auditActionStyle[type] ?? { bg: "rgba(138,148,166,0.12)", text: "#8A94A6" };
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-medium tracking-wider"
      style={{ background: s.bg, color: s.text }}
    >
      {type}
    </span>
  );
}

// ─── Sort Helper ──────────────────────────────────────────────────────────────

function SortIcon({ dir }: { dir: SortDir }) {
  if (dir === "asc") return <ChevronUp className="w-3 h-3 inline ml-1" style={{ color: "#C8A24A" }} />;
  if (dir === "desc") return <ChevronDown className="w-3 h-3 inline ml-1" style={{ color: "#C8A24A" }} />;
  return <ChevronsUpDown className="w-3 h-3 inline ml-1 opacity-30" />;
}

function ThCell({ label, col, sortCol, sortDir, onSort }: { label: string; col: string; sortCol: string; sortDir: SortDir; onSort: (c: string) => void }) {
  const active = sortCol === col;
  return (
    <th
      className="px-4 py-2.5 text-left text-[11px] font-semibold uppercase tracking-widest cursor-pointer select-none whitespace-nowrap"
      style={{ color: active ? "#C8A24A" : "#8A94A6" }}
      onClick={() => onSort(col)}
    >
      {label}
      <SortIcon dir={active ? sortDir : null} />
    </th>
  );
}

// ─── Input / Select Components ────────────────────────────────────────────────

function Input({ label, value, onChange, placeholder, type = "text" }: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string; type?: string;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[11px] font-semibold uppercase tracking-widest" style={{ color: "#8A94A6" }}>{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="h-9 px-3 rounded-lg text-sm outline-none transition-all"
        style={{
          background: "#0E1420",
          border: "1px solid rgba(255,255,255,0.1)",
          color: "#E6EAF0",
        }}
      />
    </div>
  );
}

function Select({ label, value, onChange, options }: {
  label: string; value: string; onChange: (v: string) => void; options: string[];
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[11px] font-semibold uppercase tracking-widest" style={{ color: "#8A94A6" }}>{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="h-9 px-3 rounded-lg text-sm outline-none appearance-none cursor-pointer"
        style={{
          background: "#0E1420",
          border: "1px solid rgba(255,255,255,0.1)",
          color: value ? "#E6EAF0" : "#8A94A6",
        }}
      >
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}

// ─── Modal Shell ──────────────────────────────────────────────────────────────

function Modal({ title, onClose, children, width = "max-w-lg" }: {
  title: string; onClose: () => void; children: React.ReactNode; width?: string;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: "rgba(0,0,0,0.72)" }}>
      <div className={`${width} w-full rounded-xl border shadow-2xl`} style={{ background: "#161D26", borderColor: "rgba(255,255,255,0.1)" }}>
        <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: "rgba(255,255,255,0.08)" }}>
          <h2 className="text-base font-semibold" style={{ color: "#E6EAF0" }}>{title}</h2>
          <button onClick={onClose} className="rounded-lg p-1 hover:bg-white/5 transition-colors" style={{ color: "#8A94A6" }}>
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="px-6 py-5">{children}</div>
      </div>
    </div>
  );
}

// ─── Pagination ────────────────────────────────────────────────────────────────

function Pagination({ page, total, perPage, onChange }: { page: number; total: number; perPage: number; onChange: (p: number) => void }) {
  const pages = Math.ceil(total / perPage);
  if (pages <= 1) return null;
  return (
    <div className="flex items-center justify-between px-4 py-3 border-t" style={{ borderColor: "rgba(255,255,255,0.07)" }}>
      <span className="text-xs" style={{ color: "#8A94A6" }}>
        Showing {(page - 1) * perPage + 1}–{Math.min(page * perPage, total)} of {total}
      </span>
      <div className="flex items-center gap-1">
        <button
          onClick={() => onChange(page - 1)}
          disabled={page === 1}
          className="p-1.5 rounded hover:bg-white/5 disabled:opacity-30 transition-colors"
          style={{ color: "#8A94A6" }}
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        {Array.from({ length: pages }, (_, i) => i + 1).map(p => (
          <button
            key={p}
            onClick={() => onChange(p)}
            className="w-7 h-7 rounded text-xs font-medium transition-colors"
            style={{
              background: p === page ? "#C8A24A" : "transparent",
              color: p === page ? "#0B0F14" : "#8A94A6",
            }}
          >
            {p}
          </button>
        ))}
        <button
          onClick={() => onChange(page + 1)}
          disabled={page === pages}
          className="p-1.5 rounded hover:bg-white/5 disabled:opacity-30 transition-colors"
          style={{ color: "#8A94A6" }}
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// ─── Filter Chip ──────────────────────────────────────────────────────────────

function FilterChip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 pl-2.5 pr-1.5 py-0.5 rounded-full text-xs font-medium border"
      style={{ background: "rgba(200,162,74,0.1)", color: "#C8A24A", borderColor: "rgba(200,162,74,0.3)" }}
    >
      {label}
      <button onClick={onRemove} className="hover:opacity-70 transition-opacity"><X className="w-3 h-3" /></button>
    </span>
  );
}

// ─── Search Bar ───────────────────────────────────────────────────────────────

function SearchBar({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <div className="relative flex-1 min-w-48 max-w-72">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 pointer-events-none" style={{ color: "#8A94A6" }} />
      <input
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder ?? "Search…"}
        className="w-full h-9 pl-9 pr-8 rounded-lg text-sm outline-none"
        style={{ background: "#0E1420", border: "1px solid rgba(255,255,255,0.09)", color: "#E6EAF0" }}
      />
      {value && (
        <button onClick={() => onChange("")} className="absolute right-2.5 top-1/2 -translate-y-1/2 hover:opacity-70">
          <X className="w-3 h-3" style={{ color: "#8A94A6" }} />
        </button>
      )}
    </div>
  );
}

function FilterSelect({ value, onChange, options, placeholder }: {
  value: string; onChange: (v: string) => void; options: string[]; placeholder: string;
}) {
  return (
    <div className="relative">
      <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 pointer-events-none" style={{ color: "#8A94A6" }} />
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="h-9 pl-8 pr-8 rounded-lg text-sm outline-none appearance-none cursor-pointer"
        style={{ background: "#0E1420", border: "1px solid rgba(255,255,255,0.09)", color: value ? "#E6EAF0" : "#8A94A6" }}
      >
        <option value="">{placeholder}</option>
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}

// ─── Empty State ──────────────────────────────────────────────────────────────

function EmptyState({ icon: Icon, title, sub }: { icon: React.FC<any>; title: string; sub: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-3">
      <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: "rgba(255,255,255,0.04)" }}>
        <Icon className="w-5 h-5" style={{ color: "#8A94A6" }} />
      </div>
      <p className="text-sm font-semibold" style={{ color: "#E6EAF0" }}>{title}</p>
      <p className="text-xs" style={{ color: "#8A94A6" }}>{sub}</p>
    </div>
  );
}

// ─── Create User Modal ────────────────────────────────────────────────────────

function CreateUserModal({ units, onClose, onSave }: {
  units: Unit[];
  onClose: () => void;
  onSave: (u: User) => void;
}) {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [role, setRole] = useState<Role>("Operator");
  const [unit, setUnit] = useState(units[0]?.code ?? "");

  const handleSave = () => {
    if (!email || !name) return;
    const u: User = {
      id: `u${Date.now()}`, name, email, role, unit,
      status: "Active", createdBy: "m.hale@mcs.mil", lastLogin: "—"
    };
    onSave(u);
    onClose();
  };

  return (
    <Modal title="Create New User" onClose={onClose}>
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <Input label="Full Name" value={name} onChange={setName} placeholder="Rank. Firstname Lastname" />
          <Input label="Email" value={email} onChange={setEmail} placeholder="user@mcs.mil" type="email" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Select label="Role" value={role} onChange={v => setRole(v as Role)} options={ROLES} />
          <Select label="Unit" value={unit} onChange={setUnit} options={units.map(u => u.code)} />
        </div>
        <div className="rounded-lg px-3 py-2.5 text-xs" style={{ background: "rgba(200,162,74,0.08)", color: "#C8A24A", border: "1px solid rgba(200,162,74,0.2)" }}>
          An activation email will be sent to the new user. They must set a password on first login.
        </div>
        <div className="flex justify-end gap-2 pt-1">
          <button onClick={onClose} className="h-9 px-4 rounded-lg text-sm font-medium transition-colors hover:bg-white/5" style={{ color: "#8A94A6", border: "1px solid rgba(255,255,255,0.1)" }}>
            Cancel
          </button>
          <button onClick={handleSave} className="h-9 px-5 rounded-lg text-sm font-semibold transition-colors hover:opacity-90" style={{ background: "#C8A24A", color: "#0B0F14" }}>
            Create &amp; Send Activation
          </button>
        </div>
      </div>
    </Modal>
  );
}

// ─── Change Role Modal ────────────────────────────────────────────────────────

function ChangeRoleModal({ user, onClose, onSave }: { user: User; onClose: () => void; onSave: (role: Role) => void }) {
  const [role, setRole] = useState<Role>(user.role);

  return (
    <Modal title="Change User Role" onClose={onClose}>
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3 p-3 rounded-lg" style={{ background: "rgba(255,255,255,0.04)" }}>
          <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold" style={{ background: "#C8A24A22", color: "#C8A24A" }}>
            {user.name.split(" ").pop()![0]}
          </div>
          <div>
            <p className="text-sm font-semibold" style={{ color: "#E6EAF0" }}>{user.name}</p>
            <p className="text-xs" style={{ color: "#8A94A6" }}>{user.email}</p>
          </div>
          <div className="ml-auto"><RoleBadge role={user.role} /></div>
        </div>
        <Select label="New Role" value={role} onChange={v => setRole(v as Role)} options={ROLES} />
        <div className="rounded-lg px-3 py-2.5 text-xs" style={{ background: "rgba(229,72,77,0.07)", color: "#E5484D", border: "1px solid rgba(229,72,77,0.2)" }}>
          This action will be written to the immutable audit log.
        </div>
        <div className="flex justify-end gap-2 pt-1">
          <button onClick={onClose} className="h-9 px-4 rounded-lg text-sm font-medium hover:bg-white/5 transition-colors" style={{ color: "#8A94A6", border: "1px solid rgba(255,255,255,0.1)" }}>
            Cancel
          </button>
          <button onClick={() => { onSave(role); onClose(); }} className="h-9 px-5 rounded-lg text-sm font-semibold hover:opacity-90 transition-colors" style={{ background: "#C8A24A", color: "#0B0F14" }}>
            Confirm Change
          </button>
        </div>
      </div>
    </Modal>
  );
}

// ─── Activate / Deactivate Confirm Modal ──────────────────────────────────────

function ToggleStatusModal({ user, onClose, onConfirm }: { user: User; onClose: () => void; onConfirm: (reason: string) => void }) {
  const [reason, setReason] = useState("");
  const deactivating = user.status === "Active";

  return (
    <Modal title={deactivating ? "Deactivate User" : "Activate User"} onClose={onClose}>
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3 p-3 rounded-lg" style={{ background: "rgba(255,255,255,0.04)" }}>
          <StatusPill status={user.status} />
          <div>
            <p className="text-sm font-semibold" style={{ color: "#E6EAF0" }}>{user.name}</p>
            <p className="text-xs" style={{ color: "#8A94A6" }}>{user.email}</p>
          </div>
        </div>
        {deactivating && (
          <div className="rounded-lg px-3 py-2.5 text-xs flex items-start gap-2" style={{ background: "rgba(229,72,77,0.07)", color: "#E5484D", border: "1px solid rgba(229,72,77,0.2)" }}>
            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
            Deactivating this user will immediately revoke all system access. They will not be able to log in.
          </div>
        )}
        <div className="flex flex-col gap-1">
          <label className="text-[11px] font-semibold uppercase tracking-widest" style={{ color: "#8A94A6" }}>Reason (required for audit log)</label>
          <textarea
            value={reason}
            onChange={e => setReason(e.target.value)}
            rows={2}
            placeholder="Provide a reason for this action…"
            className="px-3 py-2 rounded-lg text-sm resize-none outline-none"
            style={{ background: "#0E1420", border: "1px solid rgba(255,255,255,0.1)", color: "#E6EAF0" }}
          />
        </div>
        <div className="flex justify-end gap-2 pt-1">
          <button onClick={onClose} className="h-9 px-4 rounded-lg text-sm font-medium hover:bg-white/5 transition-colors" style={{ color: "#8A94A6", border: "1px solid rgba(255,255,255,0.1)" }}>
            Cancel
          </button>
          <button
            onClick={() => { if (reason.trim()) { onConfirm(reason); onClose(); } }}
            disabled={!reason.trim()}
            className="h-9 px-5 rounded-lg text-sm font-semibold transition-colors disabled:opacity-40"
            style={{ background: deactivating ? "#E5484D" : "#3FB950", color: "#ffffff" }}
          >
            {deactivating ? "Deactivate" : "Activate"}
          </button>
        </div>
      </div>
    </Modal>
  );
}

// ─── Add Unit Modal ───────────────────────────────────────────────────────────

function AddUnitModal({ onClose, onSave }: { onClose: () => void; onSave: (u: Unit) => void }) {
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [desc, setDesc] = useState("");

  const handleSave = () => {
    if (!name || !code) return;
    onSave({ id: `un${Date.now()}`, name, code: code.toUpperCase(), description: desc, active: true, drones: 0, users: 0 });
    onClose();
  };

  return (
    <Modal title="Add Military Unit" onClose={onClose}>
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <Input label="Unit Name" value={name} onChange={setName} placeholder="e.g. 5th Strike Squadron" />
          <Input label="Unit Code" value={code} onChange={v => setCode(v.toUpperCase())} placeholder="e.g. 5TH-STRIKE-SQN" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[11px] font-semibold uppercase tracking-widest" style={{ color: "#8A94A6" }}>Description</label>
          <textarea
            value={desc}
            onChange={e => setDesc(e.target.value)}
            rows={2}
            placeholder="Brief description of unit mission…"
            className="px-3 py-2 rounded-lg text-sm resize-none outline-none"
            style={{ background: "#0E1420", border: "1px solid rgba(255,255,255,0.1)", color: "#E6EAF0" }}
          />
        </div>
        <div className="flex justify-end gap-2 pt-1">
          <button onClick={onClose} className="h-9 px-4 rounded-lg text-sm font-medium hover:bg-white/5 transition-colors" style={{ color: "#8A94A6", border: "1px solid rgba(255,255,255,0.1)" }}>
            Cancel
          </button>
          <button onClick={handleSave} className="h-9 px-5 rounded-lg text-sm font-semibold hover:opacity-90 transition-colors" style={{ background: "#C8A24A", color: "#0B0F14" }}>
            Add Unit
          </button>
        </div>
      </div>
    </Modal>
  );
}

// ─── Tab: Users ───────────────────────────────────────────────────────────────

function UsersTab({ units }: { units: Unit[] }) {
  const [users, setUsers] = useState<User[]>(SEED_USERS);
  const [search, setSearch] = useState("");
  const [filterRole, setFilterRole] = useState("");
  const [filterUnit, setFilterUnit] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [sortCol, setSortCol] = useState("name");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [page, setPage] = useState(1);
  const [showCreate, setShowCreate] = useState(false);
  const [changeRoleUser, setChangeRoleUser] = useState<User | null>(null);
  const [toggleUser, setToggleUser] = useState<User | null>(null);
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const PER_PAGE = 6;

  const handleSort = (col: string) => {
    if (sortCol === col) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortCol(col); setSortDir("asc"); }
    setPage(1);
  };

  const chips: { label: string; clear: () => void }[] = [];
  if (filterRole) chips.push({ label: `Role: ${filterRole}`, clear: () => setFilterRole("") });
  if (filterUnit) chips.push({ label: `Unit: ${filterUnit}`, clear: () => setFilterUnit("") });
  if (filterStatus) chips.push({ label: `Status: ${filterStatus}`, clear: () => setFilterStatus("") });

  const filtered = users
    .filter(u =>
      (!search || u.name.toLowerCase().includes(search.toLowerCase()) || u.email.toLowerCase().includes(search.toLowerCase())) &&
      (!filterRole || u.role === filterRole) &&
      (!filterUnit || u.unit === filterUnit) &&
      (!filterStatus || u.status === filterStatus)
    )
    .sort((a, b) => {
      const va = (a as any)[sortCol]?.toLowerCase?.() ?? (a as any)[sortCol] ?? "";
      const vb = (b as any)[sortCol]?.toLowerCase?.() ?? (b as any)[sortCol] ?? "";
      return sortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
    });

  const paged = filtered.slice((page - 1) * PER_PAGE, page * PER_PAGE);

  return (
    <div className="flex flex-col gap-4">
      {/* Filter bar */}
      <div className="flex items-center gap-2 flex-wrap">
        <SearchBar value={search} onChange={v => { setSearch(v); setPage(1); }} placeholder="Search name or email…" />
        <FilterSelect value={filterRole} onChange={v => { setFilterRole(v); setPage(1); }} options={ROLES} placeholder="Role" />
        <FilterSelect value={filterUnit} onChange={v => { setFilterUnit(v); setPage(1); }} options={UNITS_LIST.slice(1)} placeholder="Unit" />
        <FilterSelect value={filterStatus} onChange={v => { setFilterStatus(v); setPage(1); }} options={["Active", "Inactive"]} placeholder="Status" />
        <div className="flex-1" />
        <button
          onClick={() => setShowCreate(true)}
          className="inline-flex items-center gap-2 h-9 px-4 rounded-lg text-sm font-semibold hover:opacity-90 transition-colors"
          style={{ background: "#C8A24A", color: "#0B0F14" }}
        >
          <Plus className="w-3.5 h-3.5" />
          Create User
        </button>
      </div>

      {/* Active chips */}
      {chips.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          {chips.map(c => <FilterChip key={c.label} label={c.label} onRemove={c.clear} />)}
          <button onClick={() => { setFilterRole(""); setFilterUnit(""); setFilterStatus(""); }} className="text-xs hover:opacity-70 transition-opacity" style={{ color: "#8A94A6" }}>Clear all</button>
        </div>
      )}

      {/* Table */}
      <div className="rounded-xl border overflow-hidden" style={{ background: "#161D26", borderColor: "rgba(255,255,255,0.07)" }}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ background: "#0E1420", borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
                <ThCell label="Name" col="name" sortCol={sortCol} sortDir={sortDir} onSort={handleSort} />
                <ThCell label="Email" col="email" sortCol={sortCol} sortDir={sortDir} onSort={handleSort} />
                <th className="px-4 py-2.5 text-left text-[11px] font-semibold uppercase tracking-widest" style={{ color: "#8A94A6" }}>Role</th>
                <ThCell label="Unit" col="unit" sortCol={sortCol} sortDir={sortDir} onSort={handleSort} />
                <th className="px-4 py-2.5 text-left text-[11px] font-semibold uppercase tracking-widest" style={{ color: "#8A94A6" }}>Status</th>
                <ThCell label="Created By" col="createdBy" sortCol={sortCol} sortDir={sortDir} onSort={handleSort} />
                <ThCell label="Last Login" col="lastLogin" sortCol={sortCol} sortDir={sortDir} onSort={handleSort} />
                <th className="px-4 py-2.5 text-right text-[11px] font-semibold uppercase tracking-widest" style={{ color: "#8A94A6" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {paged.length === 0 ? (
                <tr><td colSpan={8}><EmptyState icon={Users} title="No users found" sub="Try adjusting your filters or search query" /></td></tr>
              ) : paged.map((u, i) => (
                <tr
                  key={u.id}
                  className="group transition-colors"
                  style={{
                    borderBottom: i < paged.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none",
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,0.025)")}
                  onMouseLeave={e => (e.currentTarget.style.background = "")}
                >
                  <td className="px-4 py-3 font-medium whitespace-nowrap" style={{ color: "#E6EAF0" }}>
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0" style={{ background: "rgba(200,162,74,0.15)", color: "#C8A24A" }}>
                        {u.name.split(" ").pop()![0]}
                      </div>
                      {u.name}
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap" style={{ color: "#8A94A6" }}>{u.email}</td>
                  <td className="px-4 py-3"><RoleBadge role={u.role} /></td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs font-mono" style={{ color: "#8A94A6" }}>{u.unit}</td>
                  <td className="px-4 py-3"><StatusPill status={u.status} /></td>
                  <td className="px-4 py-3 text-xs font-mono whitespace-nowrap" style={{ color: "#8A94A6" }}>{u.createdBy}</td>
                  <td className="px-4 py-3 text-xs font-mono whitespace-nowrap" style={{ color: "#8A94A6" }}>{u.lastLogin}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="relative inline-block">
                      <button
                        onClick={() => setOpenMenuId(openMenuId === u.id ? null : u.id)}
                        className="p-1.5 rounded hover:bg-white/5 transition-colors"
                        style={{ color: "#8A94A6" }}
                      >
                        <MoreHorizontal className="w-4 h-4" />
                      </button>
                      {openMenuId === u.id && (
                        <div
                          className="absolute right-0 top-full mt-1 z-20 rounded-lg border w-44 py-1 shadow-xl"
                          style={{ background: "#1C2533", borderColor: "rgba(255,255,255,0.1)" }}
                        >
                          <button
                            onClick={() => { setChangeRoleUser(u); setOpenMenuId(null); }}
                            className="flex items-center gap-2 w-full px-3 py-2 text-xs hover:bg-white/5 transition-colors text-left"
                            style={{ color: "#E6EAF0" }}
                          >
                            <Edit3 className="w-3.5 h-3.5" />
                            Change Role
                          </button>
                          <button
                            onClick={() => { setToggleUser(u); setOpenMenuId(null); }}
                            className="flex items-center gap-2 w-full px-3 py-2 text-xs hover:bg-white/5 transition-colors text-left"
                            style={{ color: u.status === "Active" ? "#E5484D" : "#3FB950" }}
                          >
                            {u.status === "Active" ? <ToggleLeft className="w-3.5 h-3.5" /> : <ToggleRight className="w-3.5 h-3.5" />}
                            {u.status === "Active" ? "Deactivate" : "Activate"}
                          </button>
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Pagination page={page} total={filtered.length} perPage={PER_PAGE} onChange={p => { setPage(p); setOpenMenuId(null); }} />
      </div>

      {showCreate && <CreateUserModal units={units} onClose={() => setShowCreate(false)} onSave={u => setUsers(prev => [u, ...prev])} />}
      {changeRoleUser && (
        <ChangeRoleModal
          user={changeRoleUser}
          onClose={() => setChangeRoleUser(null)}
          onSave={role => setUsers(prev => prev.map(u => u.id === changeRoleUser.id ? { ...u, role } : u))}
        />
      )}
      {toggleUser && (
        <ToggleStatusModal
          user={toggleUser}
          onClose={() => setToggleUser(null)}
          onConfirm={() => setUsers(prev => prev.map(u => u.id === toggleUser.id ? { ...u, status: u.status === "Active" ? "Inactive" : "Active" } : u))}
        />
      )}
    </div>
  );
}

// ─── Tab: Military Units ──────────────────────────────────────────────────────

function UnitsTab() {
  const [units, setUnits] = useState<Unit[]>(SEED_UNITS);
  const [showAdd, setShowAdd] = useState(false);
  const [search, setSearch] = useState("");

  const filtered = units.filter(u =>
    !search || u.name.toLowerCase().includes(search.toLowerCase()) || u.code.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <SearchBar value={search} onChange={setSearch} placeholder="Search unit name or code…" />
        <div className="flex-1" />
        <button
          onClick={() => setShowAdd(true)}
          className="inline-flex items-center gap-2 h-9 px-4 rounded-lg text-sm font-semibold hover:opacity-90 transition-colors"
          style={{ background: "#C8A24A", color: "#0B0F14" }}
        >
          <Plus className="w-3.5 h-3.5" />
          Add Unit
        </button>
      </div>

      <div className="rounded-xl border overflow-hidden" style={{ background: "#161D26", borderColor: "rgba(255,255,255,0.07)" }}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ background: "#0E1420", borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
                {["Unit Name", "Code", "Description", "Drones", "Users", "Status", ""].map(h => (
                  <th key={h} className="px-4 py-2.5 text-left text-[11px] font-semibold uppercase tracking-widest" style={{ color: "#8A94A6" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr><td colSpan={7}><EmptyState icon={Building2} title="No units found" sub="Add a unit or adjust your search" /></td></tr>
              ) : filtered.map((u, i) => (
                <tr
                  key={u.id}
                  className="transition-colors"
                  style={{ borderBottom: i < filtered.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none" }}
                  onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,0.025)")}
                  onMouseLeave={e => (e.currentTarget.style.background = "")}
                >
                  <td className="px-4 py-3 font-semibold whitespace-nowrap" style={{ color: "#E6EAF0" }}>{u.name}</td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-xs px-2 py-0.5 rounded" style={{ background: "rgba(255,255,255,0.06)", color: "#C8A24A" }}>{u.code}</span>
                  </td>
                  <td className="px-4 py-3 max-w-xs truncate" style={{ color: "#8A94A6" }}>{u.description}</td>
                  <td className="px-4 py-3 text-center font-mono text-xs" style={{ color: u.drones > 0 ? "#E6EAF0" : "#8A94A6" }}>{u.drones}</td>
                  <td className="px-4 py-3 text-center font-mono text-xs" style={{ color: u.users > 0 ? "#E6EAF0" : "#8A94A6" }}>{u.users}</td>
                  <td className="px-4 py-3"><StatusPill status={u.active ? "Active" : "Inactive"} /></td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => setUnits(prev => prev.map(x => x.id === u.id ? { ...x, active: !x.active } : x))}
                      className="text-xs px-3 py-1 rounded hover:opacity-80 transition-opacity"
                      style={{ color: u.active ? "#E5484D" : "#3FB950", border: `1px solid ${u.active ? "rgba(229,72,77,0.3)" : "rgba(63,185,80,0.3)"}` }}
                    >
                      {u.active ? "Deactivate" : "Activate"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showAdd && <AddUnitModal onClose={() => setShowAdd(false)} onSave={u => setUnits(prev => [...prev, u])} />}
    </div>
  );
}

// ─── Tab: Audit Log ───────────────────────────────────────────────────────────

function AuditTab() {
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterResult, setFilterResult] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sortCol, setSortCol] = useState("timestamp");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [page, setPage] = useState(1);
  const PER_PAGE = 8;

  const handleSort = (col: string) => {
    if (sortCol === col) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortCol(col); setSortDir("asc"); }
    setPage(1);
  };

  const chips: { label: string; clear: () => void }[] = [];
  if (filterType) chips.push({ label: `Action: ${filterType}`, clear: () => setFilterType("") });
  if (filterResult) chips.push({ label: `Result: ${filterResult}`, clear: () => setFilterResult("") });
  if (dateFrom) chips.push({ label: `From: ${dateFrom}`, clear: () => setDateFrom("") });
  if (dateTo) chips.push({ label: `To: ${dateTo}`, clear: () => setDateTo("") });

  const filtered = SEED_AUDIT
    .filter(e =>
      (!search || e.actor.toLowerCase().includes(search.toLowerCase()) || e.target.toLowerCase().includes(search.toLowerCase())) &&
      (!filterType || e.actionType === filterType) &&
      (!filterResult || e.result === filterResult) &&
      (!dateFrom || e.timestamp >= dateFrom) &&
      (!dateTo || e.timestamp <= dateTo + " 99")
    )
    .sort((a, b) => {
      const va = (a as any)[sortCol] ?? "";
      const vb = (b as any)[sortCol] ?? "";
      return sortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
    });

  const paged = filtered.slice((page - 1) * PER_PAGE, page * PER_PAGE);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 flex-wrap">
        <SearchBar value={search} onChange={v => { setSearch(v); setPage(1); }} placeholder="Search actor or target…" />
        <FilterSelect value={filterType} onChange={v => { setFilterType(v); setPage(1); }} options={AUDIT_ACTION_TYPES.slice(1)} placeholder="Action Type" />
        <FilterSelect value={filterResult} onChange={v => { setFilterResult(v); setPage(1); }} options={["Success", "Failure"]} placeholder="Result" />
        <div className="flex items-center gap-1.5">
          <input
            type="date"
            value={dateFrom}
            onChange={e => setDateFrom(e.target.value)}
            className="h-9 px-3 rounded-lg text-sm outline-none"
            style={{ background: "#0E1420", border: "1px solid rgba(255,255,255,0.09)", color: dateFrom ? "#E6EAF0" : "#8A94A6" }}
          />
          <span className="text-xs" style={{ color: "#8A94A6" }}>–</span>
          <input
            type="date"
            value={dateTo}
            onChange={e => setDateTo(e.target.value)}
            className="h-9 px-3 rounded-lg text-sm outline-none"
            style={{ background: "#0E1420", border: "1px solid rgba(255,255,255,0.09)", color: dateTo ? "#E6EAF0" : "#8A94A6" }}
          />
        </div>
        <div className="flex-1" />
        <button
          className="inline-flex items-center gap-2 h-9 px-4 rounded-lg text-sm font-semibold border hover:bg-white/5 transition-colors"
          style={{ color: "#C8A24A", borderColor: "rgba(200,162,74,0.35)" }}
          onClick={() => {
            const csv = ["Action Type,Actor,Target,Result,IP,User Agent,Timestamp",
              ...filtered.map(e => `${e.actionType},${e.actor},${e.target},${e.result},${e.ip},"${e.userAgent}",${e.timestamp}`)
            ].join("\n");
            const blob = new Blob([csv], { type: "text/csv" });
            const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "audit-log.csv"; a.click();
          }}
        >
          <Download className="w-3.5 h-3.5" />
          Export CSV
        </button>
      </div>

      {chips.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          {chips.map(c => <FilterChip key={c.label} label={c.label} onRemove={c.clear} />)}
          <button onClick={() => { setFilterType(""); setFilterResult(""); setDateFrom(""); setDateTo(""); }} className="text-xs hover:opacity-70" style={{ color: "#8A94A6" }}>Clear all</button>
        </div>
      )}

      <div className="rounded-xl border overflow-hidden" style={{ background: "#161D26", borderColor: "rgba(255,255,255,0.07)" }}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ background: "#0E1420", borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
                <th className="px-4 py-2.5 text-left text-[11px] font-semibold uppercase tracking-widest" style={{ color: "#8A94A6" }}>Action</th>
                <ThCell label="Actor" col="actor" sortCol={sortCol} sortDir={sortDir} onSort={handleSort} />
                <ThCell label="Target" col="target" sortCol={sortCol} sortDir={sortDir} onSort={handleSort} />
                <th className="px-4 py-2.5 text-left text-[11px] font-semibold uppercase tracking-widest" style={{ color: "#8A94A6" }}>Result</th>
                <th className="px-4 py-2.5 text-left text-[11px] font-semibold uppercase tracking-widest" style={{ color: "#8A94A6" }}>IP Address</th>
                <th className="px-4 py-2.5 text-left text-[11px] font-semibold uppercase tracking-widest" style={{ color: "#8A94A6" }}>User Agent</th>
                <ThCell label="Timestamp" col="timestamp" sortCol={sortCol} sortDir={sortDir} onSort={handleSort} />
              </tr>
            </thead>
            <tbody>
              {paged.length === 0 ? (
                <tr><td colSpan={7}><EmptyState icon={ScrollText} title="No audit entries" sub="Try adjusting your filters or date range" /></td></tr>
              ) : paged.map((e, i) => (
                <tr
                  key={e.id}
                  style={{ borderBottom: i < paged.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none" }}
                  onMouseEnter={ev => (ev.currentTarget.style.background = "rgba(255,255,255,0.02)")}
                  onMouseLeave={ev => (ev.currentTarget.style.background = "")}
                >
                  <td className="px-4 py-3"><AuditActionPill type={e.actionType} /></td>
                  <td className="px-4 py-3 text-xs font-mono whitespace-nowrap" style={{ color: "#E6EAF0" }}>{e.actor}</td>
                  <td className="px-4 py-3 text-xs font-mono whitespace-nowrap" style={{ color: "#8A94A6" }}>{e.target}</td>
                  <td className="px-4 py-3"><ResultPill result={e.result} /></td>
                  <td className="px-4 py-3 text-xs font-mono" style={{ color: "#8A94A6", fontFamily: "'IBM Plex Mono', monospace" }}>{e.ip}</td>
                  <td className="px-4 py-3 text-xs max-w-[160px] truncate" style={{ color: "#8A94A6", fontFamily: "'IBM Plex Mono', monospace" }} title={e.userAgent}>{e.userAgent}</td>
                  <td className="px-4 py-3 text-xs font-mono whitespace-nowrap" style={{ color: "#8A94A6", fontFamily: "'IBM Plex Mono', monospace" }}>{e.timestamp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-between px-4 py-2.5 border-t" style={{ borderColor: "rgba(255,255,255,0.07)", background: "#0E1420" }}>
          <span className="text-xs flex items-center gap-1.5" style={{ color: "#8A94A6" }}>
            <Shield className="w-3 h-3" />
            Audit log is immutable — entries cannot be edited or deleted.
          </span>
          <Pagination page={page} total={filtered.length} perPage={PER_PAGE} onChange={setPage} />
        </div>
      </div>
    </div>
  );
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────

const NAV_ITEMS = [
  { icon: Home,       label: "Dashboard",     active: false },
  { icon: Map,        label: "Mission Map",   active: false },
  { icon: Activity,   label: "Fleet Status",  active: false },
  { icon: Cpu,        label: "Drone Control", active: false },
  { icon: ScrollText, label: "Mission Logs",  active: false },
  { icon: Shield,     label: "Administration", active: true  },
  { icon: Settings,   label: "Settings",      active: false },
];

function Sidebar() {
  return (
    <aside className="flex flex-col w-[220px] shrink-0 h-full border-r" style={{ background: "#0E1420", borderColor: "rgba(255,255,255,0.06)" }}>
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-4 border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: "rgba(200,162,74,0.15)", border: "1px solid rgba(200,162,74,0.3)" }}>
          <Shield className="w-4 h-4" style={{ color: "#C8A24A" }} />
        </div>
        <div>
          <p className="text-xs font-bold tracking-widest uppercase" style={{ color: "#C8A24A" }}>MCS</p>
          <p className="text-[10px] tracking-wider uppercase" style={{ color: "#8A94A6" }}>Mission Control</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 px-2 flex flex-col gap-0.5 overflow-y-auto">
        {NAV_ITEMS.map(item => (
          <button
            key={item.label}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-left text-[13px] font-medium transition-all w-full"
            style={{
              background: item.active ? "rgba(200,162,74,0.12)" : "transparent",
              color: item.active ? "#C8A24A" : "#8A94A6",
              borderLeft: item.active ? "2px solid #C8A24A" : "2px solid transparent",
            }}
            onMouseEnter={e => { if (!item.active) { (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.04)"; (e.currentTarget as HTMLElement).style.color = "#E6EAF0"; } }}
            onMouseLeave={e => { if (!item.active) { (e.currentTarget as HTMLElement).style.background = "transparent"; (e.currentTarget as HTMLElement).style.color = "#8A94A6"; } }}
          >
            <item.icon className="w-4 h-4 shrink-0" />
            {item.label}
          </button>
        ))}
      </nav>

      {/* User */}
      <div className="px-3 py-3 border-t" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        <div className="flex items-center gap-2.5 px-2 py-2 rounded-lg">
          <div className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0" style={{ background: "rgba(200,162,74,0.2)", color: "#C8A24A" }}>H</div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold truncate" style={{ color: "#E6EAF0" }}>Col. Marcus Hale</p>
            <p className="text-[10px] truncate" style={{ color: "#8A94A6" }}>Admin</p>
          </div>
          <button className="hover:opacity-70 transition-opacity" style={{ color: "#8A94A6" }}>
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </aside>
  );
}

// ─── Top Bar ──────────────────────────────────────────────────────────────────

function TopBar() {
  return (
    <header className="h-12 flex items-center justify-between px-6 border-b shrink-0" style={{ background: "#0E1420", borderColor: "rgba(255,255,255,0.06)" }}>
      <div className="flex items-center gap-2 text-xs font-mono" style={{ color: "#8A94A6" }}>
        <span style={{ color: "#C8A24A" }}>MCS</span>
        <span>/</span>
        <span>Administration</span>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-mono" style={{ background: "rgba(63,185,80,0.1)", color: "#3FB950" }}>
          <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
          SYSTEM NOMINAL
        </div>
        <button className="relative p-2 rounded hover:bg-white/5 transition-colors" style={{ color: "#8A94A6" }}>
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full" style={{ background: "#E5484D" }} />
        </button>
        <button className="p-2 rounded hover:bg-white/5 transition-colors" style={{ color: "#8A94A6" }}>
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}

// ─── App Root ─────────────────────────────────────────────────────────────────

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("Users");
  const [units] = useState<Unit[]>(SEED_UNITS);

  const TABS: Tab[] = ["Users", "Military Units", "Audit Log"];
  const TAB_ICONS: Record<Tab, React.FC<any>> = { Users, "Military Units": Building2, "Audit Log": ScrollText };

  return (
    <div className="flex h-screen w-full overflow-hidden" style={{ background: "#0B0F14", fontFamily: "'Inter', system-ui, sans-serif" }}>
      <Sidebar />

      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <TopBar />

        {/* Main content */}
        <main className="flex-1 overflow-y-auto p-6" style={{ scrollbarWidth: "thin", scrollbarColor: "rgba(255,255,255,0.1) transparent" }}>
          {/* Page header */}
          <div className="flex items-start justify-between mb-5">
            <div>
              <h1 className="text-2xl font-semibold" style={{ color: "#E6EAF0" }}>Administration</h1>
              <p className="text-xs mt-0.5 font-mono" style={{ color: "#8A94A6" }}>Restricted — Admin &amp; Commander roles</p>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs border" style={{ background: "rgba(229,72,77,0.08)", color: "#E5484D", borderColor: "rgba(229,72,77,0.2)" }}>
              <Shield className="w-3.5 h-3.5" />
              RESTRICTED ACCESS
            </div>
          </div>

          {/* Tab bar */}
          <div className="flex items-center gap-0 mb-5 border-b" style={{ borderColor: "rgba(255,255,255,0.07)" }}>
            {TABS.map(tab => {
              const Icon = TAB_ICONS[tab];
              const active = tab === activeTab;
              return (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className="inline-flex items-center gap-2 px-5 py-3 text-sm font-medium relative transition-colors"
                  style={{ color: active ? "#C8A24A" : "#8A94A6" }}
                  onMouseEnter={e => { if (!active) (e.currentTarget as HTMLElement).style.color = "#E6EAF0"; }}
                  onMouseLeave={e => { if (!active) (e.currentTarget as HTMLElement).style.color = "#8A94A6"; }}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {tab}
                  {active && (
                    <span className="absolute bottom-0 left-0 right-0 h-0.5 rounded-t" style={{ background: "#C8A24A" }} />
                  )}
                </button>
              );
            })}
          </div>

          {/* Tab content */}
          {activeTab === "Users" && <UsersTab units={units} />}
          {activeTab === "Military Units" && <UnitsTab />}
          {activeTab === "Audit Log" && <AuditTab />}
        </main>
      </div>
    </div>
  );
}
