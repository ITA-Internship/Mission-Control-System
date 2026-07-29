import { useState } from "react";
import type { FormEvent } from "react";
import { Shield } from "lucide-react";

import { AuthLayout } from "../components/AuthLayout";
import { AuthPageContent } from "../components/AuthPageContent";
import { PasswordInput } from "../components/PasswordInput";
import { PasswordStrength } from "../components/PasswordStrength";
import { SubmitButton } from "../components/SubmitButton";

export function RequiredPasswordChangePage() {
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
        >
          <div className="flex flex-col gap-4">
            <PasswordInput
              id="required-current-password"
              name="currentPassword"
              label="Current password"
              value={currentPassword}
              onChange={(event) =>
                setCurrentPassword(
                  event.target.value,
                )
              }
              autoComplete="current-password"
              required
            />

            <PasswordInput
              id="required-new-password"
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
                  ? "required-password-strength"
                  : undefined
              }
              required
            />

            <PasswordStrength
              id="required-password-strength"
              password={newPassword}
            />

            <PasswordInput
              id="required-confirm-password"
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