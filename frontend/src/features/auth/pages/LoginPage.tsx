import {
  useRef,
  useState,
} from "react";
import type { FormEvent } from "react";
import { Mail } from "lucide-react";
import { useNavigate } from "react-router";

import { isAbortError } from "../../../shared/api/apiClient";
import {
  prepareSignIn,
  signIn,
} from "../api/authApi";
import { AuthAlert } from "../components/AuthAlert";
import { AuthLayout } from "../components/AuthLayout";
import { AuthPageContent } from "../components/AuthPageContent";
import { AuthTextLink } from "../components/AuthTextLink";
import { PasswordInput } from "../components/PasswordInput";
import { SubmitButton } from "../components/SubmitButton";
import { TextInput } from "../components/TextInput";
import { useAbortableRequest } from "../../../shared/hooks/useAbortableRequest";
import { getFormError } from "../utils/authErrors";
import { validateRequiredPassword } from "../validation/authValidation";
import { useAuth } from "../hooks/useAuth";

export function LoginPage() {
  const navigate = useNavigate();

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [identifierError, setIdentifierError] =
    useState<string>();
  const [passwordError, setPasswordError] =
    useState<string>();
  const [formError, setFormError] =
    useState<string>();
  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const identifierRef =
    useRef<HTMLInputElement>(null);
  const alertRef =
    useRef<HTMLDivElement>(null);

  const {
    run,
    isMounted,
  } = useAbortableRequest();

  const {
    setAuthenticatedUser,
  } = useAuth();

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

    const trimmedIdentifier =
      identifier.trim();
    const nextIdentifierError =
      trimmedIdentifier
        ? undefined
        : "Email or username is required.";
    const nextPasswordError =
      validateRequiredPassword(
        password,
        "Password",
      );

    setIdentifierError(nextIdentifierError);
    setPasswordError(nextPasswordError);
    setFormError(undefined);

    if (nextIdentifierError) {
      identifierRef.current?.focus();
      return;
    }

    if (nextPasswordError) {
      return;
    }

    setIsSubmitting(true);

    try {
      await run((signal) =>
        prepareSignIn(signal),
      );

      if (!isMounted()) {
        return;
      }

      const user = await run((signal) =>
        signIn(
          trimmedIdentifier,
          password,
          signal,
        ),
      );

      if (!isMounted()) {
        return;
      }

      setAuthenticatedUser(user);

      navigate(
        user.must_change_password
          ? "/change-password/required"
          : "/my-profile",
        { replace: true },
      );
    } catch (error) {
      if (
        isAbortError(error) ||
        !isMounted()
      ) {
        return;
      }

      setFormError(
        getFormError(
          error,
          "Sign in could not be completed. Please try again.",
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
        headingId="login-heading"
        title="Sign in"
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
            <TextInput
              ref={identifierRef}
              id="login-identifier"
              name="identifier"
              label="Email or Username"
              type="text"
              inputMode="email"
              value={identifier}
              onChange={(event) => {
                setIdentifier(event.target.value);
                setIdentifierError(undefined);
                setFormError(undefined);
              }}
              placeholder="operator@squadron.mil"
              autoComplete="username"
              autoCapitalize="none"
              spellCheck={false}
              leadingIcon={
                <Mail
                  size={15}
                  aria-hidden="true"
                />
              }
              error={identifierError}
              disabled={isSubmitting}
              required
            />

            <div className="flex flex-col gap-1.5">
              <PasswordInput
                id="login-password"
                name="password"
                label="Password"
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);
                  setPasswordError(undefined);
                  setFormError(undefined);
                }}
                autoComplete="current-password"
                error={passwordError}
                disabled={isSubmitting}
                required
              />

              <div className="flex justify-end">
                <AuthTextLink to="/forgot-password">
                  Forgot password?
                </AuthTextLink>
              </div>
            </div>
          </div>

          <SubmitButton
            isLoading={isSubmitting}
            loadingLabel="Signing in"
          >
            Sign in
          </SubmitButton>

          <p className="mt-1 text-center text-xs leading-5 text-mc-subtle">
            Authorized personnel only — unauthorized
            access is prohibited.
          </p>
        </form>
      </AuthPageContent>
    </AuthLayout>
  );
}
