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

import type {
  PasswordFormState,
  PasswordRequirement,
  PasswordStrength,
  PasswordVisibilityKey,
  StatusBanner,
} from "../types/profile";
import {
  AlertBanner,
  Card,
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
      style={{
        color: "#8A94A6",
      }}
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
    <Card
      id="password"
      title="Change Password"
    >
      <form
        className="flex flex-col gap-5"
        onSubmit={onSubmit}
      >
        {passwordBanner ? (
          <AlertBanner
            type={passwordBanner.type}
            message={passwordBanner.message}
            onClose={onDismissBanner}
          />
        ) : null}

        <div className="grid gap-4">
          <div className="flex flex-col gap-1.5">
            <FieldLabel>
              Current Password
            </FieldLabel>
            <FormTextInput
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
            <FieldLabel>
              New Password
            </FieldLabel>
            <FormTextInput
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
            <div
              className="rounded-lg border p-3"
              style={{
                borderColor:
                  "rgba(255,255,255,.07)",
                background:
                  "rgba(255,255,255,.02)",
              }}
            >
              <div className="mb-2 flex items-center justify-between gap-3">
                <span
                  className="text-xs font-semibold uppercase tracking-widest"
                  style={{
                    color: "#8A94A6",
                  }}
                >
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
                      className="h-1.5 flex-1 rounded-full"
                      style={{
                        background:
                          index <=
                          passwordStrength.score
                            ? passwordStrength.color
                            : "rgba(255,255,255,.08)",
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
                      className="flex items-center gap-2"
                      style={{
                        color:
                          requirement.ok
                            ? "#3FB950"
                            : "#8A94A6",
                      }}
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
            <FieldLabel>
              Confirm New Password
            </FieldLabel>
            <FormTextInput
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

        <div
          className="border-t pt-4"
          style={{
            borderColor:
              "rgba(255,255,255,.07)",
          }}
        >
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
    </Card>
  );
}
