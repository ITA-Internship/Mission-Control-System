import { useState, useRef, useCallback, useEffect } from "react";
import {
  LayoutDashboard,
  Map,
  Navigation2,
  Bell,
  Users,
  Wrench,
  Settings,
  User,
  Eye,
  EyeOff,
  Upload,
  X,
  Check,
  Camera,
  Lock,
  Clock,
  LogOut,
  ChevronDown,
  AlertCircle,
  CheckCircle,
  Shield,
  Activity,
  Menu,
  ChevronRight,
  Crosshair,
  BarChart3,
  Target,
} from "lucide-react";
import { toast, Toaster } from "sonner";

// ─── Types ────────────────────────────────────────────────────────────────────
type Role = "Admin" | "Commander" | "Dispatcher" | "Operator" | "Technician" | "Viewer";
type AvatarState = "idle" | "dragging" | "uploading" | "success" | "error";

// ─── Data ─────────────────────────────────────────────────────────────────────
const ROLE_BADGE: Record<Role, { fg: string; bg: string; border: string }> = {
  Admin:      { fg: "#C8A24A", bg: "rgba(200,162,74,.13)",  border: "rgba(200,162,74,.3)"  },
  Commander:  { fg: "#4C8DFF", bg: "rgba(76,141,255,.13)",  border: "rgba(76,141,255,.3)"  },
  Dispatcher: { fg: "#2DD4BF", bg: "rgba(45,212,191,.13)",  border: "rgba(45,212,191,.3)"  },
  Operator:   { fg: "#8A94A6", bg: "rgba(138,148,166,.13)", border: "rgba(138,148,166,.3)" },
  Technician: { fg: "#A78BFA", bg: "rgba(167,139,250,.13)", border: "rgba(167,139,250,.3)" },
  Viewer:     { fg: "#6B7280", bg: "rgba(107,114,128,.13)", border: "rgba(107,114,128,.3)" },
};

const USER = {
  id:        "USR-0047",
  name:      "Major Sarah Chen",
  firstName: "Sarah",
  lastName:  "Chen",
  rank:      "Major",
  email:     "s.chen@mil-ops.gov",
  role:      "Commander" as Role,
  unit:      "3rd UAS Battalion",
  phone:     "+1 (703) 555-0192",
  joined:    "2022-03-14",
  lastLogin: "2026-07-28  08:14 UTC",
  status:    "Active",
  createdBy: "Lt. Col. R. Vasquez",
};

const NAV_ITEMS = [
  { icon: LayoutDashboard, label: "Dashboard"   },
  { icon: Map,             label: "Fleet Map"   },
  { icon: Navigation2,     label: "Drone Fleet" },
  { icon: Target,          label: "Missions"    },
  { icon: Bell,            label: "Alerts"      },
  { icon: Users,           label: "Operators"   },
  { icon: Wrench,          label: "Maintenance" },
  { icon: BarChart3,       label: "Reports"     },
  { icon: Settings,        label: "Settings"    },
];

const SECTIONS = [
  { id: "profile",  label: "Profile Details"     },
  { id: "avatar",   label: "Avatar"              },
  { id: "password", label: "Change Password"     },
  { id: "security", label: "Account & Security"  },
];

// ─── Password helpers ─────────────────────────────────────────────────────────
function calcStrength(pw: string) {
  if (!pw) return { score: 0, label: "", color: "transparent" };
  let s = 0;
  if (pw.length >= 8)           s++;
  if (pw.length >= 12)          s++;
  if (/[A-Z]/.test(pw))         s++;
  if (/[0-9]/.test(pw))         s++;
  if (/[^A-Za-z0-9]/.test(pw))  s++;
  const map = [
    { label: "Very Weak",   color: "#E5484D" },
    { label: "Weak",        color: "#F97316" },
    { label: "Fair",        color: "#EAB308" },
    { label: "Strong",      color: "#84CC16" },
    { label: "Very Strong", color: "#3FB950" },
  ];
  return { score: s, ...map[Math.min(s, 4)] };
}

function checkReqs(pw: string) {
  return [
    { label: "At least 8 characters",    ok: pw.length >= 8           },
    { label: "Uppercase letter (A–Z)",   ok: /[A-Z]/.test(pw)         },
    { label: "Lowercase letter (a–z)",   ok: /[a-z]/.test(pw)         },
    { label: "Number (0–9)",             ok: /[0-9]/.test(pw)         },
    { label: "Special character (!@#…)", ok: /[^A-Za-z0-9]/.test(pw) },
  ];
}

// ─── Primitive components ─────────────────────────────────────────────────────
function RoleBadge({ role }: { role: Role }) {
  const c = ROLE_BADGE[role];
  return (
    <span
      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide border"
      style={{ color: c.fg, background: c.bg, borderColor: c.border }}
    >
      {role}
    </span>
  );
}

function UnitChip({ unit }: { unit: string }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border"
      style={{ color: "#8A94A6", background: "rgba(138,148,166,.08)", borderColor: "rgba(138,148,166,.2)" }}
    >
      <Shield size={10} />
      {unit}
    </span>
  );
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label className="text-xs font-semibold tracking-widest uppercase" style={{ color: "#8A94A6" }}>
      {children}
    </label>
  );
}

function TextInput({
  value, onChange, placeholder = "", type = "text",
  disabled = false, error = false, rightEl,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
  disabled?: boolean;
  error?: boolean;
  rightEl?: React.ReactNode;
}) {
  const [focused, setFocused] = useState(false);
  return (
    <div className="relative">
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        className="w-full rounded-lg px-3 py-2.5 text-sm outline-none transition-all"
        style={{
          background: disabled ? "rgba(15,22,32,.5)" : "#0F1620",
          color: disabled ? "#8A94A6" : "#E6EAF0",
          border: `1px solid ${
            error   ? "#E5484D"
            : focused ? "#C8A24A"
            : "rgba(255,255,255,.1)"
          }`,
          paddingRight: rightEl ? "2.75rem" : undefined,
          boxShadow: focused && !error ? "0 0 0 2px rgba(200,162,74,.12)" : undefined,
        }}
      />
      {rightEl && (
        <div className="absolute right-3 top-1/2 -translate-y-1/2">{rightEl}</div>
      )}
    </div>
  );
}

function Card({ id, title, children, accent = false }: {
  id?: string; title: string; children: React.ReactNode; accent?: boolean;
}) {
  return (
    <div
      id={id}
      className="rounded-xl border overflow-hidden"
      style={{ background: "#161D26", borderColor: accent ? "rgba(200,162,74,.18)" : "rgba(255,255,255,.07)" }}
    >
      {accent && <div className="h-px" style={{ background: "linear-gradient(90deg, #C8A24A 0%, transparent 55%)" }} />}
      <div className="px-6 py-4 border-b flex items-center gap-3" style={{ borderColor: "rgba(255,255,255,.07)" }}>
        <h2 className="text-sm font-semibold tracking-wide" style={{ color: "#E6EAF0" }}>{title}</h2>
      </div>
      <div className="px-6 py-5">{children}</div>
    </div>
  );
}

function PrimaryBtn({
  children, onClick, loading = false, disabled = false, type = "button",
}: {
  children: React.ReactNode; onClick?: () => void;
  loading?: boolean; disabled?: boolean; type?: "button" | "submit";
}) {
  const isDisabled = disabled || loading;
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={isDisabled}
      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all"
      style={{
        background: isDisabled ? "rgba(200,162,74,.35)" : "#C8A24A",
        color: "#0B0F14",
        cursor: isDisabled ? "not-allowed" : "pointer",
        opacity: isDisabled ? 0.7 : 1,
      }}
    >
      {loading && (
        <svg className="animate-spin w-3.5 h-3.5" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {children}
    </button>
  );
}

function SecondaryBtn({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
      style={{ background: "rgba(255,255,255,.05)", color: "#E6EAF0", border: "1px solid rgba(255,255,255,.1)" }}
      onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,.09)")}
      onMouseLeave={e => (e.currentTarget.style.background = "rgba(255,255,255,.05)")}
    >
      {children}
    </button>
  );
}

function AlertBanner({ type, message, onClose }: {
  type: "error" | "success" | "info"; message: string; onClose?: () => void;
}) {
  const cfg = {
    error:   { bg: "rgba(229,72,77,.1)",   border: "rgba(229,72,77,.3)",   color: "#E5484D", Icon: AlertCircle  },
    success: { bg: "rgba(63,185,80,.1)",   border: "rgba(63,185,80,.3)",   color: "#3FB950", Icon: CheckCircle  },
    info:    { bg: "rgba(138,148,166,.1)", border: "rgba(138,148,166,.3)", color: "#8A94A6", Icon: AlertCircle  },
  }[type];
  const { Icon } = cfg;
  return (
    <div
      className="flex items-start gap-3 p-3 rounded-lg border text-sm"
      style={{ background: cfg.bg, borderColor: cfg.border }}
    >
      <Icon size={15} style={{ color: cfg.color, flexShrink: 0, marginTop: 1 }} />
      <span className="flex-1 text-sm" style={{ color: cfg.color }}>{message}</span>
      {onClose && (
        <button onClick={onClose} style={{ color: cfg.color, flexShrink: 0 }}>
          <X size={14} />
        </button>
      )}
    </div>
  );
}

// ─── Avatar Upload Card ───────────────────────────────────────────────────────
function AvatarUploadCard({ avatarUrl, onAvatarChange }: {
  avatarUrl: string | null; onAvatarChange: (url: string | null) => void;
}) {
  const [state, setState] = useState<AvatarState>("idle");
  const [preview, setPreview] = useState<string | null>(null);
  const [errMsg, setErrMsg] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((file: File) => {
    const allowed = ["image/jpeg", "image/png", "image/webp", "image/gif"];
    if (!allowed.includes(file.type)) {
      setState("error");
      setErrMsg("Invalid file type. Accepted: JPG, PNG, WEBP, GIF.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setState("error");
      setErrMsg("File too large. Maximum size is 5 MB.");
      return;
    }
    setState("uploading");
    const reader = new FileReader();
    reader.onload = e => {
      const result = e.target?.result as string;
      setPreview(result);
      setTimeout(() => {
        setState("success");
        onAvatarChange(result);
        toast.success("Avatar updated.");
      }, 1200);
    };
    reader.readAsDataURL(file);
  }, [onAvatarChange]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setState("idle");
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const current = preview || avatarUrl;
  const isDragging = state === "dragging";

  return (
    <Card id="avatar" title="Avatar">
      <div className="flex flex-col sm:flex-row gap-6 items-start">
        {/* Preview */}
        <div className="flex-shrink-0 flex flex-col items-center gap-2">
          <div
            className="w-24 h-24 rounded-full overflow-hidden border-2 flex items-center justify-center"
            style={{ borderColor: "rgba(200,162,74,.3)", background: "#1A2233" }}
          >
            {current ? (
              <img src={current} alt="Avatar" className="w-full h-full object-cover" />
            ) : (
              <span className="text-2xl font-bold" style={{ color: "#C8A24A" }}>SC</span>
            )}
          </div>
          {current && (
            <button
              onClick={() => { setPreview(null); onAvatarChange(null); setState("idle"); setErrMsg(""); }}
              className="text-xs transition-colors"
              style={{ color: "#E5484D" }}
            >
              Remove
            </button>
          )}
        </div>

        {/* Dropzone + controls */}
        <div className="flex-1 flex flex-col gap-3">
          <div
            onDrop={handleDrop}
            onDragOver={e => { e.preventDefault(); setState("dragging"); }}
            onDragLeave={() => setState("idle")}
            onClick={() => inputRef.current?.click()}
            className="relative flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-8 cursor-pointer transition-all"
            style={{
              borderColor: isDragging ? "#C8A24A" : state === "error" ? "#E5484D" : "rgba(255,255,255,.12)",
              background:  isDragging ? "rgba(200,162,74,.04)" : "rgba(255,255,255,.015)",
            }}
          >
            {state === "uploading" ? (
              <div className="flex flex-col items-center gap-2">
                <svg className="animate-spin w-6 h-6" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="#C8A24A" strokeWidth="4" />
                  <path className="opacity-75" fill="#C8A24A" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <span className="text-xs" style={{ color: "#8A94A6" }}>Uploading…</span>
              </div>
            ) : state === "success" ? (
              <div className="flex flex-col items-center gap-2">
                <CheckCircle size={24} style={{ color: "#3FB950" }} />
                <span className="text-xs font-medium" style={{ color: "#3FB950" }}>Upload successful</span>
              </div>
            ) : (
              <>
                <Upload size={20} style={{ color: "#8A94A6" }} />
                <p className="text-sm text-center">
                  <span className="font-medium" style={{ color: "#E6EAF0" }}>Drop an image here</span>
                  <span style={{ color: "#8A94A6" }}> or </span>
                  <span className="font-semibold" style={{ color: "#C8A24A" }}>browse files</span>
                </p>
              </>
            )}
            <input
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              className="hidden"
              onChange={e => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
                e.target.value = "";
              }}
            />
          </div>

          {state === "error" && (
            <AlertBanner
              type="error"
              message={errMsg}
              onClose={() => { setState("idle"); setErrMsg(""); }}
            />
          )}

          <p className="text-xs" style={{ color: "#8A94A6" }}>
            Accepted: JPG, PNG, WEBP, GIF &mdash; max 5 MB. Image will be cropped to a circle.
          </p>
        </div>
      </div>
    </Card>
  );
}

// ─── Profile Details Card ─────────────────────────────────────────────────────
function ProfileDetailsCard() {
  const [mode, setMode]   = useState<"read" | "edit" | "saving">("read");
  const [rank, setRank]   = useState(USER.rank);
  const [phone, setPhone] = useState(USER.phone);
  const [banner, setBanner] = useState<"success" | null>(null);

  const save = () => {
    setMode("saving");
    setTimeout(() => {
      setMode("read");
      setBanner("success");
      toast.success("Profile changes saved.");
      setTimeout(() => setBanner(null), 4000);
    }, 1400);
  };

  const cancel = () => {
    setRank(USER.rank);
    setPhone(USER.phone);
    setMode("read");
  };

  const editing = mode === "edit";
  const saving  = mode === "saving";

  return (
    <Card id="profile" title="Profile Details">
      <div className="flex flex-col gap-5">
        {banner === "success" && (
          <AlertBanner type="success" message="Profile changes saved successfully." onClose={() => setBanner(null)} />
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {/* Full name — always read-only */}
          <div className="flex flex-col gap-1.5">
            <FieldLabel>Full Name</FieldLabel>
            <span className="text-sm" style={{ color: "#8A94A6" }}>{USER.name}</span>
          </div>

          {/* Rank — editable */}
          <div className="flex flex-col gap-1.5">
            <FieldLabel>Rank</FieldLabel>
            {editing ? (
              <TextInput value={rank} onChange={setRank} placeholder="e.g. Major" />
            ) : (
              <span className="text-sm" style={{ color: saving ? "#8A94A6" : "#E6EAF0" }}>{rank}</span>
            )}
          </div>

          {/* Email — always read-only */}
          <div className="flex flex-col gap-1.5">
            <FieldLabel>Email Address</FieldLabel>
            <span className="text-sm font-mono" style={{ color: "#8A94A6" }}>{USER.email}</span>
            <span className="text-xs" style={{ color: "#4A5568" }}>Managed by administrators &mdash; not editable</span>
          </div>

          {/* Phone — editable */}
          <div className="flex flex-col gap-1.5">
            <FieldLabel>Phone / Contact</FieldLabel>
            {editing ? (
              <TextInput value={phone} onChange={setPhone} type="tel" placeholder="+1 (000) 000-0000" />
            ) : (
              <span className="text-sm font-mono" style={{ color: saving ? "#8A94A6" : "#E6EAF0" }}>{phone}</span>
            )}
          </div>

          {/* Unit — always read-only */}
          <div className="flex flex-col gap-1.5">
            <FieldLabel>Military Unit</FieldLabel>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm" style={{ color: "#8A94A6" }}>{USER.unit}</span>
              <span
                className="text-xs px-1.5 py-0.5 rounded"
                style={{ background: "rgba(138,148,166,.1)", color: "#8A94A6" }}
              >
                Admin-managed
              </span>
            </div>
          </div>

          {/* Role — always read-only */}
          <div className="flex flex-col gap-1.5">
            <FieldLabel>Role</FieldLabel>
            <div className="flex flex-wrap items-center gap-2">
              <RoleBadge role={USER.role} />
              <span className="text-xs" style={{ color: "#4A5568" }}>Admin-managed &mdash; not editable</span>
            </div>
          </div>
        </div>

        <div
          className="flex items-center gap-3 pt-4 border-t"
          style={{ borderColor: "rgba(255,255,255,.07)" }}
        >
          {!editing && !saving ? (
            <PrimaryBtn onClick={() => setMode("edit")}>Edit Profile</PrimaryBtn>
          ) : (
            <>
              <PrimaryBtn onClick={save} loading={saving}>
                {saving ? "Saving…" : "Save Changes"}
              </PrimaryBtn>
              {!saving && <SecondaryBtn onClick={cancel}>Cancel</SecondaryBtn>}
            </>
          )}
        </div>
      </div>
    </Card>
  );
}

// ─── Change Password Card ─────────────────────────────────────────────────────
function ChangePasswordCard() {
  const [current,     setCurrent]     = useState("");
  const [next,        setNext]        = useState("");
  const [confirm,     setConfirm]     = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNext,    setShowNext]    = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [status,      setStatus]      = useState<"idle" | "saving" | "success" | "error">("idle");
  const [errMsg,      setErrMsg]      = useState("");

  const strength       = calcStrength(next);
  const reqs           = checkReqs(next);
  const allReqsMet     = reqs.every(r => r.ok);
  const mismatch       = confirm.length > 0 && next !== confirm;
  const canSubmit      = current && next && confirm && !mismatch;

  const EyeToggle = ({ show, toggle }: { show: boolean; toggle: () => void }) => (
    <button type="button" onClick={toggle} style={{ color: "#8A94A6" }} className="transition-colors hover:text-[#E6EAF0]">
      {show ? <EyeOff size={15} /> : <Eye size={15} />}
    </button>
  );

  const submit = () => {
    if (!current)    { setErrMsg("Current password is required.");           setStatus("error"); return; }
    if (!allReqsMet) { setErrMsg("New password does not meet requirements."); setStatus("error"); return; }
    if (next !== confirm) { setErrMsg("Passwords do not match.");             setStatus("error"); return; }
    setStatus("saving");
    setErrMsg("");
    setTimeout(() => {
      if (current === "wrong") {
        setStatus("error");
        setErrMsg("Current password is incorrect. Please try again.");
      } else {
        setStatus("success");
        setCurrent(""); setNext(""); setConfirm("");
        toast.success("Password updated successfully.");
      }
    }, 1500);
  };

  return (
    <Card id="password" title="Change Password">
      <div className="flex flex-col gap-4 max-w-md">
        {status === "error" && (
          <AlertBanner type="error" message={errMsg} onClose={() => setStatus("idle")} />
        )}
        {status === "success" && (
          <AlertBanner type="success" message="Your password has been updated." onClose={() => setStatus("idle")} />
        )}

        {/* Current password */}
        <div className="flex flex-col gap-1.5">
          <FieldLabel>Current Password</FieldLabel>
          <TextInput
            value={current}
            onChange={setCurrent}
            type={showCurrent ? "text" : "password"}
            placeholder="Enter current password"
            rightEl={<EyeToggle show={showCurrent} toggle={() => setShowCurrent(v => !v)} />}
          />
        </div>

        {/* New password + strength */}
        <div className="flex flex-col gap-1.5">
          <FieldLabel>New Password</FieldLabel>
          <TextInput
            value={next}
            onChange={setNext}
            type={showNext ? "text" : "password"}
            placeholder="Enter new password"
            rightEl={<EyeToggle show={showNext} toggle={() => setShowNext(v => !v)} />}
          />
          {next.length > 0 && (
            <div className="flex flex-col gap-1.5 mt-1">
              <div className="flex gap-1 h-1.5">
                {[1, 2, 3, 4, 5].map(i => (
                  <div
                    key={i}
                    className="flex-1 rounded-full transition-all duration-300"
                    style={{ background: i <= strength.score ? strength.color : "rgba(255,255,255,.1)" }}
                  />
                ))}
              </div>
              {strength.label && (
                <span className="text-xs font-semibold" style={{ color: strength.color }}>
                  {strength.label}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Confirm password */}
        <div className="flex flex-col gap-1.5">
          <FieldLabel>Confirm New Password</FieldLabel>
          <TextInput
            value={confirm}
            onChange={setConfirm}
            type={showConfirm ? "text" : "password"}
            placeholder="Confirm new password"
            error={mismatch}
            rightEl={<EyeToggle show={showConfirm} toggle={() => setShowConfirm(v => !v)} />}
          />
          {mismatch && (
            <span className="text-xs" style={{ color: "#E5484D" }}>Passwords do not match.</span>
          )}
        </div>

        {/* Requirements checklist */}
        {next.length > 0 && (
          <div
            className="rounded-lg p-4 border"
            style={{ background: "rgba(255,255,255,.02)", borderColor: "rgba(255,255,255,.07)" }}
          >
            <p className="text-xs font-semibold tracking-widest uppercase mb-3" style={{ color: "#8A94A6" }}>
              Requirements
            </p>
            <div className="flex flex-col gap-2">
              {reqs.map(r => (
                <div key={r.label} className="flex items-center gap-2.5">
                  <div
                    className="w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0"
                    style={{ background: r.ok ? "rgba(63,185,80,.15)" : "rgba(229,72,77,.1)" }}
                  >
                    {r.ok
                      ? <Check size={9}  style={{ color: "#3FB950" }} />
                      : <X     size={9}  style={{ color: "#E5484D" }} />
                    }
                  </div>
                  <span className="text-xs" style={{ color: r.ok ? "#3FB950" : "#8A94A6" }}>{r.label}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="pt-3 border-t" style={{ borderColor: "rgba(255,255,255,.07)" }}>
          <PrimaryBtn onClick={submit} loading={status === "saving"} disabled={!canSubmit}>
            {status === "saving" ? "Updating…" : "Update Password"}
          </PrimaryBtn>
        </div>
      </div>
    </Card>
  );
}

// ─── Account & Security Card ──────────────────────────────────────────────────
function AccountSecurityCard() {
  return (
    <Card id="security" title="Account & Security">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div className="flex flex-col gap-1.5">
          <FieldLabel>Account Status</FieldLabel>
          <span
            className="inline-flex items-center gap-1.5 w-fit px-2.5 py-1 rounded-full text-xs font-semibold border"
            style={{ color: "#3FB950", background: "rgba(63,185,80,.1)", borderColor: "rgba(63,185,80,.25)" }}
          >
            <span className="w-1.5 h-1.5 rounded-full inline-block animate-pulse" style={{ background: "#3FB950" }} />
            {USER.status}
          </span>
        </div>

        <div className="flex flex-col gap-1.5">
          <FieldLabel>Account ID</FieldLabel>
          <span className="text-sm font-mono" style={{ color: "#8A94A6" }}>{USER.id}</span>
        </div>

        <div className="flex flex-col gap-1.5">
          <FieldLabel>Date Joined</FieldLabel>
          <div className="flex items-center gap-2">
            <Clock size={13} style={{ color: "#8A94A6" }} />
            <span className="text-sm font-mono" style={{ color: "#8A94A6" }}>{USER.joined}</span>
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <FieldLabel>Account Created By</FieldLabel>
          <span className="text-sm" style={{ color: "#8A94A6" }}>{USER.createdBy}</span>
        </div>

        <div className="flex flex-col gap-1.5">
          <FieldLabel>Last Login</FieldLabel>
          <div className="flex items-center gap-2">
            <Activity size={13} style={{ color: "#8A94A6" }} />
            <span className="text-sm font-mono" style={{ color: "#8A94A6" }}>{USER.lastLogin}</span>
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <FieldLabel>Authentication</FieldLabel>
          <div className="flex items-center gap-2">
            <Lock size={13} style={{ color: "#8A94A6" }} />
            <span className="text-sm" style={{ color: "#8A94A6" }}>Password + 2FA (TOTP)</span>
          </div>
        </div>
      </div>

      <p className="mt-5 text-xs" style={{ color: "#4A5568" }}>
        Account status, role, and unit are administrator-managed. Contact your system admin for changes.
      </p>
    </Card>
  );
}

// ─── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  const [avatarUrl,     setAvatarUrl]     = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState("profile");
  const [sidebarOpen,   setSidebarOpen]   = useState(false);
  const [userMenuOpen,  setUserMenuOpen]  = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close user menu on outside click
  useEffect(() => {
    if (!userMenuOpen) return;
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [userMenuOpen]);

  const scrollTo = (id: string) => {
    setActiveSection(id);
    setSidebarOpen(false);
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div
      className="flex h-screen overflow-hidden"
      style={{ background: "#0B0F14", fontFamily: "'Inter', -apple-system, sans-serif" }}
    >
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#161D26",
            color: "#E6EAF0",
            border: "1px solid rgba(255,255,255,.1)",
            fontFamily: "'Inter', sans-serif",
          },
        }}
      />

      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-60 flex flex-col border-r transition-transform duration-200
          lg:translate-x-0 lg:static lg:z-auto ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}`}
        style={{ background: "#0D1219", borderColor: "rgba(255,255,255,.07)" }}
      >
        {/* Brand */}
        <div
          className="flex items-center gap-3 px-5 h-14 border-b flex-shrink-0"
          style={{ borderColor: "rgba(255,255,255,.07)" }}
        >
          <div
            className="w-7 h-7 rounded flex items-center justify-center flex-shrink-0"
            style={{ background: "rgba(200,162,74,.13)", border: "1px solid rgba(200,162,74,.28)" }}
          >
            <Crosshair size={14} style={{ color: "#C8A24A" }} />
          </div>
          <div className="leading-none">
            <div className="text-xs font-bold tracking-widest uppercase" style={{ color: "#E6EAF0" }}>Mission</div>
            <div className="text-[10px] tracking-widest mt-0.5" style={{ color: "#8A94A6" }}>CONTROL SYSTEM</div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-3 px-2" style={{ scrollbarWidth: "none" }}>
          <p className="px-3 mb-2 text-[10px] font-semibold tracking-widest uppercase" style={{ color: "#4A5568" }}>
            Navigation
          </p>
          {NAV_ITEMS.map(item => {
            const Icon = item.icon;
            return (
              <button
                key={item.label}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm mb-0.5 transition-all text-left"
                style={{ color: "#8A94A6", background: "transparent" }}
                onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,.04)")}
                onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
              >
                <Icon size={15} />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Bottom user strip */}
        <div className="px-4 py-4 border-t" style={{ borderColor: "rgba(255,255,255,.07)" }}>
          <div className="flex items-center gap-3">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
              style={{ background: "rgba(200,162,74,.13)", color: "#C8A24A", border: "1px solid rgba(200,162,74,.25)" }}
            >
              SC
            </div>
            <div className="min-w-0">
              <div className="text-xs font-semibold truncate" style={{ color: "#E6EAF0" }}>Maj. S. Chen</div>
              <div className="text-xs truncate" style={{ color: "#8A94A6" }}>{USER.unit}</div>
            </div>
          </div>
        </div>
      </aside>

      {/* Backdrop (mobile) */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Main ────────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header
          className="flex items-center justify-between px-5 h-14 border-b flex-shrink-0"
          style={{ background: "#0D1219", borderColor: "rgba(255,255,255,.07)" }}
        >
          <div className="flex items-center gap-3">
            <button className="lg:hidden" onClick={() => setSidebarOpen(v => !v)} style={{ color: "#8A94A6" }}>
              <Menu size={20} />
            </button>
            {/* Breadcrumb */}
            <nav className="flex items-center gap-1.5 text-xs" style={{ color: "#8A94A6" }}>
              <span>Home</span>
              <ChevronRight size={11} />
              <span style={{ color: "#E6EAF0" }}>My Profile</span>
            </nav>
          </div>

          <div className="flex items-center gap-3">
            {/* Alert bell */}
            <button className="relative" style={{ color: "#8A94A6" }}>
              <Bell size={17} />
              <span
                className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full"
                style={{ background: "#E5484D" }}
              />
            </button>

            {/* User menu */}
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setUserMenuOpen(v => !v)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all"
                style={{ background: "rgba(255,255,255,.04)", border: "1px solid rgba(255,255,255,.08)" }}
              >
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold overflow-hidden"
                  style={{ background: "rgba(200,162,74,.13)", color: "#C8A24A" }}
                >
                  {avatarUrl
                    ? <img src={avatarUrl} alt="avatar" className="w-full h-full object-cover" />
                    : "SC"
                  }
                </div>
                <span className="text-xs font-medium hidden sm:block" style={{ color: "#E6EAF0" }}>
                  Maj. S. Chen
                </span>
                <ChevronDown size={12} style={{ color: "#8A94A6" }} />
              </button>

              {userMenuOpen && (
                <div
                  className="absolute right-0 top-full mt-2 w-56 rounded-xl border overflow-hidden z-50 shadow-2xl"
                  style={{ background: "#161D26", borderColor: "rgba(255,255,255,.1)" }}
                >
                  <div className="px-4 py-3 border-b" style={{ borderColor: "rgba(255,255,255,.07)" }}>
                    <div className="text-sm font-semibold" style={{ color: "#E6EAF0" }}>{USER.name}</div>
                    <div className="text-xs font-mono mt-0.5" style={{ color: "#8A94A6" }}>{USER.email}</div>
                    <div className="mt-2 flex items-center gap-2">
                      <RoleBadge role={USER.role} />
                      <UnitChip unit="3rd UAS" />
                    </div>
                  </div>
                  <div className="p-2">
                    {[
                      { icon: User,     label: "My Profile", color: "#C8A24A" },
                      { icon: Settings, label: "Settings",   color: "#8A94A6" },
                    ].map(item => {
                      const Icon = item.icon;
                      return (
                        <button
                          key={item.label}
                          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-left transition-all"
                          style={{ color: "#E6EAF0" }}
                          onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,.05)")}
                          onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
                        >
                          <Icon size={13} style={{ color: item.color }} />
                          {item.label}
                        </button>
                      );
                    })}
                    <div className="border-t my-1" style={{ borderColor: "rgba(255,255,255,.07)" }} />
                    <button
                      className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-left transition-all"
                      style={{ color: "#E5484D" }}
                      onMouseEnter={e => (e.currentTarget.style.background = "rgba(229,72,77,.08)")}
                      onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
                    >
                      <LogOut size={13} />
                      Sign Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* ── Content ─────────────────────────────────────────────── */}
        <main className="flex-1 overflow-y-auto" style={{ scrollbarWidth: "none" }}>
          <div className="max-w-[960px] mx-auto px-6 py-8">

            {/* Page title */}
            <div className="mb-7">
              <h1 className="text-2xl font-semibold" style={{ color: "#E6EAF0" }}>My Profile</h1>
              <p className="text-sm mt-1" style={{ color: "#8A94A6" }}>
                Manage your personal information and account security settings.
              </p>
            </div>

            {/* ── Profile Summary Band ─────────────────────────────── */}
            <div
              className="rounded-xl border mb-8 overflow-hidden"
              style={{
                background: "#161D26",
                borderColor: "rgba(200,162,74,.15)",
                boxShadow: "0 0 0 1px rgba(200,162,74,.05), 0 4px 24px rgba(0,0,0,.3)",
              }}
            >
              {/* Gold accent rule */}
              <div className="h-px" style={{ background: "linear-gradient(90deg, #C8A24A 0%, rgba(200,162,74,.15) 50%, transparent 80%)" }} />

              <div className="px-6 py-6 flex flex-col sm:flex-row items-start sm:items-center gap-5">
                {/* Avatar with hover-to-edit overlay */}
                <div
                  className="relative group flex-shrink-0 cursor-pointer"
                  onClick={() => scrollTo("avatar")}
                  title="Change avatar"
                >
                  <div
                    className="w-[76px] h-[76px] rounded-full overflow-hidden border-2"
                    style={{ borderColor: "rgba(200,162,74,.35)", background: "rgba(200,162,74,.08)" }}
                  >
                    {avatarUrl ? (
                      <img src={avatarUrl} alt="Profile" className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-2xl font-bold" style={{ color: "#C8A24A" }}>
                        SC
                      </div>
                    )}
                  </div>
                  {/* Hover overlay */}
                  <div
                    className="absolute inset-0 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                    style={{ background: "rgba(0,0,0,.6)" }}
                  >
                    <Camera size={18} style={{ color: "#fff" }} />
                  </div>
                  {/* Ring glow on hover */}
                  <div
                    className="absolute inset-0 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                    style={{ boxShadow: "0 0 0 3px rgba(200,162,74,.4)" }}
                  />
                </div>

                {/* Info block */}
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1.5">
                    <h2 className="text-xl font-semibold" style={{ color: "#E6EAF0" }}>{USER.name}</h2>
                    <RoleBadge role={USER.role} />
                  </div>
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <UnitChip unit={USER.unit} />
                    <span className="text-xs font-mono" style={{ color: "#4A5568" }}>{USER.id}</span>
                  </div>
                  <p className="text-xs font-mono" style={{ color: "#8A94A6" }}>{USER.email}</p>
                </div>

                {/* Active status pill */}
                <div className="flex-shrink-0 self-start sm:self-auto">
                  <span
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border"
                    style={{ color: "#3FB950", background: "rgba(63,185,80,.08)", borderColor: "rgba(63,185,80,.2)" }}
                  >
                    <span className="w-1.5 h-1.5 rounded-full inline-block animate-pulse" style={{ background: "#3FB950" }} />
                    {USER.status}
                  </span>
                </div>
              </div>
            </div>

            {/* ── Two-column layout ───────────────────────────────── */}
            <div className="flex gap-6 items-start">
              {/* Section nav (sticky, desktop only) */}
              <div className="hidden md:block w-44 flex-shrink-0 sticky top-6">
                <div
                  className="rounded-xl border overflow-hidden"
                  style={{ background: "#161D26", borderColor: "rgba(255,255,255,.07)" }}
                >
                  <div className="px-4 py-3 border-b" style={{ borderColor: "rgba(255,255,255,.07)" }}>
                    <span className="text-[10px] font-semibold tracking-widest uppercase" style={{ color: "#8A94A6" }}>
                      Sections
                    </span>
                  </div>
                  <nav className="p-2">
                    {SECTIONS.map(s => {
                      const isActive = activeSection === s.id;
                      return (
                        <button
                          key={s.id}
                          onClick={() => scrollTo(s.id)}
                          className="w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-all mb-0.5"
                          style={{
                            color:        isActive ? "#C8A24A" : "#8A94A6",
                            background:   isActive ? "rgba(200,162,74,.1)" : "transparent",
                            borderLeft:   `2px solid ${isActive ? "#C8A24A" : "transparent"}`,
                            paddingLeft:  isActive ? "10px" : "12px",
                          }}
                          onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = "rgba(255,255,255,.04)"; }}
                          onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = "transparent"; }}
                        >
                          {s.label}
                        </button>
                      );
                    })}
                  </nav>
                </div>

                {/* Operational hint */}
                <div
                  className="mt-4 rounded-xl border p-4"
                  style={{ background: "rgba(200,162,74,.04)", borderColor: "rgba(200,162,74,.12)" }}
                >
                  <Shield size={14} style={{ color: "#C8A24A" }} className="mb-2" />
                  <p className="text-[11px] leading-relaxed" style={{ color: "#8A94A6" }}>
                    Changes to email, unit, and role require administrator authorization.
                  </p>
                </div>
              </div>

              {/* Cards stack */}
              <div className="flex-1 min-w-0 flex flex-col gap-6">
                <ProfileDetailsCard />
                <AvatarUploadCard avatarUrl={avatarUrl} onAvatarChange={setAvatarUrl} />
                <ChangePasswordCard />
                <AccountSecurityCard />
              </div>
            </div>

          </div>
        </main>
      </div>
    </div>
  );
}
