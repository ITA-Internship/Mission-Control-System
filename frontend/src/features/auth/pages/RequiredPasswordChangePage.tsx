import {
  useRef,
  useState,
} from "react";
import type { FormEvent } from "react";
import { Shield } from "lucide-react";
import { useNavigate } from "react-router";

import {
  isAbortError,
} from "../../../shared/api/apiClient";
import { changePassword } from "../api/authApi";
import { AuthAlert } from "../components/AuthAlert";
import { AuthLayout } from "../components/AuthLayout";
import { AuthPageContent } from "../components/AuthPageContent";
import { PasswordInput } from "../components/PasswordInput";
import { PasswordStrength } from "../components/PasswordStrength";
import { SubmitButton } from "../components/SubmitButton";
import { useAbortableRequest } from "../../../shared/hooks/useAbortableRequest";
import {
  getApiFieldError,
  getFormError,
  isSessionAuthenticationError,
} from "../utils/authErrors";
import {
  validatePasswordConfirmation,
  validateRequiredPassword,
} from "../validation/authValidation";
import { useAuth } from "../hooks/useAuth";

export function RequiredPasswordChangePage() {
  const navigate = useNavigate();

  const [
    currentPassword,
    setCurrentPassword,
  ] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("");
  const [
    currentPasswordError,
    setCurrentPasswordError,
  ] = useState<string>();
  const [
    newPasswordError,
    setNewPasswordError,
  ] = useState<string>();
  const [
    confirmPasswordError,
    setConfirmPasswordError,
  ] = useState<string>();
  const [
    formError,
    setFormError,
  ] = useState<string>();
  const [
    isSubmitting,
    setIsSubmitting,
  ] = useState(false);

  const currentPasswordRef =
    useRef<HTMLInputElement>(null);
  const newPasswordRef =
    useRef<HTMLInputElement>(null);
  const confirmPasswordRef =
    useRef<HTMLInputElement>(null);
  const alertRef =
    useRef<HTMLDivElement>(null);

  const {
    run,
    isMounted,
  } = useAbortableRequest();

  const { refreshCurrentUser } = useAuth();

  function focusAlert() {
    requestAnimationFrame(() => {
      alertRef.current?.focus();
    });
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (isSubmitting) {
      return;
    }

    const nextCurrentPasswordError =
      validateRequiredPassword(
        currentPassword,
        "Current password",
      );
    const nextNewPasswordError =
      validateRequiredPassword(
        newPassword,
        "New password",
      );
    const nextConfirmPasswordError =
      validatePasswordConfirmation(
        newPassword,
        confirmPassword,
      );

    setCurrentPasswordError(
      nextCurrentPasswordError,
    );
    setNewPasswordError(
      nextNewPasswordError,
    );
    setConfirmPasswordError(
      nextConfirmPasswordError,
    );
    setFormError(undefined);

    if (nextCurrentPasswordError) {
      currentPasswordRef.current?.focus();
      return;
    }

    if (nextNewPasswordError) {
      newPasswordRef.current?.focus();
      return;
    }

    if (nextConfirmPasswordError) {
      confirmPasswordRef.current?.focus();
      return;
    }

    setIsSubmitting(true);

    try {
      await run((signal) =>
        changePassword(
          currentPassword,
          newPassword,
          signal,
        ),
      );

      if (!isMounted()) {
        return;
      }

      const refreshedUser = await refreshCurrentUser();

      if (!isMounted()) {
        return;
      }

      if (!refreshedUser) {
        navigate("/login", {
          replace: true,
        });
        return;
      }

      if (refreshedUser.must_change_password) {
        setFormError(
          "Your account still requires a password change. Please try again.",
        );
        return;
      }

      navigate("/my-profile", {
        replace: true,
      });
    } catch (error) {
      if (
        isAbortError(error) ||
        !isMounted()
      ) {
        return;
      }

      if (isSessionAuthenticationError(error)) {
        navigate("/login", {
          replace: true,
        });
        return;
      }

      const backendCurrentPasswordError =
        getApiFieldError(
          error,
          "old_password",
        );
      if (backendCurrentPasswordError) {
        setCurrentPasswordError(
          backendCurrentPasswordError,
        );
        requestAnimationFrame(() => {
          currentPasswordRef.current?.focus();
        });
        return;
      }

      const backendNewPasswordError =
        getApiFieldError(
          error,
          "new_password",
        );
      if (backendNewPasswordError) {
        setNewPasswordError(
          backendNewPasswordError,
        );
        requestAnimationFrame(() => {
          newPasswordRef.current?.focus();
        });
        return;
      }

      setFormError(
        getFormError(
          error,
          "The password could not be updated. Please try again.",
        ),
      );
      focusAlert();
    } finally {
      if (isMounted()) {
        setIsSubmitting(false);
      }
    }
  }

  return (
    <AuthLayout>
      <AuthPageContent
        headingId="required-password-change-heading"
        title="Update your password to continue"
        description="For security, you must set a new password before proceeding."
        prelude={
          <div className="flex items-center gap-2 rounded-lg border border-mc-accent/15 bg-mc-accent/10 px-3 py-2">
            <Shield
              size={14}
              className="shrink-0 text-mc-accent"
              aria-hidden="true"
            />

            <span className="text-xs font-medium tracking-wider text-mc-accent uppercase">
              Security action required
            </span>
          </div>
        }
      >
        <form
          className="flex flex-col gap-5"
          onSubmit={handleSubmit}
          noValidate
          aria-busy={isSubmitting}
        >
          {formError ? (
            <AuthAlert
              ref={alertRef}
              variant="error"
              tabIndex={-1}
            >
              {formError}
            </AuthAlert>
          ) : null}

          <div className="flex flex-col gap-4">
            <PasswordInput
              ref={currentPasswordRef}
              id="required-current-password"
              name="currentPassword"
              label="Current password"
              value={currentPassword}
              onChange={(event) => {
                setCurrentPassword(
                  event.target.value,
                );
                setCurrentPasswordError(
                  undefined,
                );
                setFormError(undefined);
              }}
              autoComplete="current-password"
              error={currentPasswordError}
              disabled={isSubmitting}
              required
            />

            <PasswordInput
              ref={newPasswordRef}
              id="required-new-password"
              name="newPassword"
              label="New password"
              value={newPassword}
              onChange={(event) => {
                setNewPassword(event.target.value);
                setNewPasswordError(undefined);
                setConfirmPasswordError(undefined);
                setFormError(undefined);
              }}
              autoComplete="new-password"
              aria-describedby={
                newPassword
                  ? "required-password-strength"
                  : undefined
              }
              error={newPasswordError}
              disabled={isSubmitting}
              required
            />

            <PasswordStrength
              id="required-password-strength"
              password={newPassword}
            />

            <PasswordInput
              ref={confirmPasswordRef}
              id="required-confirm-password"
              name="confirmPassword"
              label="Confirm new password"
              value={confirmPassword}
              onChange={(event) => {
                setConfirmPassword(
                  event.target.value,
                );
                setConfirmPasswordError(undefined);
                setFormError(undefined);
              }}
              autoComplete="new-password"
              error={confirmPasswordError}
              disabled={isSubmitting}
              required
            />
          </div>

          <SubmitButton
            isLoading={isSubmitting}
            loadingLabel="Saving password"
          >
            Save and continue
          </SubmitButton>

          <p className="text-center text-xs leading-5 text-mc-subtle">
            This step is mandatory and cannot be
            skipped.
          </p>
        </form>
      </AuthPageContent>
    </AuthLayout>
  );
}
