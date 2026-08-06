import {
  AlertCircle,
  CheckCircle,
  Eye,
  EyeOff,
} from "lucide-react";
import type {
  FormEvent,
  RefObject,
} from "react";

import { Alert } from "../../../shared/components/Alert";
import { Panel } from "../../../shared/components/Panel";
import { cn } from "../../../shared/utils/cn";
import type {
  PasswordFormState,
  PasswordRequirement,
  PasswordStrength,
  PasswordVisibilityKey,
  StatusBanner,
} from "../types/profile";
import {
  FieldLabel,
  FormTextInput,
  PrimaryButton,
} from "./ProfilePrimitives";

function PasswordToggleButton({
  isVisible,
  onClick,
}: {
  isVisible: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={
        isVisible
          ? "Hide password"
          : "Show password"
      }
      className="text-mc-muted transition-colors hover:text-mc-accent"
    >
      {isVisible ? (
        <EyeOff size={15} />
      ) : (
        <Eye size={15} />
      )}
    </button>
  );
}

export function ProfilePasswordCard({
  passwordBanner,
  passwordForm,
  passwordErrors,
  passwordStatus,
  passwordVisibility,
  passwordStrength,
  passwordRequirements,
  currentPasswordRef,
  onDismissBanner,
  onSubmit,
  onSetPasswordField,
  onToggleVisibility,
}: {
  passwordBanner: StatusBanner | null;
  passwordForm: PasswordFormState;
  passwordErrors: Record<string, string>;
  passwordStatus: "idle" | "saving";
  passwordVisibility: Record<
    PasswordVisibilityKey,
    boolean
  >;
  passwordStrength: PasswordStrength;
  passwordRequirements: PasswordRequirement[];
  currentPasswordRef: RefObject<HTMLInputElement | null>;
  onDismissBanner: () => void;
  onSubmit: (
    event: FormEvent<HTMLFormElement>,
  ) => void;
  onSetPasswordField: (
    key: keyof PasswordFormState,
    value: string,
  ) => void;
  onToggleVisibility: (
    key: PasswordVisibilityKey,
  ) => void;
}) {
  return (
    <Panel
      id="password"
      title="Change Password"
    >
      <form
        className="flex flex-col gap-5"
        onSubmit={onSubmit}
      >
        {passwordBanner ? (
          <Alert
            variant={passwordBanner.type}
            onClose={onDismissBanner}
          >
            {passwordBanner.message}
          </Alert>
        ) : null}

        <div className="grid gap-4">
          <div className="flex flex-col gap-1.5">
            <FieldLabel htmlFor="profile-current-password">
              Current Password
            </FieldLabel>
            <FormTextInput
              id="profile-current-password"
              inputRef={currentPasswordRef}
              value={
                passwordForm.currentPassword
              }
              onChange={(value) =>
                onSetPasswordField(
                  "currentPassword",
                  value,
                )
              }
              placeholder="Enter current password"
              type={
                passwordVisibility.current
                  ? "text"
                  : "password"
              }
              error={
                passwordErrors.currentPassword
              }
              autoComplete="current-password"
              rightElement={
                <PasswordToggleButton
                  isVisible={
                    passwordVisibility.current
                  }
                  onClick={() =>
                    onToggleVisibility(
                      "current",
                    )
                  }
                />
              }
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <FieldLabel htmlFor="profile-new-password">
              New Password
            </FieldLabel>
            <FormTextInput
              id="profile-new-password"
              value={passwordForm.newPassword}
              onChange={(value) =>
                onSetPasswordField(
                  "newPassword",
                  value,
                )
              }
              placeholder="Enter new password"
              type={
                passwordVisibility.next
                  ? "text"
                  : "password"
              }
              error={
                passwordErrors.newPassword
              }
              autoComplete="new-password"
              rightElement={
                <PasswordToggleButton
                  isVisible={
                    passwordVisibility.next
                  }
                  onClick={() =>
                    onToggleVisibility("next")
                  }
                />
              }
            />
          </div>

          {passwordForm.newPassword ? (
            <div className="rounded-lg border border-mc-border bg-white/[0.02] p-3">
              <div className="mb-2 flex items-center justify-between gap-3">
                <span className="text-xs font-semibold uppercase tracking-widest text-mc-muted">
                  Password Strength
                </span>
                <span
                  className="text-xs font-medium"
                  style={{
                    color:
                      passwordStrength.color,
                  }}
                >
                  {passwordStrength.label}
                </span>
              </div>
              <div className="mb-3 flex gap-1.5">
                {[1, 2, 3, 4, 5].map(
                  (index) => (
                    <span
                      key={index}
                      className={cn(
                        "h-1.5 flex-1 rounded-full",
                        index <=
                          passwordStrength.score
                          ? ""
                          : "bg-white/8",
                      )}
                      style={{
                        background:
                          index <=
                          passwordStrength.score
                            ? passwordStrength.color
                            : undefined,
                      }}
                    />
                  ),
                )}
              </div>
              <ul className="grid gap-1.5 text-xs">
                {passwordRequirements.map(
                  (requirement) => (
                    <li
                      key={requirement.label}
                      className={cn(
                        "flex items-center gap-2",
                        requirement.ok
                          ? "text-mc-success"
                          : "text-mc-muted",
                      )}
                    >
                      {requirement.ok ? (
                        <CheckCircle
                          size={12}
                        />
                      ) : (
                        <AlertCircle
                          size={12}
                        />
                      )}
                      {requirement.label}
                    </li>
                  ),
                )}
              </ul>
            </div>
          ) : null}

          <div className="flex flex-col gap-1.5">
            <FieldLabel htmlFor="profile-confirm-password">
              Confirm New Password
            </FieldLabel>
            <FormTextInput
              id="profile-confirm-password"
              value={
                passwordForm.confirmPassword
              }
              onChange={(value) =>
                onSetPasswordField(
                  "confirmPassword",
                  value,
                )
              }
              placeholder="Confirm new password"
              type={
                passwordVisibility.confirm
                  ? "text"
                  : "password"
              }
              error={
                passwordErrors.confirmPassword
              }
              autoComplete="new-password"
              rightElement={
                <PasswordToggleButton
                  isVisible={
                    passwordVisibility.confirm
                  }
                  onClick={() =>
                    onToggleVisibility(
                      "confirm",
                    )
                  }
                />
              }
            />
          </div>
        </div>

        <div className="border-t border-mc-border pt-4">
          <PrimaryButton
            type="submit"
            loading={
              passwordStatus === "saving"
            }
            disabled={
              passwordStatus === "saving"
            }
          >
            {passwordStatus === "saving"
              ? "Updating..."
              : "Update Password"}
          </PrimaryButton>
        </div>
      </form>
    </Panel>
  );
}
