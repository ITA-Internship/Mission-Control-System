import {
  CheckCircle,
  Upload,
} from "lucide-react";
import type {
  ChangeEvent,
  DragEvent,
  RefObject,
} from "react";

import { Alert } from "../../../shared/components/Alert";
import { Panel } from "../../../shared/components/Panel";
import type { CurrentUser } from "../../../shared/types/accounts";
import { cn } from "../../../shared/utils/cn";
import type { AvatarState } from "../types/profile";
import { getInitials } from "../utils/profileUtils";
import {
  PrimaryButton,
  ProfileAvatarImage,
  SecondaryButton,
} from "./ProfilePrimitives";

export function ProfileAvatarCard({
  currentUser,
  avatarDisplay,
  avatarState,
  avatarError,
  profilePictureError,
  saving,
  fileInputRef,
  onRemoveAvatar,
  onAvatarDrop,
  onAvatarDragOver,
  onAvatarDragLeave,
  onAvatarInputChange,
  onDismissAvatarError,
  onDismissProfilePictureError,
  onOpenFilePicker,
  onSave,
  onCancel,
}: {
  currentUser: CurrentUser;
  avatarDisplay: string | null;
  avatarState: AvatarState;
  avatarError: string;
  profilePictureError?: string;
  saving: boolean;
  fileInputRef: RefObject<HTMLInputElement | null>;
  onRemoveAvatar: () => void;
  onAvatarDrop: (
    event: DragEvent<HTMLDivElement>,
  ) => void;
  onAvatarDragOver: (
    event: DragEvent<HTMLDivElement>,
  ) => void;
  onAvatarDragLeave: () => void;
  onAvatarInputChange: (
    event: ChangeEvent<HTMLInputElement>,
  ) => void;
  onDismissAvatarError: () => void;
  onDismissProfilePictureError: () => void;
  onOpenFilePicker: () => void;
  onSave: () => void;
  onCancel: () => void;
}) {
  return (
    <Panel id="avatar" title="Avatar">
      <div className="flex flex-col items-start gap-6 sm:flex-row">
        <div className="flex flex-shrink-0 flex-col items-center gap-2">
          <div className="relative flex h-24 w-24 items-center justify-center overflow-hidden rounded-full border-2 border-mc-accent/30 bg-mc-elevated">
            <span
              className="text-2xl font-bold text-mc-accent"
              aria-hidden={Boolean(avatarDisplay)}
            >
              {getInitials(currentUser)}
            </span>
            <ProfileAvatarImage
              source={avatarDisplay}
              alt="Avatar"
              className="absolute inset-0 h-full w-full object-cover"
            />
          </div>

          {avatarDisplay ? (
            <button
              type="button"
              onClick={onRemoveAvatar}
              className="text-xs text-mc-error transition-colors hover:text-mc-error/80"
              aria-label="Remove selected avatar"
            >
              Remove
            </button>
          ) : null}
        </div>

        <div className="flex flex-1 flex-col gap-3">
          <div
            role="button"
            tabIndex={0}
            onDrop={onAvatarDrop}
            onDragOver={onAvatarDragOver}
            onDragLeave={onAvatarDragLeave}
            onClick={onOpenFilePicker}
            onKeyDown={(event) => {
              if (
                event.key === "Enter" ||
                event.key === " "
              ) {
                event.preventDefault();
                onOpenFilePicker();
              }
            }}
            className={cn(
              "relative flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-8 transition-colors",
              avatarState === "dragging"
                ? "border-mc-accent bg-mc-accent/[0.04]"
                : avatarState === "error"
                  ? "border-mc-error bg-white/[0.015]"
                  : "border-white/12 bg-white/[0.015]",
            )}
            aria-label="Upload profile avatar"
          >
            {avatarState === "success" ? (
              <div className="flex flex-col items-center gap-2">
                <CheckCircle
                  size={24}
                  className="text-mc-success"
                />
                <span className="text-xs font-medium text-mc-success">
                  Ready to save
                </span>
              </div>
            ) : (
              <>
                <Upload
                  size={20}
                  className="text-mc-muted"
                />
                <p className="text-center text-sm">
                  <span className="font-medium text-mc-text">
                    Drop an image here
                  </span>
                  <span className="text-mc-muted">
                    {" "}
                    or{" "}
                  </span>
                  <span className="font-semibold text-mc-accent">
                    browse files
                  </span>
                </p>
              </>
            )}

            <input
              ref={fileInputRef}
              type="file"
              aria-label="Choose profile avatar"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={onAvatarInputChange}
            />
          </div>

          {avatarState === "error" ? (
            <Alert
              variant="error"
              onClose={onDismissAvatarError}
            >
              {avatarError}
            </Alert>
          ) : null}

          {profilePictureError ? (
            <Alert
              variant="error"
              onClose={onDismissProfilePictureError}
            >
              {profilePictureError}
            </Alert>
          ) : null}

          {avatarState === "success" ? (
            <div className="flex flex-wrap gap-3 border-t border-mc-border pt-4">
              <PrimaryButton
                onClick={onSave}
                loading={saving}
                disabled={saving}
              >
                {saving
                  ? "Saving..."
                  : "Save all changes"}
              </PrimaryButton>
              {!saving ? (
                <SecondaryButton
                  onClick={onCancel}
                >
                  Cancel avatar change
                </SecondaryButton>
              ) : null}
            </div>
          ) : null}

          <p className="text-xs text-mc-muted">
            Accepted: JPG, PNG, WEBP - max 5 MB. Image will be cropped to a circle.
          </p>
        </div>
      </div>
    </Panel>
  );
}
