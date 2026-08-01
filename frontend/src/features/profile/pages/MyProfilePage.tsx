import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type {
  ChangeEvent,
  DragEvent,
  FormEvent,
} from "react";
import {
  BarChart3,
  Bell,
  ChevronDown,
  ChevronRight,
  Crosshair,
  LayoutDashboard,
  LogOut,
  Map,
  Navigation2,
  Settings,
  Target,
  User,
  Users,
  Wrench,
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
import { ProfileAvatarCard } from "../components/ProfileAvatarCard";
import { ProfileDetailsCard } from "../components/ProfileDetailsCard";
import { ProfilePasswordCard } from "../components/ProfilePasswordCard";
import {
  RoleBadge,
  UnitChip,
} from "../components/ProfilePrimitives";
import { ProfileSectionsSidebar } from "../components/ProfileSectionsSidebar";
import { ProfileSecurityCard } from "../components/ProfileSecurityCard";
import { ProfileSummaryHero } from "../components/ProfileSummaryHero";
import type {
  ActiveSection,
  AvatarState,
  PasswordFormState,
  PasswordVisibilityKey,
  ProfileFormState,
  StatusBanner,
} from "../types/profile";
import {
  formatDate,
  formatDateTime,
  getInitials,
  getPasswordRequirements,
  getProfileFormState,
  getRoleLabel,
  getStrength,
  getUnitLabel,
} from "../utils/profileUtils";

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
    useState<StatusBanner | null>(null);
  const [passwordForm, setPasswordForm] =
    useState<PasswordFormState>({
      currentPassword: "",
      newPassword: "",
      confirmPassword: "",
    });
  const [passwordErrors, setPasswordErrors] =
    useState<Record<string, string>>({});
  const [passwordBanner, setPasswordBanner] =
    useState<StatusBanner | null>(null);
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

        setLoadError(
          getFormError(
            error,
            "We could not load your profile right now.",
          ),
        );
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

  const avatarDisplay =
    avatarPreview ??
    currentUser?.profile_picture ??
    null;

  const passwordStrength = getStrength(
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

  const profileSaving =
    profileMode === "saving";
  const profileEditing =
    profileMode === "edit";

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

  function togglePasswordVisibility(
    key: PasswordVisibilityKey,
  ) {
    setPasswordVisibility((current) => ({
      ...current,
      [key]: !current[key],
    }));
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
    window.setTimeout(() => {
      firstEditableFieldRef.current?.focus();
    }, 0);
  }

  function resetAvatarSelection() {
    setAvatarFile(null);
    setAvatarError("");
    setAvatarState("idle");
  }

  function cancelProfileEdit() {
    if (!currentUser) {
      return;
    }

    setProfileForm(
      getProfileFormState(currentUser),
    );
    resetAvatarSelection();
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
      resetAvatarSelection();
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

  function handleAvatarFile(file: File) {
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
    event: DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault();
    setAvatarState("idle");
    const file =
      event.dataTransfer.files?.[0];

    if (file) {
      handleAvatarFile(file);
    }
  }

  function handleAvatarDragOver(
    event: DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault();
    setAvatarState("dragging");
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
          Loading profile...
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
                type="button"
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
                aria-haspopup="menu"
                aria-expanded={userMenuOpen}
                aria-label="Open account menu"
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
                      type="button"
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
                      type="button"
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
                      type="button"
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

            <ProfileSummaryHero
              currentUser={currentUser}
              avatarDisplay={avatarDisplay}
              onAvatarClick={() =>
                scrollToSection("avatar")
              }
            />

            <div className="flex items-start gap-6">
              <ProfileSectionsSidebar
                activeSection={activeSection}
                sections={SECTIONS}
                onSelectSection={
                  scrollToSection
                }
              />

              <div className="flex min-w-0 flex-1 flex-col gap-6">
                <ProfileDetailsCard
                  currentUser={currentUser}
                  profileBanner={profileBanner}
                  profileEditing={profileEditing}
                  profileSaving={profileSaving}
                  profileForm={profileForm}
                  profileErrors={profileErrors}
                  firstEditableFieldRef={
                    firstEditableFieldRef
                  }
                  onSetProfileField={
                    setProfileField
                  }
                  onDismissBanner={() =>
                    setProfileBanner(null)
                  }
                  onEnterEditMode={
                    enterProfileEditMode
                  }
                  onSave={handleProfileSave}
                  onCancel={cancelProfileEdit}
                />

                <ProfileAvatarCard
                  currentUser={currentUser}
                  avatarDisplay={avatarDisplay}
                  avatarState={avatarState}
                  avatarError={avatarError}
                  profilePictureError={
                    profileErrors.profile_picture
                  }
                  fileInputRef={fileInputRef}
                  onRemoveAvatar={
                    resetAvatarSelection
                  }
                  onAvatarDrop={
                    handleAvatarDrop
                  }
                  onAvatarDragOver={
                    handleAvatarDragOver
                  }
                  onAvatarDragLeave={() =>
                    setAvatarState("idle")
                  }
                  onAvatarInputChange={
                    handleAvatarInputChange
                  }
                  onDismissAvatarError={() => {
                    setAvatarState("idle");
                    setAvatarError("");
                  }}
                  onDismissProfilePictureError={() =>
                    setProfileErrors(
                      (current) => ({
                        ...current,
                        profile_picture: "",
                      }),
                    )
                  }
                  onOpenFilePicker={() =>
                    fileInputRef.current?.click()
                  }
                />

                <ProfilePasswordCard
                  passwordBanner={
                    passwordBanner
                  }
                  passwordForm={passwordForm}
                  passwordErrors={
                    passwordErrors
                  }
                  passwordStatus={
                    passwordStatus
                  }
                  passwordVisibility={
                    passwordVisibility
                  }
                  passwordStrength={
                    passwordStrength
                  }
                  passwordRequirements={
                    passwordRequirements
                  }
                  currentPasswordRef={
                    currentPasswordRef
                  }
                  onDismissBanner={() =>
                    setPasswordBanner(null)
                  }
                  onSubmit={
                    handlePasswordSubmit
                  }
                  onSetPasswordField={
                    setPasswordField
                  }
                  onToggleVisibility={
                    togglePasswordVisibility
                  }
                />

                <ProfileSecurityCard
                  currentUser={currentUser}
                  createdAtLabel={
                    createdAtLabel
                  }
                  lastLoginLabel={
                    lastLoginLabel
                  }
                />
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
