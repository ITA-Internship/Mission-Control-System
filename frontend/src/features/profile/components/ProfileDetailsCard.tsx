import type {
  RefObject,
} from "react";

import { Alert } from "../../../shared/components/Alert";
import { Panel } from "../../../shared/components/Panel";
import type { CurrentUser } from "../../../shared/types/accounts";
import {
  getRoleLabel,
  getUnitLabel,
} from "../utils/profileUtils";
import type {
  ProfileFormState,
  StatusBanner,
} from "../types/profile";
import {
  FieldLabel,
  FormTextInput,
  PrimaryButton,
  RoleBadge,
  SecondaryButton,
} from "./ProfilePrimitives";

export function ProfileDetailsCard({
  currentUser,
  profileBanner,
  profileEditing,
  profileSaving,
  profileForm,
  profileErrors,
  firstEditableFieldRef,
  onSetProfileField,
  onDismissBanner,
  onEnterEditMode,
  onSave,
  onCancel,
}: {
  currentUser: CurrentUser;
  profileBanner: StatusBanner | null;
  profileEditing: boolean;
  profileSaving: boolean;
  profileForm: ProfileFormState;
  profileErrors: Record<string, string>;
  firstEditableFieldRef: RefObject<HTMLInputElement | null>;
  onSetProfileField: (
    key: keyof ProfileFormState,
    value: string,
  ) => void;
  onDismissBanner: () => void;
  onEnterEditMode: () => void;
  onSave: () => void;
  onCancel: () => void;
}) {
  return (
    <Panel
      id="profile"
      title="Profile Details"
    >
      <div className="flex flex-col gap-5">
        {profileBanner ? (
          <Alert
            variant={profileBanner.type}
            onClose={onDismissBanner}
          >
            {profileBanner.message}
          </Alert>
        ) : null}

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <FieldLabel>
              Full Name
            </FieldLabel>
            {profileEditing ||
            profileSaving ? (
              <div className="grid gap-3">
                <FormTextInput
                  id="profile-first-name"
                  ariaLabel="First name"
                  inputRef={
                    firstEditableFieldRef
                  }
                  value={
                    profileForm.firstName
                  }
                  onChange={(value) =>
                    onSetProfileField(
                      "firstName",
                      value,
                    )
                  }
                  placeholder="First name"
                  error={
                    profileErrors.firstName
                  }
                  disabled={profileSaving}
                  autoComplete="given-name"
                  maxLength={150}
                />
                <FormTextInput
                  id="profile-last-name"
                  ariaLabel="Last name"
                  value={profileForm.lastName}
                  onChange={(value) =>
                    onSetProfileField(
                      "lastName",
                      value,
                    )
                  }
                  placeholder="Last name"
                  error={
                    profileErrors.lastName
                  }
                  disabled={profileSaving}
                  autoComplete="family-name"
                  maxLength={150}
                />
              </div>
            ) : (
              <span className="text-sm text-mc-text">
                {currentUser.first_name}{" "}
                {currentUser.last_name}
              </span>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <FieldLabel htmlFor="profile-rank">
              Rank
            </FieldLabel>
            {profileEditing ||
            profileSaving ? (
              <FormTextInput
                id="profile-rank"
                value={profileForm.rank}
                onChange={(value) =>
                  onSetProfileField(
                    "rank",
                    value,
                  )
                }
                placeholder="e.g. Major"
                error={profileErrors.rank}
                disabled={profileSaving}
                maxLength={100}
              />
            ) : (
              <span className="text-sm text-mc-text">
                {currentUser.rank ||
                  "Not set"}
              </span>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <FieldLabel>
              Email Address
            </FieldLabel>
            <span className="font-mono text-sm text-mc-muted">
              {currentUser.email}
            </span>
            <span className="text-xs text-mc-subtle">
              Managed by administrators - not editable
            </span>
          </div>

          <div className="flex flex-col gap-1.5">
            <FieldLabel htmlFor="profile-contact">
              Phone / Contact
            </FieldLabel>
            {profileEditing ||
            profileSaving ? (
              <FormTextInput
                id="profile-contact"
                value={profileForm.contact}
                onChange={(value) =>
                  onSetProfileField(
                    "contact",
                    value,
                  )
                }
                type="tel"
                placeholder="+1 (000) 000-0000"
                error={profileErrors.contact}
                disabled={profileSaving}
                maxLength={255}
                autoComplete="tel"
              />
            ) : (
              <span className="font-mono text-sm text-mc-text">
                {currentUser.contact ||
                  "Not set"}
              </span>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <FieldLabel>
              Military Unit
            </FieldLabel>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm text-mc-muted">
                {getUnitLabel(currentUser)}
              </span>
              <span className="rounded bg-mc-muted/10 px-1.5 py-0.5 text-xs text-mc-muted">
                Admin-managed
              </span>
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <FieldLabel>Role</FieldLabel>
            <div className="flex flex-wrap items-center gap-2">
              <RoleBadge
                role={getRoleLabel(
                  currentUser,
                )}
              />
              <span className="text-xs text-mc-subtle">
                Admin-managed - not editable
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 border-t border-mc-border pt-4">
          {!profileEditing &&
          !profileSaving ? (
            <PrimaryButton
              onClick={onEnterEditMode}
            >
              Edit Profile
            </PrimaryButton>
          ) : (
            <>
              <PrimaryButton
                onClick={onSave}
                loading={profileSaving}
                disabled={profileSaving}
              >
                {profileSaving
                  ? "Saving..."
                  : "Save Changes"}
              </PrimaryButton>
              {!profileSaving ? (
                <SecondaryButton
                  onClick={onCancel}
                >
                  Cancel
                </SecondaryButton>
              ) : null}
            </>
          )}
        </div>
      </div>
    </Panel>
  );
}
