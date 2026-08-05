import {
  useRef,
  useState,
} from "react";
import type {
  FormEvent,
} from "react";
import {
  ArrowLeft,
  Mail,
} from "lucide-react";

import {
  isAbortError,
} from "../../../shared/api/apiClient";
import {
  requestPasswordReset,
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
  AuthTextLink,
} from "../components/AuthTextLink";
import {
  SubmitButton,
} from "../components/SubmitButton";
import {
  TextInput,
} from "../components/TextInput";
import {
  useAbortableRequest,
} from "../../../shared/hooks/useAbortableRequest";
import {
  getApiFieldError,
  getFormError,
} from "../../../shared/utils/apiErrors";
import {
  validateEmail,
} from "../validation/authValidation";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");

  const [
    emailError,
    setEmailError,
  ] = useState<string>();

  const [
    formError,
    setFormError,
  ] = useState<string>();

  const [
    isSubmitting,
    setIsSubmitting,
  ] = useState(false);

  const [
    isSuccess,
    setIsSuccess,
  ] = useState(false);

  const emailRef =
    useRef<HTMLInputElement>(null);

  const alertRef =
    useRef<HTMLDivElement>(null);

  const {
    run,
    isMounted,
  } = useAbortableRequest();

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

    const validationError =
      validateEmail(email);

    setEmailError(validationError);
    setFormError(undefined);

    if (validationError) {
      emailRef.current?.focus();
      return;
    }

    setIsSubmitting(true);

    try {
      await run((signal) =>
        requestPasswordReset(
          email.trim(),
          signal,
        ),
      );

      if (!isMounted()) {
        return;
      }

      setEmail("");
      setIsSuccess(true);
    } catch (error) {
      if (
        isAbortError(error) ||
        !isMounted()
      ) {
        return;
      }

      const backendEmailError =
        getApiFieldError(
          error,
          "email",
        );

      if (backendEmailError) {
        setEmailError(
          backendEmailError,
        );

        requestAnimationFrame(() => {
          emailRef.current?.focus();
        });

        return;
      }

      setFormError(
        getFormError(
          error,
          "Password reset instructions could not be sent. Please try again.",
        ),
      );

      focusAlert();
    } finally {
      if (isMounted()) {
        setIsSubmitting(false);
      }
    }
  }

  if (isSuccess) {
    return (
      <AuthLayout>
        <AuthPageContent
          headingId="forgot-password-heading"
          title="Check your email"
        >
          <AuthAlert variant="success">
            If an account exists for this email
            address, password reset instructions
            have been sent.
          </AuthAlert>

          <AuthPrimaryLink to="/login">
            Back to sign in
          </AuthPrimaryLink>
        </AuthPageContent>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <AuthPageContent
        headingId="forgot-password-heading"
        title="Reset password"
        description="Enter your email and we'll send you a reset link."
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

          <TextInput
            ref={emailRef}
            id="forgot-password-email"
            name="email"
            label="Email"
            type="email"
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
              setEmailError(undefined);
              setFormError(undefined);
            }}
            placeholder="operator@squadron.mil"
            autoComplete="email"
            autoCapitalize="none"
            spellCheck={false}
            leadingIcon={
              <Mail
                size={15}
                aria-hidden="true"
              />
            }
            error={emailError}
            disabled={isSubmitting}
            required
          />

          <SubmitButton
            isLoading={isSubmitting}
            loadingLabel="Sending reset link"
          >
            Send reset link
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
