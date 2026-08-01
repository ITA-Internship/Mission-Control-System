import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type {
  ChangeEvent,
  FormEvent,
} from "react";
import {
  Activity,
  AlertCircle,
  Bell,
  Camera,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Clock,
  Crosshair,
  Eye,
  EyeOff,
  LayoutDashboard,
  Lock,
  LogOut,
  Map,
  Navigation2,
  Settings,
  Shield,
  Target,
  Upload,
  User,
  Users,
  Wrench,
  X,
  BarChart3,
} from "lucide-react";
import {
  Link,
  useNavigate,
} from "react-router";

import {
  isAbortError,
} from "../../auth/api/apiClient";
import {
  changePassword,
  getCurrentUser,
} from "../../auth/api/authApi";
import { AuthAlert } from "../../auth/components/AuthAlert";
import {
  getApiFieldError,
  getFormError,
} from "../../auth/utils/authErrors";
import type { CurrentUser } from "../../auth/types/auth";
import { updateCurrentUserProfile } from "../api/profileApi";

type AvatarState =
  | "idle"
  | "dragging"
  | "uploading"
  | "success"
  | "error";

type ActiveSection =
  | "profile"
  | "avatar"
  | "password"
  | "security";

type PasswordVisibilityKey =
  | "current"
  | "next"
  | "confirm";

interface ProfileFormState {
  firstName: string;
  lastName: string;
  rank: string;
  contact: string;
}

interface PasswordFormState {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

const NAV_ITEMS = [
  {
    icon: LayoutDashboard,
    label: "Dashboard",
  },
  {
    icon: Map,
    label: "Fleet Map",
  },
  {
    icon: Navigation2,
    label: "Drone Fleet",
  },
  {
    icon: Target,
    label: "Missions",
  },
  {
    icon: Bell,
    label: "Alerts",
  },
  {
    icon: Users,
    label: "Operators",
  },
  {
    icon: Wrench,
    label: "Maintenance",
  },
  {
    icon: BarChart3,
    label: "Reports",
  },
  {
    icon: Settings,
    label: "Settings",
  },
];

const SECTIONS: Array<{
  id: ActiveSection;
  label: string;
}> = [
  {
    id: "profile",
    label: "Profile Details",
  },
  {
    id: "avatar",
    label: "Avatar",
  },
  {
    id: "password",
    label: "Change Password",
  },
  {
    id: "security",
    label: "Account & Security",
  },
];

function getInitials(user: CurrentUser): string {
  const first =
    user.first_name?.[0] ??
    user.username?.[0] ??
    "U";

  const last =
    user.last_name?.[0] ?? "";

  return `${first}${last}`.toUpperCase();
}

function getRoleLabel(user: CurrentUser): string {
  return (
    user.role_name ??
    user.role_code ??
    (user.role !== null
      ? `Role #${user.role}`
      : "Unassigned")
  );
}

function getUnitLabel(user: CurrentUser): string {
  if (user.unit_name && user.unit_code) {
    return `${user.unit_name}`;
  }

  if (user.unit_name) {
    return user.unit_name;
  }

  return user.unit !== null
    ? `Unit #${user.unit}`
    : "Not assigned";
}

function getUserIdentifier(user: CurrentUser): string {
  return `USR-${String(user.id).padStart(
    4,
    "0",
  )}`;
}

function formatDate(
  value: string | null | undefined,
): string | null {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      dateStyle: "medium",
    },
  ).format(parsed);
}

function formatDateTime(
  value: string | null | undefined,
): string | null {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(parsed);
}

function getProfileFormState(
  user: CurrentUser,
): ProfileFormState {
  return {
    firstName: user.first_name,
    lastName: user.last_name,
    rank: user.rank ?? "",
    contact: user.contact ?? "",
  };
}

function getStrength(password: string): {
  score: number;
  label: string;
  color: string;
} {
  if (!password) {
    return {
      score: 0,
      label: "",
      color: "transparent",
    };
  }

  let score = 0;

  if (password.length >= 8) {
    score += 1;
  }

  if (password.length >= 12) {
    score += 1;
  }

  if (/[A-Z]/.test(password)) {
    score += 1;
  }

  if (/[0-9]/.test(password)) {
    score += 1;
  }

  if (/[^A-Za-z0-9]/.test(password)) {
    score += 1;
  }

  const map = [
    {
      label: "Very Weak",
      color: "#E5484D",
    },
    {
      label: "Weak",
      color: "#F97316",
    },
    {
      label: "Fair",
      color: "#EAB308",
    },
    {
      label: "Strong",
      color: "#84CC16",
    },
    {
      label: "Very Strong",
      color: "#3FB950",
    },
  ];

  return {
    score,
    ...map[Math.min(score, 4)],
  };
}

function getPasswordRequirements(
  password: string,
) {
  return [
    {
      label: "At least 8 characters",
      ok: password.length >= 8,
    },
    {
      label: "Uppercase letter (A–Z)",
      ok: /[A-Z]/.test(password),
    },
    {
      label: "Lowercase letter (a–z)",
      ok: /[a-z]/.test(password),
    },
    {
      label: "Number (0–9)",
      ok: /[0-9]/.test(password),
    },
    {
      label: "Special character (!@#…)",
      ok: /[^A-Za-z0-9]/.test(password),
    },
  ];
}

function RoleBadge({
  role,
}: {
  role: string;
}) {
  return (
    <span
      className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold tracking-wide"
      style={{
        color: "#4C8DFF",
        background: "rgba(76,141,255,.13)",
        borderColor: "rgba(76,141,255,.3)",
      }}
    >
      {role}
    </span>
  );
}

function UnitChip({
  unit,
}: {
  unit: string;
}) {
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium"
      style={{
        color: "#8A94A6",
        background:
          "rgba(138,148,166,.08)",
        borderColor:
          "rgba(138,148,166,.2)",
      }}
    >
      <Shield size={10} />
      {unit}
    </span>
  );
}

function FieldLabel({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <label
      className="text-xs font-semibold tracking-widest uppercase"
      style={{
        color: "#8A94A6",
      }}
    >
      {children}
    </label>
  );
}

function Card({
  id,
  title,
  children,
  accent = false,
}: {
  id?: string;
  title: string;
  children: React.ReactNode;
  accent?: boolean;
}) {
  return (
    <div
      id={id}
      className="overflow-hidden rounded-xl border"
      style={{
        background: "#161D26",
        borderColor: accent
          ? "rgba(200,162,74,.18)"
          : "rgba(255,255,255,.07)",
      }}
    >
      {accent ? (
        <div
          className="h-px"
          style={{
            background:
              "linear-gradient(90deg, #C8A24A 0%, transparent 55%)",
          }}
        />
      ) : null}

      <div
        className="flex items-center gap-3 border-b px-6 py-4"
        style={{
          borderColor:
            "rgba(255,255,255,.07)",
        }}
      >
        <h2
          className="text-sm font-semibold tracking-wide"
          style={{
            color: "#E6EAF0",
          }}
        >
          {title}
        </h2>
      </div>

      <div className="px-6 py-5">
        {children}
      </div>
    </div>
  );
}

function PrimaryButton({
  children,
  onClick,
  loading = false,
  disabled = false,
  type = "button",
}: {
  children: React.ReactNode;
  onClick?: () => void;
  loading?: boolean;
  disabled?: boolean;
  type?: "button" | "submit";
}) {
  const isDisabled =
    disabled || loading;

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={isDisabled}
      className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition-all"
      style={{
        background: isDisabled
          ? "rgba(200,162,74,.35)"
          : "#C8A24A",
        color: "#0B0F14",
        cursor: isDisabled
          ? "not-allowed"
          : "pointer",
        opacity: isDisabled ? 0.7 : 1,
      }}
    >
      {loading ? (
        <svg
          className="h-3.5 w-3.5 animate-spin"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      ) : null}
      {children}
    </button>
  );
}

function SecondaryButton({
  children,
  onClick,
}: {
  children: React.ReactNode;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-all"
      style={{
        background:
          "rgba(255,255,255,.05)",
        color: "#E6EAF0",
        borderColor:
          "rgba(255,255,255,.1)",
      }}
    >
      {children}
    </button>
  );
}

function FormTextInput({
  value,
  onChange,
  placeholder = "",
  type = "text",
  disabled = false,
  error,
  rightElement,
  inputRef,
  autoComplete,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: string;
  disabled?: boolean;
  error?: string;
  rightElement?: React.ReactNode;
  inputRef?: React.RefObject<HTMLInputElement | null>;
  autoComplete?: string;
}) {
  const [focused, setFocused] =
    useState(false);

  return (
    <div className="flex flex-col gap-1.5">
      <div className="relative">
        <input
          ref={inputRef}
          type={type}
          value={value}
          onChange={(event) =>
            onChange(event.target.value)
          }
          placeholder={placeholder}
          disabled={disabled}
          autoComplete={autoComplete}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          className="w-full rounded-lg px-3 py-2.5 text-sm outline-none transition-all"
          style={{
            background: disabled
              ? "rgba(15,22,32,.5)"
              : "#0F1620",
            color: disabled
              ? "#8A94A6"
              : "#E6EAF0",
            border: `1px solid ${
              error
                ? "#E5484D"
                : focused
                  ? "#C8A24A"
                  : "rgba(255,255,255,.1)"
            }`,
            paddingRight: rightElement
              ? "2.75rem"
              : undefined,
            boxShadow:
              focused && !error
                ? "0 0 0 2px rgba(200,162,74,.12)"
                : undefined,
          }}
          aria-invalid={Boolean(error)}
        />

        {rightElement ? (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            {rightElement}
          </div>
        ) : null}
      </div>

      {error ? (
        <p
          className="text-xs"
          style={{
            color: "#E5484D",
          }}
          role="alert"
        >
          {error}
        </p>
      ) : null}
    </div>
  );
}

function AlertBanner({
  type,
  message,
  onClose,
}: {
  type: "error" | "success" | "info";
  message: string;
  onClose?: () => void;
}) {
  const config = {
    error: {
      bg: "rgba(229,72,77,.1)",
      border: "rgba(229,72,77,.3)",
      color: "#E5484D",
      Icon: AlertCircle,
    },
    success: {
      bg: "rgba(63,185,80,.1)",
      border: "rgba(63,185,80,.3)",
      color: "#3FB950",
      Icon: CheckCircle,
    },
    info: {
      bg: "rgba(138,148,166,.1)",
      border: "rgba(138,148,166,.3)",
      color: "#8A94A6",
      Icon: AlertCircle,
    },
  }[type];

  const Icon = config.Icon;

  return (
    <div
      className="flex items-start gap-3 rounded-lg border p-3 text-sm"
      style={{
        background: config.bg,
        borderColor: config.border,
      }}
      role={type === "error" ? "alert" : "status"}
      aria-live={
        type === "error"
          ? "assertive"
          : "polite"
      }
    >
      <Icon
        size={15}
        style={{
          color: config.color,
          flexShrink: 0,
          marginTop: 1,
        }}
        aria-hidden="true"
      />

      <span
        className="flex-1 text-sm"
        style={{
          color: config.color,
        }}
      >
        {message}
      </span>

      {onClose ? (
        <button
          onClick={onClose}
          style={{
            color: config.color,
            flexShrink: 0,
          }}
          aria-label="Dismiss message"
        >
          <X size={14} />
        </button>
      ) : null}
    </div>
  );
}

export function MyProfilePage() {
  const navigate = useNavigate();

  const [currentUser, setCurrentUser] =
    useState<CurrentUser | null>(null);
  const [loading, setLoading] =
    useState(true);
  const [loadError, setLoadError] =
    useState<string | null>(null);
  const [activeSection, setActiveSection] =
    useState<ActiveSection>("profile");
  const [sidebarOpen, setSidebarOpen] =
    useState(false);
  const [userMenuOpen, setUserMenuOpen] =
    useState(false);
  const [avatarState, setAvatarState] =
    useState<AvatarState>("idle");
  const [avatarError, setAvatarError] =
    useState("");
  const [avatarFile, setAvatarFile] =
    useState<File | null>(null);
  const [profileMode, setProfileMode] =
    useState<"read" | "edit" | "saving">(
      "read",
    );
  const [profileForm, setProfileForm] =
    useState<ProfileFormState>({
      firstName: "",
      lastName: "",
      rank: "",
      contact: "",
    });
  const [profileErrors, setProfileErrors] =
    useState<Record<string, string>>({});
  const [profileBanner, setProfileBanner] =
    useState<{
      type: "success" | "error";
      message: string;
    } | null>(null);
  const [passwordForm, setPasswordForm] =
    useState<PasswordFormState>({
      currentPassword: "",
      newPassword: "",
      confirmPassword: "",
    });
  const [passwordErrors, setPasswordErrors] =
    useState<Record<string, string>>({});
  const [passwordBanner, setPasswordBanner] =
    useState<{
      type: "success" | "error";
      message: string;
    } | null>(null);
  const [passwordStatus, setPasswordStatus] =
    useState<"idle" | "saving">("idle");
  const [passwordVisibility, setPasswordVisibility] =
    useState<
      Record<PasswordVisibilityKey, boolean>
    >({
      current: false,
      next: false,
      confirm: false,
    });

  const menuRef =
    useRef<HTMLDivElement>(null);
  const fileInputRef =
    useRef<HTMLInputElement>(null);
  const firstEditableFieldRef =
    useRef<HTMLInputElement>(null);
  const currentPasswordRef =
    useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!userMenuOpen) {
      return undefined;
    }

    function handleOutsideClick(
      event: MouseEvent,
    ) {
      if (
        menuRef.current &&
        !menuRef.current.contains(
          event.target as Node,
        )
      ) {
        setUserMenuOpen(false);
      }
    }

    document.addEventListener(
      "mousedown",
      handleOutsideClick,
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleOutsideClick,
      );
    };
  }, [userMenuOpen]);

  useEffect(() => {
    const controller =
      new AbortController();

    async function loadCurrentUserData() {
      try {
        setLoading(true);
        setLoadError(null);

        const user =
          await getCurrentUser(
            controller.signal,
          );

        if (user.must_change_password) {
          navigate(
            "/change-password/required",
            {
              replace: true,
            },
          );
          return;
        }

        setCurrentUser(user);
        setProfileForm(
          getProfileFormState(user),
        );
      } catch (error) {
        if (isAbortError(error)) {
          return;
        }

        const message = getFormError(
          error,
          "We could not load your profile right now.",
        );

        setLoadError(message);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadCurrentUserData();

    return () => {
      controller.abort();
    };
  }, [navigate]);

  const avatarPreview = useMemo(() => {
    if (!avatarFile) {
      return null;
    }

    return URL.createObjectURL(avatarFile);
  }, [avatarFile]);

  useEffect(() => {
    return () => {
      if (avatarPreview) {
        URL.revokeObjectURL(avatarPreview);
      }
    };
  }, [avatarPreview]);

  const avatarUrl = useMemo(() => {
    return (
      avatarPreview ??
      currentUser?.profile_picture ??
      null
    );
  }, [avatarPreview, currentUser]);

  const strength = getStrength(
    passwordForm.newPassword,
  );

  const passwordRequirements =
    getPasswordRequirements(
      passwordForm.newPassword,
    );

  const createdAtLabel = formatDate(
    currentUser?.created_at,
  );
  const lastLoginLabel = formatDateTime(
    currentUser?.last_login,
  );

  function setProfileField(
    key: keyof ProfileFormState,
    value: string,
  ) {
    setProfileForm((current) => ({
      ...current,
      [key]: value,
    }));

    setProfileErrors((current) => ({
      ...current,
      [key]: "",
    }));
    setProfileBanner(null);
  }

  function setPasswordField(
    key: keyof PasswordFormState,
    value: string,
  ) {
    setPasswordForm((current) => ({
      ...current,
      [key]: value,
    }));

    setPasswordErrors((current) => ({
      ...current,
      [key]: "",
    }));
    setPasswordBanner(null);
  }

  function scrollToSection(
    section: ActiveSection,
  ) {
    setActiveSection(section);
    setSidebarOpen(false);
    document
      .getElementById(section)
      ?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
  }

  function enterProfileEditMode() {
    setProfileMode("edit");
    setProfileBanner(null);
    setTimeout(() => {
      firstEditableFieldRef.current?.focus();
    }, 0);
  }

  function cancelProfileEdit() {
    if (!currentUser) {
      return;
    }

    setProfileForm(
      getProfileFormState(currentUser),
    );
    setAvatarFile(null);
    setAvatarError("");
    setAvatarState("idle");
    setProfileErrors({});
    setProfileBanner(null);
    setProfileMode("read");
  }

  function validateProfileForm() {
    const nextErrors: Record<
      string,
      string
    > = {};

    if (!profileForm.firstName.trim()) {
      nextErrors.firstName =
        "First name is required.";
    }

    if (!profileForm.lastName.trim()) {
      nextErrors.lastName =
        "Last name is required.";
    }

    return nextErrors;
  }

  async function handleProfileSave() {
    if (!currentUser) {
      return;
    }

    const nextErrors =
      validateProfileForm();

    if (Object.keys(nextErrors).length > 0) {
      setProfileErrors(nextErrors);
      firstEditableFieldRef.current?.focus();
      return;
    }

    setProfileMode("saving");
    setProfileBanner(null);
    setProfileErrors({});

    try {
      const updatedUser =
        await updateCurrentUserProfile({
          firstName:
            profileForm.firstName.trim(),
          lastName:
            profileForm.lastName.trim(),
          rank: profileForm.rank.trim(),
          contact:
            profileForm.contact.trim(),
          profilePicture: avatarFile,
        });

      setCurrentUser(updatedUser);
      setProfileForm(
        getProfileFormState(updatedUser),
      );
      setAvatarFile(null);
      setAvatarError("");
      setAvatarState("success");
      setProfileBanner({
        type: "success",
        message:
          "Profile changes saved successfully.",
      });
      setProfileMode("read");
    } catch (error) {
      setProfileErrors({
        firstName:
          getApiFieldError(
            error,
            "first_name",
          ) ?? "",
        lastName:
          getApiFieldError(
            error,
            "last_name",
          ) ?? "",
        rank:
          getApiFieldError(
            error,
            "rank",
          ) ?? "",
        contact:
          getApiFieldError(
            error,
            "contact",
          ) ?? "",
        profile_picture:
          getApiFieldError(
            error,
            "profile_picture",
          ) ?? "",
      });
      setProfileBanner({
        type: "error",
        message: getFormError(
          error,
          "We could not save your profile changes.",
        ),
      });
      setProfileMode("edit");
    }
  }

  function validatePasswordForm() {
    const nextErrors: Record<
      string,
      string
    > = {};

    if (!passwordForm.currentPassword) {
      nextErrors.currentPassword =
        "Current password is required.";
    }

    if (!passwordForm.newPassword) {
      nextErrors.newPassword =
        "New password is required.";
    }

    if (!passwordForm.confirmPassword) {
      nextErrors.confirmPassword =
        "Please confirm your new password.";
    } else if (
      passwordForm.newPassword !==
      passwordForm.confirmPassword
    ) {
      nextErrors.confirmPassword =
        "Passwords do not match.";
    }

    return nextErrors;
  }

  async function handlePasswordSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const nextErrors =
      validatePasswordForm();

    if (Object.keys(nextErrors).length > 0) {
      setPasswordErrors(nextErrors);
      currentPasswordRef.current?.focus();
      return;
    }

    setPasswordStatus("saving");
    setPasswordBanner(null);
    setPasswordErrors({});

    try {
      const response =
        await changePassword(
          passwordForm.currentPassword,
          passwordForm.newPassword,
        );

      setPasswordBanner({
        type: "success",
        message: response.detail,
      });
      setPasswordForm({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      });
    } catch (error) {
      setPasswordErrors({
        currentPassword:
          getApiFieldError(
            error,
            "old_password",
          ) ?? "",
        newPassword:
          getApiFieldError(
            error,
            "new_password",
          ) ?? "",
        confirmPassword: "",
      });
      setPasswordBanner({
        type: "error",
        message: getFormError(
          error,
          "We could not update your password.",
        ),
      });
    } finally {
      setPasswordStatus("idle");
    }
  }

  function handleAvatarFile(
    file: File,
  ) {
    const allowed = new Set([
      "image/jpeg",
      "image/png",
      "image/webp",
    ]);

    if (!allowed.has(file.type)) {
      setAvatarState("error");
      setAvatarError(
        "Invalid file type. Accepted: JPG, PNG, WEBP.",
      );
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setAvatarState("error");
      setAvatarError(
        "File too large. Maximum size is 5 MB.",
      );
      return;
    }

    setAvatarError("");
    setAvatarState("uploading");

    window.setTimeout(() => {
      setAvatarFile(file);
      setAvatarState("success");
    }, 250);
  }

  function handleAvatarDrop(
    event: React.DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault();
    setAvatarState("idle");
    const file =
      event.dataTransfer.files?.[0];

    if (file) {
      handleAvatarFile(file);
    }
  }

  function handleAvatarInputChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const file =
      event.target.files?.[0];

    if (file) {
      handleAvatarFile(file);
    }

    event.target.value = "";
  }

  if (loading) {
    return (
      <div
        className="flex min-h-screen items-center justify-center"
        style={{
          background: "#0B0F14",
          color: "#E6EAF0",
        }}
      >
        <div
          className="rounded-xl border px-6 py-4 text-sm"
          style={{
            background: "#161D26",
            borderColor:
              "rgba(255,255,255,.08)",
          }}
        >
          Loading profile…
        </div>
      </div>
    );
  }

  if (!currentUser || loadError) {
    return (
      <div
        className="flex min-h-screen items-center justify-center px-6"
        style={{
          background: "#0B0F14",
        }}
      >
        <div
          className="flex max-w-md flex-col gap-4 rounded-xl border p-6"
          style={{
            background: "#161D26",
            borderColor:
              "rgba(255,255,255,.08)",
          }}
        >
          <AuthAlert variant="error">
            {loadError ??
              "Profile data is unavailable."}
          </AuthAlert>

          <Link
            to="/login"
            className="text-sm font-medium"
            style={{
              color: "#C8A24A",
            }}
          >
            Return to sign in
          </Link>
        </div>
      </div>
    );
  }

  const profileSaving =
    profileMode === "saving";
  const profileEditing =
    profileMode === "edit";
  const avatarDisplay =
    avatarUrl || null;

  return (
    <div
      className="flex h-screen overflow-hidden"
      style={{
        background: "#0B0F14",
        fontFamily:
          "'Inter', -apple-system, sans-serif",
      }}
    >
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-60 flex-col border-r transition-transform duration-200 lg:static lg:z-auto lg:translate-x-0 ${
          sidebarOpen
            ? "translate-x-0"
            : "-translate-x-full"
        }`}
        style={{
          background: "#0D1219",
          borderColor:
            "rgba(255,255,255,.07)",
        }}
      >
        <div
          className="flex h-14 flex-shrink-0 items-center gap-3 border-b px-5"
          style={{
            borderColor:
              "rgba(255,255,255,.07)",
          }}
        >
          <div
            className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded"
            style={{
              background:
                "rgba(200,162,74,.13)",
              border:
                "1px solid rgba(200,162,74,.28)",
            }}
          >
            <Crosshair
              size={14}
              style={{
                color: "#C8A24A",
              }}
            />
          </div>
          <div className="leading-none">
            <div
              className="text-xs font-bold uppercase tracking-widest"
              style={{
                color: "#E6EAF0",
              }}
            >
              Mission
            </div>
            <div
              className="mt-0.5 text-[10px] tracking-widest"
              style={{
                color: "#8A94A6",
              }}
            >
              CONTROL SYSTEM
            </div>
          </div>
        </div>

        <nav
          className="flex-1 overflow-y-auto px-2 py-3"
          style={{
            scrollbarWidth: "none",
          }}
        >
          <p
            className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest"
            style={{
              color: "#4A5568",
            }}
          >
            Navigation
          </p>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.label}
                className="mb-0.5 flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-all"
                style={{
                  color: "#8A94A6",
                  background: "transparent",
                }}
              >
                <Icon size={15} />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div
          className="border-t px-4 py-4"
          style={{
            borderColor:
              "rgba(255,255,255,.07)",
          }}
        >
          <div className="flex items-center gap-3">
            <div
              className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold"
              style={{
                background:
                  "rgba(200,162,74,.13)",
                color: "#C8A24A",
                border:
                  "1px solid rgba(200,162,74,.25)",
              }}
            >
              {getInitials(currentUser)}
            </div>
            <div className="min-w-0">
              <div
                className="truncate text-xs font-semibold"
                style={{
                  color: "#E6EAF0",
                }}
              >
                {currentUser.rank
                  ? `${currentUser.rank} ${currentUser.first_name?.[0]}. ${currentUser.last_name}`
                  : `${currentUser.first_name} ${currentUser.last_name}`}
              </div>
              <div
                className="truncate text-xs"
                style={{
                  color: "#8A94A6",
                }}
              >
                {getUnitLabel(currentUser)}
              </div>
            </div>
          </div>
        </div>
      </aside>

      {sidebarOpen ? (
        <div
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <header
          className="flex h-14 flex-shrink-0 items-center justify-between border-b px-5"
          style={{
            background: "#0D1219",
            borderColor:
              "rgba(255,255,255,.07)",
          }}
        >
          <div className="flex items-center gap-3">
            <button
              className="lg:hidden"
              onClick={() =>
                setSidebarOpen((current) => !current)
              }
              style={{
                color: "#8A94A6",
              }}
              aria-label="Toggle navigation"
            >
              <LayoutDashboard size={20} />
            </button>
            <nav
              className="flex items-center gap-1.5 text-xs"
              style={{
                color: "#8A94A6",
              }}
            >
              <span>Home</span>
              <ChevronRight size={11} />
              <span
                style={{
                  color: "#E6EAF0",
                }}
              >
                My Profile
              </span>
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <button
              className="relative"
              style={{
                color: "#8A94A6",
              }}
              aria-label="Notifications"
            >
              <Bell size={17} />
              <span
                className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full"
                style={{
                  background: "#E5484D",
                }}
              />
            </button>

            <div
              className="relative"
              ref={menuRef}
            >
              <button
                onClick={() =>
                  setUserMenuOpen(
                    (current) => !current,
                  )
                }
                className="flex items-center gap-2 rounded-lg px-3 py-1.5 transition-all"
                style={{
                  background:
                    "rgba(255,255,255,.04)",
                  border:
                    "1px solid rgba(255,255,255,.08)",
                }}
              >
                <div
                  className="flex h-6 w-6 items-center justify-center overflow-hidden rounded-full text-xs font-bold"
                  style={{
                    background:
                      "rgba(200,162,74,.13)",
                    color: "#C8A24A",
                  }}
                >
                  {avatarDisplay ? (
                    <img
                      src={avatarDisplay}
                      alt="Profile avatar"
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    getInitials(currentUser)
                  )}
                </div>
                <span
                  className="hidden text-xs font-medium sm:block"
                  style={{
                    color: "#E6EAF0",
                  }}
                >
                  {currentUser.rank
                    ? `${currentUser.rank} ${currentUser.last_name}`
                    : `${currentUser.first_name} ${currentUser.last_name}`}
                </span>
                <ChevronDown
                  size={12}
                  style={{
                    color: "#8A94A6",
                  }}
                />
              </button>

              {userMenuOpen ? (
                <div
                  className="absolute right-0 top-full z-50 mt-2 w-56 overflow-hidden rounded-xl border shadow-2xl"
                  style={{
                    background: "#161D26",
                    borderColor:
                      "rgba(255,255,255,.1)",
                  }}
                >
                  <div
                    className="border-b px-4 py-3"
                    style={{
                      borderColor:
                        "rgba(255,255,255,.07)",
                    }}
                  >
                    <div
                      className="text-sm font-semibold"
                      style={{
                        color: "#E6EAF0",
                      }}
                    >
                      {currentUser.first_name}{" "}
                      {currentUser.last_name}
                    </div>
                    <div
                      className="mt-0.5 text-xs font-mono"
                      style={{
                        color: "#8A94A6",
                      }}
                    >
                      {currentUser.email}
                    </div>
                    <div className="mt-2 flex items-center gap-2">
                      <RoleBadge
                        role={getRoleLabel(
                          currentUser,
                        )}
                      />
                      <UnitChip
                        unit={getUnitLabel(
                          currentUser,
                        )}
                      />
                    </div>
                  </div>
                  <div className="p-2">
                    <button
                      className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm transition-all"
                      style={{
                        color: "#E6EAF0",
                      }}
                    >
                      <User
                        size={13}
                        style={{
                          color: "#C8A24A",
                        }}
                      />
                      My Profile
                    </button>
                    <button
                      className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm transition-all"
                      style={{
                        color: "#E6EAF0",
                      }}
                    >
                      <Settings
                        size={13}
                        style={{
                          color: "#8A94A6",
                        }}
                      />
                      Settings
                    </button>
                    <div
                      className="my-1 border-t"
                      style={{
                        borderColor:
                          "rgba(255,255,255,.07)",
                      }}
                    />
                    <button
                      className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm transition-all"
                      style={{
                        color: "#E5484D",
                      }}
                    >
                      <LogOut size={13} />
                      Sign Out
                    </button>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        </header>

        <main
          className="flex-1 overflow-y-auto"
          style={{
            scrollbarWidth: "none",
          }}
        >
          <div className="mx-auto max-w-[960px] px-6 py-8">
            <div className="mb-7">
              <h1
                className="text-2xl font-semibold"
                style={{
                  color: "#E6EAF0",
                }}
              >
                My Profile
              </h1>
              <p
                className="mt-1 text-sm"
                style={{
                  color: "#8A94A6",
                }}
              >
                Manage your personal information and account security settings.
              </p>
            </div>

            <div
              className="mb-8 overflow-hidden rounded-xl border"
              style={{
                background: "#161D26",
                borderColor:
                  "rgba(200,162,74,.15)",
                boxShadow:
                  "0 0 0 1px rgba(200,162,74,.05), 0 4px 24px rgba(0,0,0,.3)",
              }}
            >
              <div
                className="h-px"
                style={{
                  background:
                    "linear-gradient(90deg, #C8A24A 0%, rgba(200,162,74,.15) 50%, transparent 80%)",
                }}
              />

              <div className="flex flex-col items-start gap-5 px-6 py-6 sm:flex-row sm:items-center">
                <div
                  className="group relative flex-shrink-0 cursor-pointer"
                  onClick={() =>
                    scrollToSection("avatar")
                  }
                  title="Change avatar"
                >
                  <div
                    className="h-[76px] w-[76px] overflow-hidden rounded-full border-2"
                    style={{
                      borderColor:
                        "rgba(200,162,74,.35)",
                      background:
                        "rgba(200,162,74,.08)",
                    }}
                  >
                    {avatarDisplay ? (
                      <img
                        src={avatarDisplay}
                        alt="Profile"
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <div
                        className="flex h-full w-full items-center justify-center text-2xl font-bold"
                        style={{
                          color: "#C8A24A",
                        }}
                      >
                        {getInitials(currentUser)}
                      </div>
                    )}
                  </div>

                  <div
                    className="absolute inset-0 flex items-center justify-center rounded-full opacity-0 transition-opacity group-hover:opacity-100"
                    style={{
                      background:
                        "rgba(0,0,0,.6)",
                    }}
                  >
                    <Camera
                      size={18}
                      style={{
                        color: "#fff",
                      }}
                    />
                  </div>
                </div>

                <div className="min-w-0 flex-1">
                  <div className="mb-1.5 flex flex-wrap items-center gap-2">
                    <h2
                      className="text-xl font-semibold"
                      style={{
                        color: "#E6EAF0",
                      }}
                    >
                      {currentUser.rank
                        ? `${currentUser.rank} ${currentUser.first_name} ${currentUser.last_name}`
                        : `${currentUser.first_name} ${currentUser.last_name}`}
                    </h2>
                    <RoleBadge
                      role={getRoleLabel(
                        currentUser,
                      )}
                    />
                  </div>

                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <UnitChip
                      unit={getUnitLabel(
                        currentUser,
                      )}
                    />
                    <span
                      className="text-xs font-mono"
                      style={{
                        color: "#4A5568",
                      }}
                    >
                      {getUserIdentifier(
                        currentUser,
                      )}
                    </span>
                  </div>

                  <p
                    className="text-xs font-mono"
                    style={{
                      color: "#8A94A6",
                    }}
                  >
                    {currentUser.email}
                  </p>
                </div>

                <div className="flex-shrink-0 self-start sm:self-auto">
                  <span
                    className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold"
                    style={{
                      color: "#3FB950",
                      background:
                        "rgba(63,185,80,.08)",
                      borderColor:
                        "rgba(63,185,80,.2)",
                    }}
                  >
                    <span
                      className="inline-block h-1.5 w-1.5 animate-pulse rounded-full"
                      style={{
                        background: "#3FB950",
                      }}
                    />
                    {currentUser.is_active
                      ? "Active"
                      : "Inactive"}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-start gap-6">
              <div className="sticky top-6 hidden w-44 flex-shrink-0 md:block">
                <div
                  className="overflow-hidden rounded-xl border"
                  style={{
                    background: "#161D26",
                    borderColor:
                      "rgba(255,255,255,.07)",
                  }}
                >
                  <div
                    className="border-b px-4 py-3"
                    style={{
                      borderColor:
                        "rgba(255,255,255,.07)",
                    }}
                  >
                    <span
                      className="text-[10px] font-semibold uppercase tracking-widest"
                      style={{
                        color: "#8A94A6",
                      }}
                    >
                      Sections
                    </span>
                  </div>

                  <nav className="p-2">
                    {SECTIONS.map((section) => {
                      const isActive =
                        activeSection ===
                        section.id;

                      return (
                        <button
                          key={section.id}
                          onClick={() =>
                            scrollToSection(
                              section.id,
                            )
                          }
                          className="mb-0.5 w-full rounded-lg px-3 py-2 text-left text-xs font-medium transition-all"
                          style={{
                            color: isActive
                              ? "#C8A24A"
                              : "#8A94A6",
                            background:
                              isActive
                                ? "rgba(200,162,74,.1)"
                                : "transparent",
                            borderLeft: `2px solid ${
                              isActive
                                ? "#C8A24A"
                                : "transparent"
                            }`,
                            paddingLeft: isActive
                              ? "10px"
                              : "12px",
                          }}
                        >
                          {section.label}
                        </button>
                      );
                    })}
                  </nav>
                </div>

                <div
                  className="mt-4 rounded-xl border p-4"
                  style={{
                    background:
                      "rgba(200,162,74,.04)",
                    borderColor:
                      "rgba(200,162,74,.12)",
                  }}
                >
                  <Shield
                    size={14}
                    style={{
                      color: "#C8A24A",
                    }}
                    className="mb-2"
                  />
                  <p
                    className="text-[11px] leading-relaxed"
                    style={{
                      color: "#8A94A6",
                    }}
                  >
                    Changes to email, unit, and role require administrator authorization.
                  </p>
                </div>
              </div>

              <div className="flex min-w-0 flex-1 flex-col gap-6">
                <Card
                  id="profile"
                  title="Profile Details"
                >
                  <div className="flex flex-col gap-5">
                    {profileBanner ? (
                      <AlertBanner
                        type={profileBanner.type}
                        message={
                          profileBanner.message
                        }
                        onClose={() =>
                          setProfileBanner(null)
                        }
                      />
                    ) : null}

                    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                      <div className="flex flex-col gap-1.5">
                        <FieldLabel>
                          Full Name
                        </FieldLabel>
                        {profileEditing ||
                        profileSaving ? (
                          <div className="grid gap-3">
                            <FormTextInput
                              inputRef={
                                firstEditableFieldRef
                              }
                              value={
                                profileForm.firstName
                              }
                              onChange={(value) =>
                                setProfileField(
                                  "firstName",
                                  value,
                                )
                              }
                              placeholder="First name"
                              error={
                                profileErrors.firstName
                              }
                              autoComplete="given-name"
                            />
                            <FormTextInput
                              value={
                                profileForm.lastName
                              }
                              onChange={(value) =>
                                setProfileField(
                                  "lastName",
                                  value,
                                )
                              }
                              placeholder="Last name"
                              error={
                                profileErrors.lastName
                              }
                              autoComplete="family-name"
                            />
                          </div>
                        ) : (
                          <span
                            className="text-sm"
                            style={{
                              color: "#E6EAF0",
                            }}
                          >
                            {currentUser.first_name}{" "}
                            {currentUser.last_name}
                          </span>
                        )}
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <FieldLabel>
                          Rank
                        </FieldLabel>
                        {profileEditing ||
                        profileSaving ? (
                          <FormTextInput
                            value={profileForm.rank}
                            onChange={(value) =>
                              setProfileField(
                                "rank",
                                value,
                              )
                            }
                            placeholder="e.g. Major"
                            error={
                              profileErrors.rank
                            }
                          />
                        ) : (
                          <span
                            className="text-sm"
                            style={{
                              color: "#E6EAF0",
                            }}
                          >
                            {currentUser.rank ||
                              "Not set"}
                          </span>
                        )}
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <FieldLabel>
                          Email Address
                        </FieldLabel>
                        <span
                          className="text-sm font-mono"
                          style={{
                            color: "#8A94A6",
                          }}
                        >
                          {currentUser.email}
                        </span>
                        <span
                          className="text-xs"
                          style={{
                            color: "#4A5568",
                          }}
                        >
                          Managed by administrators — not editable
                        </span>
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <FieldLabel>
                          Phone / Contact
                        </FieldLabel>
                        {profileEditing ||
                        profileSaving ? (
                          <FormTextInput
                            value={
                              profileForm.contact
                            }
                            onChange={(value) =>
                              setProfileField(
                                "contact",
                                value,
                              )
                            }
                            type="tel"
                            placeholder="+1 (000) 000-0000"
                            error={
                              profileErrors.contact
                            }
                            autoComplete="tel"
                          />
                        ) : (
                          <span
                            className="text-sm font-mono"
                            style={{
                              color: "#E6EAF0",
                            }}
                          >
                            {currentUser.contact ||
                              "Not set"}
                          </span>
                        )}
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <FieldLabel>
                          Military Unit
                        </FieldLabel>
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className="text-sm"
                            style={{
                              color: "#8A94A6",
                            }}
                          >
                            {getUnitLabel(
                              currentUser,
                            )}
                          </span>
                          <span
                            className="rounded px-1.5 py-0.5 text-xs"
                            style={{
                              background:
                                "rgba(138,148,166,.1)",
                              color: "#8A94A6",
                            }}
                          >
                            Admin-managed
                          </span>
                        </div>
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <FieldLabel>
                          Role
                        </FieldLabel>
                        <div className="flex flex-wrap items-center gap-2">
                          <RoleBadge
                            role={getRoleLabel(
                              currentUser,
                            )}
                          />
                          <span
                            className="text-xs"
                            style={{
                              color: "#4A5568",
                            }}
                          >
                            Admin-managed — not editable
                          </span>
                        </div>
                      </div>
                    </div>

                    <div
                      className="flex items-center gap-3 border-t pt-4"
                      style={{
                        borderColor:
                          "rgba(255,255,255,.07)",
                      }}
                    >
                      {!profileEditing &&
                      !profileSaving ? (
                        <PrimaryButton
                          onClick={
                            enterProfileEditMode
                          }
                        >
                          Edit Profile
                        </PrimaryButton>
                      ) : (
                        <>
                          <PrimaryButton
                            onClick={
                              handleProfileSave
                            }
                            loading={
                              profileSaving
                            }
                            disabled={
                              profileSaving
                            }
                          >
                            {profileSaving
                              ? "Saving…"
                              : "Save Changes"}
                          </PrimaryButton>
                          {!profileSaving ? (
                            <SecondaryButton
                              onClick={
                                cancelProfileEdit
                              }
                            >
                              Cancel
                            </SecondaryButton>
                          ) : null}
                        </>
                      )}
                    </div>
                  </div>
                </Card>

                <Card
                  id="avatar"
                  title="Avatar"
                >
                  <div className="flex flex-col items-start gap-6 sm:flex-row">
                    <div className="flex flex-shrink-0 flex-col items-center gap-2">
                      <div
                        className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-full border-2"
                        style={{
                          borderColor:
                            "rgba(200,162,74,.3)",
                          background:
                            "#1A2233",
                        }}
                      >
                        {avatarDisplay ? (
                          <img
                            src={avatarDisplay}
                            alt="Avatar"
                            className="h-full w-full object-cover"
                          />
                        ) : (
                          <span
                            className="text-2xl font-bold"
                            style={{
                              color: "#C8A24A",
                            }}
                          >
                            {getInitials(
                              currentUser,
                            )}
                          </span>
                        )}
                      </div>

                      {avatarDisplay ? (
                        <button
                          onClick={() => {
                            setAvatarFile(null);
                            setAvatarState("idle");
                            setAvatarError("");
                          }}
                          className="text-xs transition-colors"
                          style={{
                            color: "#E5484D",
                          }}
                        >
                          Remove
                        </button>
                      ) : null}
                    </div>

                    <div className="flex flex-1 flex-col gap-3">
                      <div
                        onDrop={handleAvatarDrop}
                        onDragOver={(event) => {
                          event.preventDefault();
                          setAvatarState("dragging");
                        }}
                        onDragLeave={() =>
                          setAvatarState("idle")
                        }
                        onClick={() =>
                          fileInputRef.current?.click()
                        }
                        className="relative flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-8 transition-all"
                        style={{
                          borderColor:
                            avatarState ===
                            "dragging"
                              ? "#C8A24A"
                              : avatarState ===
                                  "error"
                                ? "#E5484D"
                                : "rgba(255,255,255,.12)",
                          background:
                            avatarState ===
                            "dragging"
                              ? "rgba(200,162,74,.04)"
                              : "rgba(255,255,255,.015)",
                        }}
                      >
                        {avatarState ===
                        "uploading" ? (
                          <div className="flex flex-col items-center gap-2">
                            <svg
                              className="h-6 w-6 animate-spin"
                              viewBox="0 0 24 24"
                              fill="none"
                            >
                              <circle
                                className="opacity-25"
                                cx="12"
                                cy="12"
                                r="10"
                                stroke="#C8A24A"
                                strokeWidth="4"
                              />
                              <path
                                className="opacity-75"
                                fill="#C8A24A"
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                              />
                            </svg>
                            <span
                              className="text-xs"
                              style={{
                                color: "#8A94A6",
                              }}
                            >
                              Uploading…
                            </span>
                          </div>
                        ) : avatarState ===
                          "success" ? (
                          <div className="flex flex-col items-center gap-2">
                            <CheckCircle
                              size={24}
                              style={{
                                color: "#3FB950",
                              }}
                            />
                            <span
                              className="text-xs font-medium"
                              style={{
                                color: "#3FB950",
                              }}
                            >
                              Ready to save
                            </span>
                          </div>
                        ) : (
                          <>
                            <Upload
                              size={20}
                              style={{
                                color: "#8A94A6",
                              }}
                            />
                            <p className="text-center text-sm">
                              <span
                                className="font-medium"
                                style={{
                                  color: "#E6EAF0",
                                }}
                              >
                                Drop an image here
                              </span>
                              <span
                                style={{
                                  color: "#8A94A6",
                                }}
                              >
                                {" "}
                                or{" "}
                              </span>
                              <span
                                className="font-semibold"
                                style={{
                                  color: "#C8A24A",
                                }}
                              >
                                browse files
                              </span>
                            </p>
                          </>
                        )}

                        <input
                          ref={fileInputRef}
                          type="file"
                          accept="image/jpeg,image/png,image/webp"
                          className="hidden"
                          onChange={
                            handleAvatarInputChange
                          }
                        />
                      </div>

                      {avatarState === "error" ? (
                        <AlertBanner
                          type="error"
                          message={avatarError}
                          onClose={() => {
                            setAvatarState("idle");
                            setAvatarError("");
                          }}
                        />
                      ) : null}

                      {profileErrors.profile_picture ? (
                        <AlertBanner
                          type="error"
                          message={
                            profileErrors.profile_picture
                          }
                          onClose={() =>
                            setProfileErrors(
                              (
                                current,
                              ) => ({
                                ...current,
                                profile_picture:
                                  "",
                              }),
                            )
                          }
                        />
                      ) : null}

                      <p
                        className="text-xs"
                        style={{
                          color: "#8A94A6",
                        }}
                      >
                        Accepted: JPG, PNG, WEBP — max 5 MB. Image will be cropped to a circle.
                      </p>
                    </div>
                  </div>
                </Card>

                <Card
                  id="password"
                  title="Change Password"
                >
                  <form
                    className="flex flex-col gap-5"
                    onSubmit={
                      handlePasswordSubmit
                    }
                  >
                    {passwordBanner ? (
                      <AlertBanner
                        type={passwordBanner.type}
                        message={
                          passwordBanner.message
                        }
                        onClose={() =>
                          setPasswordBanner(null)
                        }
                      />
                    ) : null}

                    <div className="grid gap-4">
                      <div className="flex flex-col gap-1.5">
                        <FieldLabel>
                          Current Password
                        </FieldLabel>
                        <FormTextInput
                          inputRef={
                            currentPasswordRef
                          }
                          value={
                            passwordForm.currentPassword
                          }
                          onChange={(value) =>
                            setPasswordField(
                              "currentPassword",
                              value,
                            )
                          }
                          placeholder="Enter current password"
                          type={
                            passwordVisibility.current
                              ? "text"
                              : "password"
                          }
                          error={
                            passwordErrors.currentPassword
                          }
                          autoComplete="current-password"
                          rightElement={
                            <button
                              type="button"
                              onClick={() =>
                                setPasswordVisibility(
                                  (
                                    current,
                                  ) => ({
                                    ...current,
                                    current:
                                      !current.current,
                                  }),
                                )
                              }
                              aria-label={
                                passwordVisibility.current
                                  ? "Hide password"
                                  : "Show password"
                              }
                              style={{
                                color: "#8A94A6",
                              }}
                            >
                              {passwordVisibility.current ? (
                                <EyeOff
                                  size={15}
                                />
                              ) : (
                                <Eye size={15} />
                              )}
                            </button>
                          }
                        />
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <FieldLabel>
                          New Password
                        </FieldLabel>
                        <FormTextInput
                          value={
                            passwordForm.newPassword
                          }
                          onChange={(value) =>
                            setPasswordField(
                              "newPassword",
                              value,
                            )
                          }
                          placeholder="Enter new password"
                          type={
                            passwordVisibility.next
                              ? "text"
                              : "password"
                          }
                          error={
                            passwordErrors.newPassword
                          }
                          autoComplete="new-password"
                          rightElement={
                            <button
                              type="button"
                              onClick={() =>
                                setPasswordVisibility(
                                  (
                                    current,
                                  ) => ({
                                    ...current,
                                    next: !current.next,
                                  }),
                                )
                              }
                              aria-label={
                                passwordVisibility.next
                                  ? "Hide password"
                                  : "Show password"
                              }
                              style={{
                                color: "#8A94A6",
                              }}
                            >
                              {passwordVisibility.next ? (
                                <EyeOff
                                  size={15}
                                />
                              ) : (
                                <Eye size={15} />
                              )}
                            </button>
                          }
                        />
                      </div>

                      {passwordForm.newPassword ? (
                        <div
                          className="rounded-lg border p-3"
                          style={{
                            borderColor:
                              "rgba(255,255,255,.07)",
                            background:
                              "rgba(255,255,255,.02)",
                          }}
                        >
                          <div className="mb-2 flex items-center justify-between gap-3">
                            <span
                              className="text-xs font-semibold uppercase tracking-widest"
                              style={{
                                color: "#8A94A6",
                              }}
                            >
                              Password Strength
                            </span>
                            <span
                              className="text-xs font-medium"
                              style={{
                                color:
                                  strength.color,
                              }}
                            >
                              {strength.label}
                            </span>
                          </div>
                          <div className="mb-3 flex gap-1.5">
                            {[1, 2, 3, 4, 5].map(
                              (index) => (
                                <span
                                  key={index}
                                  className="h-1.5 flex-1 rounded-full"
                                  style={{
                                    background:
                                      index <=
                                      strength.score
                                        ? strength.color
                                        : "rgba(255,255,255,.08)",
                                  }}
                                />
                              ),
                            )}
                          </div>
                          <ul className="grid gap-1.5 text-xs">
                            {passwordRequirements.map(
                              (
                                requirement,
                              ) => (
                                <li
                                  key={
                                    requirement.label
                                  }
                                  className="flex items-center gap-2"
                                  style={{
                                    color:
                                      requirement.ok
                                        ? "#3FB950"
                                        : "#8A94A6",
                                  }}
                                >
                                  {requirement.ok ? (
                                    <CheckCircle
                                      size={12}
                                    />
                                  ) : (
                                    <AlertCircle
                                      size={12}
                                    />
                                  )}
                                  {
                                    requirement.label
                                  }
                                </li>
                              ),
                            )}
                          </ul>
                        </div>
                      ) : null}

                      <div className="flex flex-col gap-1.5">
                        <FieldLabel>
                          Confirm New Password
                        </FieldLabel>
                        <FormTextInput
                          value={
                            passwordForm.confirmPassword
                          }
                          onChange={(value) =>
                            setPasswordField(
                              "confirmPassword",
                              value,
                            )
                          }
                          placeholder="Confirm new password"
                          type={
                            passwordVisibility.confirm
                              ? "text"
                              : "password"
                          }
                          error={
                            passwordErrors.confirmPassword
                          }
                          autoComplete="new-password"
                          rightElement={
                            <button
                              type="button"
                              onClick={() =>
                                setPasswordVisibility(
                                  (
                                    current,
                                  ) => ({
                                    ...current,
                                    confirm:
                                      !current.confirm,
                                  }),
                                )
                              }
                              aria-label={
                                passwordVisibility.confirm
                                  ? "Hide password"
                                  : "Show password"
                              }
                              style={{
                                color: "#8A94A6",
                              }}
                            >
                              {passwordVisibility.confirm ? (
                                <EyeOff
                                  size={15}
                                />
                              ) : (
                                <Eye size={15} />
                              )}
                            </button>
                          }
                        />
                      </div>
                    </div>

                    <div
                      className="border-t pt-4"
                      style={{
                        borderColor:
                          "rgba(255,255,255,.07)",
                      }}
                    >
                      <PrimaryButton
                        type="submit"
                        loading={
                          passwordStatus ===
                          "saving"
                        }
                        disabled={
                          passwordStatus ===
                          "saving"
                        }
                      >
                        {passwordStatus ===
                        "saving"
                          ? "Updating…"
                          : "Update Password"}
                      </PrimaryButton>
                    </div>
                  </form>
                </Card>

                <Card
                  id="security"
                  title="Account & Security"
                >
                  <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                    <div className="flex flex-col gap-1.5">
                      <FieldLabel>
                        Account Status
                      </FieldLabel>
                      <span
                        className="inline-flex w-fit items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold"
                        style={{
                          color: "#3FB950",
                          background:
                            "rgba(63,185,80,.1)",
                          borderColor:
                            "rgba(63,185,80,.25)",
                        }}
                      >
                        <span
                          className="inline-block h-1.5 w-1.5 animate-pulse rounded-full"
                          style={{
                            background: "#3FB950",
                          }}
                        />
                        {currentUser.is_active
                          ? "Active"
                          : "Inactive"}
                      </span>
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <FieldLabel>
                        Account ID
                      </FieldLabel>
                      <span
                        className="text-sm font-mono"
                        style={{
                          color: "#8A94A6",
                        }}
                      >
                        {getUserIdentifier(
                          currentUser,
                        )}
                      </span>
                    </div>

                    {createdAtLabel ? (
                      <div className="flex flex-col gap-1.5">
                        <FieldLabel>
                          Date Joined
                        </FieldLabel>
                        <div className="flex items-center gap-2">
                          <Clock
                            size={13}
                            style={{
                              color: "#8A94A6",
                            }}
                          />
                          <span
                            className="text-sm font-mono"
                            style={{
                              color: "#8A94A6",
                            }}
                          >
                            {createdAtLabel}
                          </span>
                        </div>
                      </div>
                    ) : null}

                    {currentUser.created_by_username ? (
                      <div className="flex flex-col gap-1.5">
                        <FieldLabel>
                          Account Created By
                        </FieldLabel>
                        <span
                          className="text-sm"
                          style={{
                            color: "#8A94A6",
                          }}
                        >
                          {currentUser.created_by_username}
                        </span>
                      </div>
                    ) : null}

                    {lastLoginLabel ? (
                      <div className="flex flex-col gap-1.5">
                        <FieldLabel>
                          Last Login
                        </FieldLabel>
                        <div className="flex items-center gap-2">
                          <Activity
                            size={13}
                            style={{
                              color: "#8A94A6",
                            }}
                          />
                          <span
                            className="text-sm font-mono"
                            style={{
                              color: "#8A94A6",
                            }}
                          >
                            {lastLoginLabel}
                          </span>
                        </div>
                      </div>
                    ) : null}

                    <div className="flex flex-col gap-1.5">
                      <FieldLabel>
                        Authentication
                      </FieldLabel>
                      <div className="flex items-center gap-2">
                        <Lock
                          size={13}
                          style={{
                            color: "#8A94A6",
                          }}
                        />
                        <span
                          className="text-sm"
                          style={{
                            color: "#8A94A6",
                          }}
                        >
                          Password
                        </span>
                      </div>
                    </div>
                  </div>

                  <p
                    className="mt-5 text-xs"
                    style={{
                      color: "#4A5568",
                    }}
                  >
                    Account status, role, and unit are administrator-managed. Contact your system admin for changes.
                  </p>
                </Card>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
