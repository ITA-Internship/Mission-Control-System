import {
  useRef,
  useState,
} from "react";
import type {
  FormEvent,
} from "react";
import {
  ArrowLeft,
} from "lucide-react";
import {
  useParams,
} from "react-router";

import {
  isAbortError,
} from "../../../shared/api/apiClient";
import {
  confirmPasswordReset,
} from "../api/authApi";
import {
  AuthAlert,
} from "../components/AuthAlert";
import {
  AuthLayout,
} from "../components/AuthLayout";
import {
  AuthPageContent,
} from "../components/AuthPageContent";
import {
  AuthPrimaryLink,
} from "../components/AuthPrimaryLink";
import {
  AuthResultState,
} from "../components/AuthResultState";
import {
  AuthTextLink,
} from "../components/AuthTextLink";
import {
  PasswordInput,
} from "../components/PasswordInput";
import {
  PasswordStrength,
} from "../components/PasswordStrength";
import {
  SubmitButton,
} from "../components/SubmitButton";
import {
  useAbortableRequest,
} from "../../../shared/hooks/useAbortableRequest";
import {
  getApiFieldError,
  getFormError,
  isInvalidResetLinkError,
} from "../utils/authErrors";
import {
  hasResetRouteParams,
  validatePasswordConfirmation,
  validateRequiredPassword,
} from "../validation/authValidation";

type ResetView =
  | "form"
  | "success"
  | "invalid";

export function ResetPasswordPage() {
  const {
    uid,
    token,
  } = useParams<{
    uid: string;
    token: string;
  }>();

  const routeIsValid =
    hasResetRouteParams(uid, token);

  const [
    view,
    setView,
  ] = useState<ResetView>("form");

  const [
    newPassword,
    setNewPassword,
  ] = useState("");

  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("");

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

  const effectiveView =
    routeIsValid
      ? view
      : "invalid";

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

    if (
      !routeIsValid ||
      !uid ||
      !token
    ) {
      setView("invalid");
      return;
    }

    const nextPasswordError =
      validateRequiredPassword(
        newPassword,
        "New password",
      );

    const nextConfirmationError =
      validatePasswordConfirmation(
        newPassword,
        confirmPassword,
      );

    setNewPasswordError(
      nextPasswordError,
    );

    setConfirmPasswordError(
      nextConfirmationError,
    );

    setFormError(undefined);

    if (nextPasswordError) {
      newPasswordRef.current?.focus();
      return;
    }

    if (nextConfirmationError) {
      confirmPasswordRef.current?.focus();
      return;
    }

    setIsSubmitting(true);

    try {
      await run((signal) =>
        confirmPasswordReset(
          uid,
          token,
          newPassword,
          signal,
        ),
      );

      if (!isMounted()) {
        return;
      }

      setNewPassword("");
      setConfirmPassword("");
      setView("success");
    } catch (error) {
      if (
        isAbortError(error) ||
        !isMounted()
      ) {
        return;
      }

      if (
        isInvalidResetLinkError(error)
      ) {
        setNewPassword("");
        setConfirmPassword("");
        setView("invalid");
        return;
      }

      const backendPasswordError =
        getApiFieldError(
          error,
          "new_password",
        );

      if (backendPasswordError) {
        setNewPasswordError(
          backendPasswordError,
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

  if (effectiveView === "success") {
    return (
      <AuthLayout>
        <AuthPageContent
          headingId="reset-password-heading"
          title="Set a new password"
        >
          <AuthResultState
            variant="success"
            title="Password updated"
            description="Your password has been reset successfully. You can now sign in."
          >
            <AuthPrimaryLink to="/login">
              Continue to sign in
            </AuthPrimaryLink>
          </AuthResultState>
        </AuthPageContent>
      </AuthLayout>
    );
  }

  if (effectiveView === "invalid") {
    return (
      <AuthLayout>
        <AuthPageContent
          headingId="reset-password-heading"
          title="Reset link unavailable"
        >
          <AuthResultState
            variant="error"
            title="Invalid or expired link"
            description="This password reset link is invalid or has expired. Request a new link to continue."
          >
            <div className="flex flex-col gap-4">
              <AuthPrimaryLink to="/forgot-password">
                Request a new reset link
              </AuthPrimaryLink>

              <div className="flex justify-center">
                <AuthTextLink
                  to="/login"
                  icon={
                    <ArrowLeft size={14} />
                  }
                >
                  Back to sign in
                </AuthTextLink>
              </div>
            </div>
          </AuthResultState>
        </AuthPageContent>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <AuthPageContent
        headingId="reset-password-heading"
        title="Set a new password"
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
              ref={newPasswordRef}
              id="reset-new-password"
              name="newPassword"
              label="New password"
              value={newPassword}
              onChange={(event) => {
                setNewPassword(
                  event.target.value,
                );

                setNewPasswordError(
                  undefined,
                );

                setConfirmPasswordError(
                  undefined,
                );

                setFormError(undefined);
              }}
              autoComplete="new-password"
              aria-describedby={
                newPassword
                  ? "reset-password-strength"
                  : undefined
              }
              error={newPasswordError}
              disabled={isSubmitting}
              required
            />

            <PasswordStrength
              id="reset-password-strength"
              password={newPassword}
            />

            <PasswordInput
              ref={confirmPasswordRef}
              id="reset-confirm-password"
              name="confirmPassword"
              label="Confirm new password"
              value={confirmPassword}
              onChange={(event) => {
                setConfirmPassword(
                  event.target.value,
                );

                setConfirmPasswordError(
                  undefined,
                );

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
            loadingLabel="Updating password"
          >
            Update password
          </SubmitButton>

          <div className="flex">
            <AuthTextLink
              to="/login"
              icon={
                <ArrowLeft size={14} />
              }
            >
              Back to sign in
            </AuthTextLink>
          </div>
        </form>
      </AuthPageContent>
    </AuthLayout>
  );
}
