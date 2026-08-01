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
  Link,
  useNavigate,
} from "react-router";

import {
  ApiError,
  isAbortError,
} from "../../auth/api/apiClient";
import {
  changePassword,
  getCurrentUser,
  signOut,
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
import { ProfileSectionsSidebar } from "../components/ProfileSectionsSidebar";
import { ProfileSecurityCard } from "../components/ProfileSecurityCard";
import { ProfileSummaryHero } from "../components/ProfileSummaryHero";
import { ProfileWorkspaceLayout } from "../components/ProfileWorkspaceLayout";
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
  getPasswordRequirements,
  getProfileFormState,
  getStrength,
} from "../utils/profileUtils";

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

export function MyProfilePage({
  initialUser = null,
}: {
  initialUser?: CurrentUser | null;
}) {
  const navigate = useNavigate();

  const [currentUser, setCurrentUser] =
    useState<CurrentUser | null>(initialUser);
  const [loading, setLoading] =
    useState(initialUser === null);
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
  const [avatarRemoved, setAvatarRemoved] =
    useState(false);
  const [profileMode, setProfileMode] =
    useState<"read" | "edit" | "saving">(
      "read",
    );
  const [profileForm, setProfileForm] =
    useState<ProfileFormState>(
      initialUser
        ? getProfileFormState(initialUser)
        : {
            firstName: "",
            lastName: "",
            rank: "",
            contact: "",
          },
    );
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
  const [signingOut, setSigningOut] =
    useState(false);
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
    if (initialUser) {
      return undefined;
    }

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

        if (
          error instanceof ApiError &&
          error.status === 401
        ) {
          navigate("/login", {
            replace: true,
          });
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
  }, [initialUser, navigate]);

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

  const avatarDisplay = avatarRemoved
    ? null
    : avatarPreview ??
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
    setAvatarRemoved(false);
    setAvatarError("");
    setAvatarState("idle");
  }

  function handleAvatarRemoval() {
    if (avatarFile) {
      resetAvatarSelection();
      return;
    }

    if (!currentUser?.profile_picture) {
      return;
    }

    setAvatarRemoved(true);
    setAvatarError("");
    setAvatarState("success");
    setProfileMode("edit");
    setProfileBanner(null);
  }

  function redirectExpiredSession(
    error: unknown,
  ): boolean {
    if (
      error instanceof ApiError &&
      error.status === 401
    ) {
      navigate("/login", {
        replace: true,
      });
      return true;
    }

    return false;
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
          profilePicture: avatarRemoved
            ? null
            : avatarFile ?? undefined,
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
      if (redirectExpiredSession(error)) {
        return;
      }

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
      if (redirectExpiredSession(error)) {
        return;
      }

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
    setAvatarRemoved(false);
    setAvatarState("uploading");
    setProfileMode("edit");
    setProfileBanner(null);

    window.setTimeout(() => {
      setAvatarFile(file);
      setAvatarState("success");
    }, 250);
  }

  async function handleSignOut() {
    if (signingOut) {
      return;
    }

    setSigningOut(true);
    setUserMenuOpen(false);

    try {
      await signOut();
      navigate("/login", {
        replace: true,
      });
    } catch (error) {
      if (redirectExpiredSession(error)) {
        return;
      }

      setProfileBanner({
        type: "error",
        message: getFormError(
          error,
          "We could not sign you out. Please try again.",
        ),
      });
      scrollToSection("profile");
    } finally {
      setSigningOut(false);
    }
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
    <ProfileWorkspaceLayout
      currentUser={currentUser}
      avatarDisplay={avatarDisplay}
      sidebarOpen={sidebarOpen}
      userMenuOpen={userMenuOpen}
      menuRef={menuRef}
      onToggleSidebar={() =>
        setSidebarOpen((current) => !current)
      }
      onCloseSidebar={() =>
        setSidebarOpen(false)
      }
      onToggleUserMenu={() =>
        setUserMenuOpen((current) => !current)
      }
      onSignOut={handleSignOut}
      signingOut={signingOut}
    >
      <div className="mx-auto max-w-240 px-6 py-8">
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
                handleAvatarRemoval
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
    </ProfileWorkspaceLayout>
  );
}
