import { useState, useCallback } from "react";
import {
  Eye,
  EyeOff,
  Mail,
  Lock,
  AlertCircle,
  CheckCircle2,
  XCircle,
  ArrowLeft,
  Loader2,
  Shield,
  Check,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

type Screen =
  | "login"
  | "forgot"
  | "reset-confirm"
  | "activation"
  | "force-change";

type ActivationVariant = "loading" | "success" | "failure";
type ResetVariant = "form" | "expired";
type ForgotVariant = "form" | "sent";

// ─── Utility ──────────────────────────────────────────────────────────────────

function cn(...classes: (string | undefined | false | null)[]) {
  return classes.filter(Boolean).join(" ");
}

// ─── Logo ─────────────────────────────────────────────────────────────────────

function LogoMark() {
  return (
    <svg
      width="40"
      height="40"
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {/* Outer ring */}
      <circle cx="20" cy="20" r="19" stroke="#C8A24A" strokeWidth="1.5" strokeDasharray="3 2" />
      {/* Inner ring */}
      <circle cx="20" cy="20" r="13" stroke="#C8A24A" strokeWidth="1" opacity="0.4" />
      {/* Crosshair lines */}
      <line x1="20" y1="1" x2="20" y2="8" stroke="#C8A24A" strokeWidth="1.5" />
      <line x1="20" y1="32" x2="20" y2="39" stroke="#C8A24A" strokeWidth="1.5" />
      <line x1="1" y1="20" x2="8" y2="20" stroke="#C8A24A" strokeWidth="1.5" />
      <line x1="32" y1="20" x2="39" y2="20" stroke="#C8A24A" strokeWidth="1.5" />
      {/* Center mark */}
      <circle cx="20" cy="20" r="3" fill="#C8A24A" />
      {/* Drone silhouette - simple quad arms */}
      <line x1="20" y1="20" x2="14" y2="14" stroke="#C8A24A" strokeWidth="1" opacity="0.7" />
      <line x1="20" y1="20" x2="26" y2="14" stroke="#C8A24A" strokeWidth="1" opacity="0.7" />
      <line x1="20" y1="20" x2="14" y2="26" stroke="#C8A24A" strokeWidth="1" opacity="0.7" />
      <line x1="20" y1="20" x2="26" y2="26" stroke="#C8A24A" strokeWidth="1" opacity="0.7" />
      <circle cx="13" cy="13" r="2" stroke="#C8A24A" strokeWidth="1" opacity="0.6" />
      <circle cx="27" cy="13" r="2" stroke="#C8A24A" strokeWidth="1" opacity="0.6" />
      <circle cx="13" cy="27" r="2" stroke="#C8A24A" strokeWidth="1" opacity="0.6" />
      <circle cx="27" cy="27" r="2" stroke="#C8A24A" strokeWidth="1" opacity="0.6" />
    </svg>
  );
}

// ─── Alert Banner ──────────────────────────────────────────────────────────────

type AlertVariant = "error" | "success" | "info";

interface AlertBannerProps {
  variant: AlertVariant;
  message: string;
}

function AlertBanner({ variant, message }: AlertBannerProps) {
  const styles: Record<AlertVariant, string> = {
    error: "bg-[#E5484D]/10 border-[#E5484D]/30 text-[#E5484D]",
    success: "bg-[#3FB950]/10 border-[#3FB950]/30 text-[#3FB950]",
    info: "bg-[#C8A24A]/10 border-[#C8A24A]/30 text-[#C8A24A]",
  };
  const icons = {
    error: <AlertCircle size={15} className="shrink-0 mt-px" />,
    success: <CheckCircle2 size={15} className="shrink-0 mt-px" />,
    info: <AlertCircle size={15} className="shrink-0 mt-px" />,
  };
  return (
    <div className={cn("flex items-start gap-2.5 rounded-lg border px-3.5 py-3 text-sm", styles[variant])}>
      {icons[variant]}
      <span>{message}</span>
    </div>
  );
}

// ─── Text Input ───────────────────────────────────────────────────────────────

interface TextInputProps {
  id: string;
  label: string;
  type?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  error?: string;
  disabled?: boolean;
  icon?: React.ReactNode;
  rightElement?: React.ReactNode;
  autoComplete?: string;
}

function TextInput({
  id,
  label,
  type = "text",
  value,
  onChange,
  placeholder,
  error,
  disabled,
  icon,
  rightElement,
  autoComplete,
}: TextInputProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={id}
        className="text-xs font-semibold uppercase tracking-wider text-[#8A94A6]"
      >
        {label}
      </label>
      <div className="relative">
        {icon && (
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8A94A6] pointer-events-none">
            {icon}
          </span>
        )}
        <input
          id={id}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          autoComplete={autoComplete}
          className={cn(
            "w-full rounded-lg bg-[#1E2733] text-[#E6EAF0] placeholder-[#4A5568]",
            "text-sm py-2.5 transition-all duration-150",
            "border focus:outline-none",
            icon ? "pl-9 pr-4" : "px-4",
            rightElement ? "pr-10" : "",
            error
              ? "border-[#E5484D]/50 focus:border-[#E5484D] focus:ring-2 focus:ring-[#E5484D]/20"
              : "border-white/8 focus:border-[#C8A24A]/60 focus:ring-2 focus:ring-[#C8A24A]/15",
            disabled ? "opacity-40 cursor-not-allowed" : "cursor-text"
          )}
        />
        {rightElement && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2">
            {rightElement}
          </span>
        )}
      </div>
      {error && (
        <p className="text-xs text-[#E5484D] flex items-center gap-1">
          <AlertCircle size={11} />
          {error}
        </p>
      )}
    </div>
  );
}

// ─── Password Input ───────────────────────────────────────────────────────────

interface PasswordInputProps {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  error?: string;
  disabled?: boolean;
  autoComplete?: string;
}

function PasswordInput({ id, label, value, onChange, placeholder, error, disabled, autoComplete }: PasswordInputProps) {
  const [show, setShow] = useState(false);
  return (
    <TextInput
      id={id}
      label={label}
      type={show ? "text" : "password"}
      value={value}
      onChange={onChange}
      placeholder={placeholder ?? "••••••••"}
      error={error}
      disabled={disabled}
      autoComplete={autoComplete}
      icon={<Lock size={15} />}
      rightElement={
        <button
          type="button"
          onClick={() => setShow((s) => !s)}
          className="text-[#8A94A6] hover:text-[#C8A24A] transition-colors"
          tabIndex={-1}
          aria-label={show ? "Hide password" : "Show password"}
        >
          {show ? <EyeOff size={15} /> : <Eye size={15} />}
        </button>
      }
    />
  );
}

// ─── Primary Button ───────────────────────────────────────────────────────────

interface PrimaryButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  type?: "button" | "submit";
  loading?: boolean;
  disabled?: boolean;
  className?: string;
}

function PrimaryButton({ children, onClick, type = "button", loading, disabled, className }: PrimaryButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={cn(
        "w-full flex items-center justify-center gap-2",
        "rounded-lg bg-[#C8A24A] text-[#0B0F14] font-semibold text-sm",
        "py-2.5 px-4 transition-all duration-150",
        "hover:bg-[#D4AD57] active:bg-[#B8922A]",
        "focus:outline-none focus:ring-2 focus:ring-[#C8A24A]/40 focus:ring-offset-2 focus:ring-offset-[#161D26]",
        (disabled || loading) ? "opacity-50 cursor-not-allowed" : "cursor-pointer",
        className
      )}
    >
      {loading && <Loader2 size={15} className="animate-spin" />}
      {children}
    </button>
  );
}

// ─── Ghost Button ─────────────────────────────────────────────────────────────

function GhostButton({ children, onClick, icon }: { children: React.ReactNode; onClick?: () => void; icon?: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex items-center gap-1.5 text-sm text-[#8A94A6] hover:text-[#C8A24A] transition-colors duration-150 group"
    >
      {icon}
      {children}
    </button>
  );
}

// ─── Password Strength ────────────────────────────────────────────────────────

interface Requirement {
  label: string;
  met: boolean;
}

function getStrength(password: string): { score: number; requirements: Requirement[] } {
  const requirements: Requirement[] = [
    { label: "At least 12 characters", met: password.length >= 12 },
    { label: "Uppercase letter (A–Z)", met: /[A-Z]/.test(password) },
    { label: "Lowercase letter (a–z)", met: /[a-z]/.test(password) },
    { label: "Number (0–9)", met: /[0-9]/.test(password) },
    { label: "Special character (!@#$…)", met: /[^A-Za-z0-9]/.test(password) },
  ];
  const score = requirements.filter((r) => r.met).length;
  return { score, requirements };
}

function PasswordStrength({ password }: { password: string }) {
  const { score, requirements } = getStrength(password);

  const segments = 5;
  const colors = ["#E5484D", "#E5484D", "#F59E0B", "#C8A24A", "#3FB950"];
  const labels = ["", "Very weak", "Weak", "Fair", "Strong", "Strong"];
  const activeColor = score > 0 ? colors[score - 1] : "transparent";

  return (
    <div className="flex flex-col gap-3">
      {/* Meter */}
      <div className="flex flex-col gap-1">
        <div className="flex gap-1">
          {Array.from({ length: segments }).map((_, i) => (
            <div
              key={i}
              className="h-1 flex-1 rounded-full transition-all duration-300"
              style={{
                backgroundColor: i < score ? activeColor : "rgba(255,255,255,0.08)",
              }}
            />
          ))}
        </div>
        {password.length > 0 && (
          <p className="text-xs" style={{ color: activeColor }}>
            {labels[score]}
          </p>
        )}
      </div>
      {/* Requirements */}
      <ul className="flex flex-col gap-1.5">
        {requirements.map((req) => (
          <li key={req.label} className="flex items-center gap-2 text-xs">
            {req.met ? (
              <Check size={12} className="text-[#3FB950] shrink-0" />
            ) : (
              <div className="w-3 h-3 rounded-full border border-white/20 shrink-0" />
            )}
            <span className={req.met ? "text-[#8A94A6]" : "text-[#4A5568]"}>{req.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ─── Loading Spinner ──────────────────────────────────────────────────────────

function Spinner({ size = 24 }: { size?: number }) {
  return <Loader2 size={size} className="animate-spin text-[#C8A24A]" />;
}

// ─── Card Shell ───────────────────────────────────────────────────────────────

function CardShell({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="w-full max-w-[440px] rounded-xl border bg-[#161D26] shadow-2xl"
      style={{
        borderColor: "rgba(255,255,255,0.08)",
        boxShadow: "0 0 0 1px rgba(200,162,74,0.06), 0 24px 64px rgba(0,0,0,0.6)",
      }}
    >
      {children}
    </div>
  );
}

// ─── Card Header (logo + wordmark) ────────────────────────────────────────────

function CardHeader() {
  return (
    <div className="flex flex-col items-center gap-3 px-8 pt-8 pb-6 border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
      <LogoMark />
      <div className="flex flex-col items-center gap-0.5">
        <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[#C8A24A]">
          Mission Control System
        </span>
        <span className="text-[11px] font-mono text-[#4A5568] tracking-wider uppercase">
          Drone Fleet Management
        </span>
      </div>
    </div>
  );
}

// ─── State 1: Login ───────────────────────────────────────────────────────────

function LoginState({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = useCallback(() => {
    if (!email || !password) {
      setError("Please enter your email and password.");
      return;
    }
    setError(null);
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setError("Invalid email or password.");
    }, 1400);
  }, [email, password]);

  return (
    <div className="px-8 py-7 flex flex-col gap-5">
      <div>
        <h1 className="text-xl font-semibold text-[#E6EAF0] tracking-tight">Sign in</h1>
      </div>

      {error && <AlertBanner variant="error" message={error} />}

      <div className="flex flex-col gap-4">
        <TextInput
          id="login-email"
          label="Email"
          type="email"
          value={email}
          onChange={setEmail}
          placeholder="operator@squadron.mil"
          error={error ? "" : undefined}
          icon={<Mail size={15} />}
          autoComplete="email"
        />
        <div className="flex flex-col gap-1.5">
          <PasswordInput
            id="login-password"
            label="Password"
            value={password}
            onChange={setPassword}
            error={error ? "" : undefined}
            autoComplete="current-password"
          />
          <div className="flex justify-end">
            <GhostButton onClick={() => onNavigate("forgot")}>
              Forgot password?
            </GhostButton>
          </div>
        </div>
      </div>

      <PrimaryButton loading={loading} onClick={handleSubmit}>
        Sign in
      </PrimaryButton>

      <p className="text-center text-xs text-[#4A5568] mt-1">
        Authorized personnel only — unauthorized access is prohibited.
      </p>
    </div>
  );
}

// ─── State 2: Forgot Password ─────────────────────────────────────────────────

function ForgotState({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [variant, setVariant] = useState<ForgotVariant>("form");

  const handleSubmit = useCallback(() => {
    if (!email) return;
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setVariant("sent");
    }, 1200);
  }, [email]);

  return (
    <div className="px-8 py-7 flex flex-col gap-5">
      <div>
        <h1 className="text-xl font-semibold text-[#E6EAF0] tracking-tight">Reset password</h1>
        <p className="text-sm text-[#8A94A6] mt-1">
          {"Enter your email and we'll send you a reset link."}
        </p>
      </div>

      {variant === "sent" && (
        <AlertBanner
          variant="success"
          message="If that email exists, a reset link has been sent."
        />
      )}

      {variant === "form" && (
        <>
          <TextInput
            id="forgot-email"
            label="Email"
            type="email"
            value={email}
            onChange={setEmail}
            placeholder="operator@squadron.mil"
            icon={<Mail size={15} />}
            autoComplete="email"
          />
          <PrimaryButton loading={loading} onClick={handleSubmit} disabled={!email}>
            Send reset link
          </PrimaryButton>
        </>
      )}

      <div className="flex items-center">
        <GhostButton onClick={() => onNavigate("login")} icon={<ArrowLeft size={14} />}>
          Back to sign in
        </GhostButton>
      </div>
    </div>
  );
}

// ─── State 3: Reset Password Confirm ──────────────────────────────────────────

function ResetConfirmState({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const [variant, setVariant] = useState<ResetVariant>("form");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [confirmError, setConfirmError] = useState("");

  const handleSubmit = useCallback(() => {
    if (newPassword !== confirmPassword) {
      setConfirmError("Passwords do not match.");
      return;
    }
    const { score } = getStrength(newPassword);
    if (score < 3) return;
    setConfirmError("");
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      onNavigate("login");
    }, 1400);
  }, [newPassword, confirmPassword, onNavigate]);

  const { score } = getStrength(newPassword);

  if (variant === "expired") {
    return (
      <div className="px-8 py-7 flex flex-col gap-5">
        <div>
          <h1 className="text-xl font-semibold text-[#E6EAF0] tracking-tight">Set a new password</h1>
        </div>
        <AlertBanner
          variant="error"
          message="This reset link is invalid or has expired."
        />
        <PrimaryButton onClick={() => onNavigate("forgot")}>
          Request a new link
        </PrimaryButton>
        <GhostButton onClick={() => onNavigate("login")} icon={<ArrowLeft size={14} />}>
          Back to sign in
        </GhostButton>
      </div>
    );
  }

  return (
    <div className="px-8 py-7 flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[#E6EAF0] tracking-tight">Set a new password</h1>
        <button
          type="button"
          onClick={() => setVariant("expired")}
          className="text-[10px] text-[#4A5568] hover:text-[#8A94A6] transition-colors border border-white/8 rounded px-2 py-1"
          title="Preview expired state"
        >
          Expired
        </button>
      </div>

      <div className="flex flex-col gap-4">
        <PasswordInput
          id="new-password"
          label="New password"
          value={newPassword}
          onChange={setNewPassword}
          autoComplete="new-password"
        />
        {newPassword.length > 0 && (
          <PasswordStrength password={newPassword} />
        )}
        <PasswordInput
          id="confirm-password"
          label="Confirm new password"
          value={confirmPassword}
          onChange={setConfirmPassword}
          error={confirmError}
          autoComplete="new-password"
        />
      </div>

      <PrimaryButton
        loading={loading}
        onClick={handleSubmit}
        disabled={!newPassword || !confirmPassword || score < 3}
      >
        Update password
      </PrimaryButton>

      <GhostButton onClick={() => onNavigate("login")} icon={<ArrowLeft size={14} />}>
        Back to sign in
      </GhostButton>
    </div>
  );
}

// ─── State 4: Account Activation ──────────────────────────────────────────────

function ActivationState({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const [variant, setVariant] = useState<ActivationVariant>("loading");

  // Simulate activation
  useState(() => {
    const timer = setTimeout(() => setVariant("success"), 2200);
    return () => clearTimeout(timer);
  });

  return (
    <div className="px-8 py-7 flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[#E6EAF0] tracking-tight">Activate your account</h1>
        {/* Preview toggles */}
        <div className="flex gap-1">
          {(["loading", "success", "failure"] as ActivationVariant[]).map((v) => (
            <button
              key={v}
              type="button"
              onClick={() => setVariant(v)}
              className={cn(
                "text-[10px] border border-white/8 rounded px-1.5 py-0.5 transition-colors",
                variant === v ? "text-[#C8A24A] border-[#C8A24A]/30" : "text-[#4A5568] hover:text-[#8A94A6]"
              )}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {variant === "loading" && (
        <div className="flex flex-col items-center gap-4 py-8">
          <Spinner size={32} />
          <p className="text-sm text-[#8A94A6]">Activating your account…</p>
        </div>
      )}

      {variant === "success" && (
        <div className="flex flex-col items-center gap-4 py-6">
          <div className="w-14 h-14 rounded-full bg-[#3FB950]/10 border border-[#3FB950]/20 flex items-center justify-center">
            <CheckCircle2 size={28} className="text-[#3FB950]" />
          </div>
          <div className="text-center">
            <p className="text-base font-semibold text-[#E6EAF0]">Your account is active</p>
            <p className="text-sm text-[#8A94A6] mt-1">You can now sign in to Mission Control.</p>
          </div>
          <PrimaryButton onClick={() => onNavigate("login")}>
            Continue to sign in
          </PrimaryButton>
        </div>
      )}

      {variant === "failure" && (
        <div className="flex flex-col items-center gap-4 py-6">
          <div className="w-14 h-14 rounded-full bg-[#E5484D]/10 border border-[#E5484D]/20 flex items-center justify-center">
            <XCircle size={28} className="text-[#E5484D]" />
          </div>
          <div className="text-center">
            <p className="text-base font-semibold text-[#E6EAF0]">Activation failed</p>
            <p className="text-sm text-[#8A94A6] mt-1">This activation link is invalid or has expired.</p>
          </div>
          <PrimaryButton onClick={() => onNavigate("forgot")}>
            Request a new link
          </PrimaryButton>
          <GhostButton onClick={() => onNavigate("login")} icon={<ArrowLeft size={14} />}>
            Back to sign in
          </GhostButton>
        </div>
      )}
    </div>
  );
}

// ─── State 5: Force Password Change ──────────────────────────────────────────

function ForceChangeState() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [confirmError, setConfirmError] = useState("");
  const [currentError, setCurrentError] = useState("");

  const { score } = getStrength(newPassword);

  const handleSubmit = useCallback(() => {
    if (!currentPassword) {
      setCurrentError("Current password is required.");
      return;
    }
    setCurrentError("");
    if (newPassword !== confirmPassword) {
      setConfirmError("Passwords do not match.");
      return;
    }
    if (score < 3) return;
    setConfirmError("");
    setLoading(true);
    setTimeout(() => setLoading(false), 1400);
  }, [currentPassword, newPassword, confirmPassword, score]);

  return (
    <div className="px-8 py-7 flex flex-col gap-5">
      {/* Mandatory badge */}
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#C8A24A]/8 border border-[#C8A24A]/15">
        <Shield size={14} className="text-[#C8A24A] shrink-0" />
        <span className="text-xs text-[#C8A24A] font-medium uppercase tracking-wider">Security Action Required</span>
      </div>

      <div>
        <h1 className="text-xl font-semibold text-[#E6EAF0] tracking-tight">Update your password to continue</h1>
        <p className="text-sm text-[#8A94A6] mt-1">
          For security, you must set a new password before proceeding.
        </p>
      </div>

      <div className="flex flex-col gap-4">
        <PasswordInput
          id="current-password"
          label="Current password"
          value={currentPassword}
          onChange={setCurrentPassword}
          error={currentError}
          autoComplete="current-password"
        />
        <PasswordInput
          id="force-new-password"
          label="New password"
          value={newPassword}
          onChange={setNewPassword}
          autoComplete="new-password"
        />
        {newPassword.length > 0 && (
          <PasswordStrength password={newPassword} />
        )}
        <PasswordInput
          id="force-confirm-password"
          label="Confirm new password"
          value={confirmPassword}
          onChange={setConfirmPassword}
          error={confirmError}
          autoComplete="new-password"
        />
      </div>

      <PrimaryButton
        loading={loading}
        onClick={handleSubmit}
        disabled={!currentPassword || !newPassword || !confirmPassword || score < 3}
      >
        Save and continue
      </PrimaryButton>

      <p className="text-center text-xs text-[#4A5568]">
        This step is mandatory and cannot be skipped.
      </p>
    </div>
  );
}

// ─── State Nav Bar (demo only) ────────────────────────────────────────────────

const SCREENS: { id: Screen; label: string }[] = [
  { id: "login", label: "Login" },
  { id: "forgot", label: "Forgot" },
  { id: "reset-confirm", label: "Reset" },
  { id: "activation", label: "Activation" },
  { id: "force-change", label: "Force Change" },
];

function StateNav({ current, onSelect }: { current: Screen; onSelect: (s: Screen) => void }) {
  return (
    <div className="flex flex-wrap gap-2 justify-center mb-8">
      {SCREENS.map((s) => (
        <button
          key={s.id}
          type="button"
          onClick={() => onSelect(s.id)}
          className={cn(
            "px-3 py-1.5 rounded text-xs font-mono uppercase tracking-wider transition-all duration-150",
            current === s.id
              ? "bg-[#C8A24A]/15 border border-[#C8A24A]/40 text-[#C8A24A]"
              : "border border-white/8 text-[#4A5568] hover:text-[#8A94A6] hover:border-white/15"
          )}
        >
          {s.label}
        </button>
      ))}
    </div>
  );
}

// ─── Background ───────────────────────────────────────────────────────────────

function Background() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden" style={{ backgroundColor: "#0B0F14" }}>
      {/* Grid texture */}
      <svg
        className="absolute inset-0 w-full h-full opacity-[0.035]"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#C8A24A" strokeWidth="0.5" />
          </pattern>
          <pattern id="cross" width="200" height="200" patternUnits="userSpaceOnUse">
            <line x1="100" y1="0" x2="100" y2="200" stroke="#C8A24A" strokeWidth="0.3" />
            <line x1="0" y1="100" x2="200" y2="100" stroke="#C8A24A" strokeWidth="0.3" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
        <rect width="100%" height="100%" fill="url(#cross)" opacity="0.4" />
      </svg>
      {/* Subtle radial glow */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 80% 60% at 50% 40%, rgba(200,162,74,0.04) 0%, transparent 70%)",
        }}
      />
      {/* Corner scan lines */}
      <div
        className="absolute top-0 left-0 w-64 h-64 opacity-10"
        style={{
          background:
            "linear-gradient(135deg, rgba(200,162,74,0.15) 0%, transparent 60%)",
        }}
      />
      <div
        className="absolute bottom-0 right-0 w-64 h-64 opacity-10"
        style={{
          background:
            "linear-gradient(315deg, rgba(200,162,74,0.15) 0%, transparent 60%)",
        }}
      />
    </div>
  );
}

// ─── App ──────────────────────────────────────────────────────────────────────

export default function App() {
  const [screen, setScreen] = useState<Screen>("login");

  const renderBody = () => {
    switch (screen) {
      case "login":
        return <LoginState onNavigate={setScreen} />;
      case "forgot":
        return <ForgotState onNavigate={setScreen} />;
      case "reset-confirm":
        return <ResetConfirmState onNavigate={setScreen} />;
      case "activation":
        return <ActivationState onNavigate={setScreen} />;
      case "force-change":
        return <ForceChangeState />;
    }
  };

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-4 py-12"
      style={{ fontFamily: "'IBM Plex Sans', system-ui, sans-serif" }}
    >
      <Background />

      {/* Demo state switcher */}
      <StateNav current={screen} onSelect={setScreen} />

      {/* Auth card */}
      <CardShell>
        <CardHeader />
        {renderBody()}
      </CardShell>

      {/* Classification footer */}
      <div className="mt-6 flex items-center gap-3">
        <div className="h-px w-12 bg-white/8" />
        <span className="text-[10px] font-mono text-[#2C3A4A] uppercase tracking-[0.2em]">
          UNCLASSIFIED // FOR OFFICIAL USE ONLY
        </span>
        <div className="h-px w-12 bg-white/8" />
      </div>
    </div>
  );
}
