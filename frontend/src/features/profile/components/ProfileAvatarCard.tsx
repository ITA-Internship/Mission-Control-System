import {
  CheckCircle,
  Upload,
} from "lucide-react";
import type {
  ChangeEvent,
  DragEvent,
  RefObject,
} from "react";

import type { CurrentUser } from "../../auth/types/auth";
import type { AvatarState } from "../types/profile";
import { getInitials } from "../utils/profileUtils";
import {
  AlertBanner,
  Card,
} from "./ProfilePrimitives";

export function ProfileAvatarCard({
  currentUser,
  avatarDisplay,
  avatarState,
  avatarError,
  profilePictureError,
  fileInputRef,
  onRemoveAvatar,
  onAvatarDrop,
  onAvatarDragOver,
  onAvatarDragLeave,
  onAvatarInputChange,
  onDismissAvatarError,
  onDismissProfilePictureError,
  onOpenFilePicker,
}: {
  currentUser: CurrentUser;
  avatarDisplay: string | null;
  avatarState: AvatarState;
  avatarError: string;
  profilePictureError?: string;
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
}) {
  return (
    <Card id="avatar" title="Avatar">
      <div className="flex flex-col items-start gap-6 sm:flex-row">
        <div className="flex flex-shrink-0 flex-col items-center gap-2">
          <div
            className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-full border-2"
            style={{
              borderColor:
                "rgba(200,162,74,.3)",
              background: "#1A2233",
            }}
          >
            {avatarDisplay ? (
              <img
                src={avatarDisplay}
                alt="Avatar"
                className="h-full w-full object-cover"
              />
            ) : (
              <span
                className="text-2xl font-bold"
                style={{
                  color: "#C8A24A",
                }}
              >
                {getInitials(currentUser)}
              </span>
            )}
          </div>

          {avatarDisplay ? (
            <button
              type="button"
              onClick={onRemoveAvatar}
              className="text-xs transition-colors"
              style={{
                color: "#E5484D",
              }}
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
            className="relative flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-8 transition-all"
            style={{
              borderColor:
                avatarState ===
                "dragging"
                  ? "#C8A24A"
                  : avatarState === "error"
                    ? "#E5484D"
                    : "rgba(255,255,255,.12)",
              background:
                avatarState ===
                "dragging"
                  ? "rgba(200,162,74,.04)"
                  : "rgba(255,255,255,.015)",
            }}
            aria-label="Upload profile avatar"
          >
            {avatarState === "success" ? (
              <div className="flex flex-col items-center gap-2">
                <CheckCircle
                  size={24}
                  style={{
                    color: "#3FB950",
                  }}
                />
                <span
                  className="text-xs font-medium"
                  style={{
                    color: "#3FB950",
                  }}
                >
                  Ready to save
                </span>
              </div>
            ) : (
              <>
                <Upload
                  size={20}
                  style={{
                    color: "#8A94A6",
                  }}
                />
                <p className="text-center text-sm">
                  <span
                    className="font-medium"
                    style={{
                      color: "#E6EAF0",
                    }}
                  >
                    Drop an image here
                  </span>
                  <span
                    style={{
                      color: "#8A94A6",
                    }}
                  >
                    {" "}
                    or{" "}
                  </span>
                  <span
                    className="font-semibold"
                    style={{
                      color: "#C8A24A",
                    }}
                  >
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
            <AlertBanner
              type="error"
              message={avatarError}
              onClose={onDismissAvatarError}
            />
          ) : null}

          {profilePictureError ? (
            <AlertBanner
              type="error"
              message={profilePictureError}
              onClose={
                onDismissProfilePictureError
              }
            />
          ) : null}

          <p
            className="text-xs"
            style={{
              color: "#8A94A6",
            }}
          >
            Accepted: JPG, PNG, WEBP - max 5 MB. Image will be cropped to a circle.
          </p>
        </div>
      </div>
    </Card>
  );
}
