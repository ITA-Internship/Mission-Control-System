import { useState } from "react";
import type { FormEvent } from "react";
import { ArrowLeft } from "lucide-react";

import { AuthLayout } from "../components/AuthLayout";
import { AuthPageContent } from "../components/AuthPageContent";
import { AuthTextLink } from "../components/AuthTextLink";
import { PasswordInput } from "../components/PasswordInput";
import { PasswordStrength } from "../components/PasswordStrength";
import { SubmitButton } from "../components/SubmitButton";

export function ActivateAccountPage() {
  const [newPassword, setNewPassword] = useState("");
  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("");
  const [
    confirmPasswordError,
    setConfirmPasswordError,
  ] = useState<string>();

  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (newPassword !== confirmPassword) {
      setConfirmPasswordError(
        "Passwords do not match.",
      );
      return;
    }

    setConfirmPasswordError(undefined);
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
        >
          <div className="flex flex-col gap-4">
            <PasswordInput
              id="activation-new-password"
              name="newPassword"
              label="New password"
              value={newPassword}
              onChange={(event) => {
                setNewPassword(event.target.value);
                setConfirmPasswordError(undefined);
              }}
              autoComplete="new-password"
              aria-describedby={
                newPassword
                  ? "activation-password-strength"
                  : undefined
              }
              required
            />

            <PasswordStrength
              id="activation-password-strength"
              password={newPassword}
            />

            <PasswordInput
              id="activation-confirm-password"
              name="confirmPassword"
              label="Confirm new password"
              value={confirmPassword}
              onChange={(event) => {
                setConfirmPassword(
                  event.target.value,
                );
                setConfirmPasswordError(undefined);
              }}
              autoComplete="new-password"
              error={confirmPasswordError}
              required
            />
          </div>

          <SubmitButton>
            Activate account
          </SubmitButton>

          <div className="flex">
            <AuthTextLink
              to="/login"
              icon={<ArrowLeft size={14} />}
            >
              Back to sign in
            </AuthTextLink>
          </div>
        </form>
      </AuthPageContent>
    </AuthLayout>
  );
}