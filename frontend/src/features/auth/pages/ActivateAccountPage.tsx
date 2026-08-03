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
  activateAccount,
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
} from "../../../shared/utils/apiErrors";
import {
  isAlreadyActivatedError,
  isInvalidActivationLinkError,
} from "../utils/authErrors";
import {
  hasActivationRouteParams,
  validatePasswordConfirmation,
  validateRequiredPassword,
} from "../validation/authValidation";

type ActivationView =
  | "form"
  | "success"
  | "invalid"
  | "already-active";

export function ActivateAccountPage() {
  const {
    userId,
    token,
  } = useParams<{
    userId: string;
    token: string;
  }>();

  const routeIsValid =
    hasActivationRouteParams(
      userId,
      token,
    );

  const [
    view,
    setView,
  ] = useState<ActivationView>("form");

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
      !userId ||
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
        activateAccount(
          userId,
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
        isAlreadyActivatedError(error)
      ) {
        setNewPassword("");
        setConfirmPassword("");
        setView("already-active");
        return;
      }

      if (
        isInvalidActivationLinkError(
          error,
        )
      ) {
        setNewPassword("");
        setConfirmPassword("");
        setView("invalid");
        return;
      }

      const backendPasswordError =
        getApiFieldError(
          error,
          "password",
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
          "The account could not be activated. Please try again.",
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
          headingId="activate-account-heading"
          title="Activate your account"
        >
          <AuthResultState
            variant="success"
            title="Your account is active"
            description="You can now sign in to Mission Control."
          >
            <AuthPrimaryLink to="/login">
              Continue to sign in
            </AuthPrimaryLink>
          </AuthResultState>
        </AuthPageContent>
      </AuthLayout>
    );
  }

  if (
    effectiveView ===
    "already-active"
  ) {
    return (
      <AuthLayout>
        <AuthPageContent
          headingId="activate-account-heading"
          title="Activate your account"
        >
          <AuthResultState
            variant="info"
            title="Account already activated"
            description="This account has already been activated. Continue to the sign-in page."
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
          headingId="activate-account-heading"
          title="Activation link unavailable"
        >
          <AuthResultState
            variant="error"
            title="Invalid or expired link"
            description="This activation link is invalid or has expired. Contact an administrator for a new invitation."
          >
            <AuthPrimaryLink to="/login">
              Return to sign in
            </AuthPrimaryLink>
          </AuthResultState>
        </AuthPageContent>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <AuthPageContent
        headingId="activate-account-heading"
        title="Activate your account"
        description="Create a password to activate your Mission Control account."
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
              id="activation-new-password"
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
                  ? "activation-password-strength"
                  : undefined
              }
              error={newPasswordError}
              disabled={isSubmitting}
              required
            />

            <PasswordStrength
              id="activation-password-strength"
              password={newPassword}
            />

            <PasswordInput
              ref={confirmPasswordRef}
              id="activation-confirm-password"
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
            loadingLabel="Activating account"
          >
            Activate account
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
