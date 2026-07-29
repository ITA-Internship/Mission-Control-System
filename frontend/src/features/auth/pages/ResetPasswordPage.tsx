import { useState } from "react";
import type { FormEvent } from "react";
import { ArrowLeft } from "lucide-react";

import { AuthLayout } from "../components/AuthLayout";
import { AuthPageContent } from "../components/AuthPageContent";
import { AuthTextLink } from "../components/AuthTextLink";
import { PasswordInput } from "../components/PasswordInput";
import { PasswordStrength } from "../components/PasswordStrength";
import { SubmitButton } from "../components/SubmitButton";

export function ResetPasswordPage() {
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
        headingId="reset-password-heading"
        title="Set a new password"
      >
        <form
          className="flex flex-col gap-5"
          onSubmit={handleSubmit}
        >
          <div className="flex flex-col gap-4">
            <PasswordInput
              id="reset-new-password"
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
                  ? "reset-password-strength"
                  : undefined
              }
              required
            />

            <PasswordStrength
              id="reset-password-strength"
              password={newPassword}
            />

            <PasswordInput
              id="reset-confirm-password"
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
            Update password
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