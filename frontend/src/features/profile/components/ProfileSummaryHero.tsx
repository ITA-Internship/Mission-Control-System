import {
  Camera,
} from "lucide-react";

import type { CurrentUser } from "../../auth/types/auth";
import {
  RoleBadge,
  UnitChip,
} from "./ProfilePrimitives";
import {
  getInitials,
  getRoleLabel,
  getUnitLabel,
  getUserIdentifier,
} from "../utils/profileUtils";

export function ProfileSummaryHero({
  currentUser,
  avatarDisplay,
  onAvatarClick,
}: {
  currentUser: CurrentUser;
  avatarDisplay: string | null;
  onAvatarClick: () => void;
}) {
  return (
    <div
      className="mb-8 overflow-hidden rounded-xl border"
      style={{
        background: "#161D26",
        borderColor:
          "rgba(200,162,74,.15)",
        boxShadow:
          "0 0 0 1px rgba(200,162,74,.05), 0 4px 24px rgba(0,0,0,.3)",
      }}
    >
      <div
        className="h-px"
        style={{
          background:
            "linear-gradient(90deg, #C8A24A 0%, rgba(200,162,74,.15) 50%, transparent 80%)",
        }}
      />

      <div className="flex flex-col items-start gap-5 px-6 py-6 sm:flex-row sm:items-center">
        <div
          className="group relative flex-shrink-0 cursor-pointer"
          onClick={onAvatarClick}
          title="Change avatar"
        >
          <div
            className="h-[76px] w-[76px] overflow-hidden rounded-full border-2"
            style={{
              borderColor:
                "rgba(200,162,74,.35)",
              background:
                "rgba(200,162,74,.08)",
            }}
          >
            {avatarDisplay ? (
              <img
                src={avatarDisplay}
                alt="Profile"
                className="h-full w-full object-cover"
              />
            ) : (
              <div
                className="flex h-full w-full items-center justify-center text-2xl font-bold"
                style={{
                  color: "#C8A24A",
                }}
              >
                {getInitials(currentUser)}
              </div>
            )}
          </div>

          <div
            className="absolute inset-0 flex items-center justify-center rounded-full opacity-0 transition-opacity group-hover:opacity-100"
            style={{
              background:
                "rgba(0,0,0,.6)",
            }}
          >
            <Camera
              size={18}
              style={{
                color: "#fff",
              }}
            />
          </div>
        </div>

        <div className="min-w-0 flex-1">
          <div className="mb-1.5 flex flex-wrap items-center gap-2">
            <h2
              className="text-xl font-semibold"
              style={{
                color: "#E6EAF0",
              }}
            >
              {currentUser.rank
                ? `${currentUser.rank} ${currentUser.first_name} ${currentUser.last_name}`
                : `${currentUser.first_name} ${currentUser.last_name}`}
            </h2>
            <RoleBadge
              role={getRoleLabel(currentUser)}
            />
          </div>

          <div className="mb-2 flex flex-wrap items-center gap-2">
            <UnitChip
              unit={getUnitLabel(currentUser)}
            />
            <span
              className="text-xs font-mono"
              style={{
                color: "#4A5568",
              }}
            >
              {getUserIdentifier(currentUser)}
            </span>
          </div>

          <p
            className="text-xs font-mono"
            style={{
              color: "#8A94A6",
            }}
          >
            {currentUser.email}
          </p>
        </div>

        <div className="flex-shrink-0 self-start sm:self-auto">
          <span
            className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold"
            style={{
              color: "#3FB950",
              background:
                "rgba(63,185,80,.08)",
              borderColor:
                "rgba(63,185,80,.2)",
            }}
          >
            <span
              className="inline-block h-1.5 w-1.5 animate-pulse rounded-full"
              style={{
                background: "#3FB950",
              }}
            />
            {currentUser.is_active
              ? "Active"
              : "Inactive"}
          </span>
        </div>
      </div>
    </div>
  );
}

