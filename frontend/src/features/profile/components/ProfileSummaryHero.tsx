import {
  Camera,
} from "lucide-react";

import type { CurrentUser } from "../../../shared/types/accounts";
import {
  ProfileAvatarImage,
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
      className="mb-8 overflow-hidden rounded-xl border border-mc-accent/15 bg-mc-card"
      style={{
        boxShadow:
          "0 0 0 1px rgb(200 162 74 / 0.05), 0 4px 24px rgb(0 0 0 / 0.3)",
      }}
    >
      <div
        className="h-px"
        style={{
          background:
            "linear-gradient(90deg, var(--color-mc-accent) 0%, rgb(200 162 74 / 0.15) 50%, transparent 80%)",
        }}
      />

      <div className="flex flex-col items-start gap-5 px-6 py-6 sm:flex-row sm:items-center">
        <button
          type="button"
          className="group relative flex-shrink-0 cursor-pointer"
          onClick={onAvatarClick}
          title="Change avatar"
          aria-label="Change avatar"
        >
          <div className="relative h-[76px] w-[76px] overflow-hidden rounded-full border-2 border-mc-accent/35 bg-mc-accent/[0.08]">
            <div
              className="flex h-full w-full items-center justify-center text-2xl font-bold text-mc-accent"
              aria-hidden={Boolean(avatarDisplay)}
            >
              {getInitials(currentUser)}
            </div>
            <ProfileAvatarImage
              source={avatarDisplay}
              alt="Profile"
              className="absolute inset-0 h-full w-full object-cover"
            />
          </div>

          <div className="absolute inset-0 flex items-center justify-center rounded-full bg-black/60 opacity-0 transition-opacity group-hover:opacity-100">
            <Camera
              size={18}
              className="text-white"
            />
          </div>
        </button>

        <div className="min-w-0 flex-1">
          <div className="mb-1.5 flex flex-wrap items-center gap-2">
            <h2 className="text-xl font-semibold text-mc-text">
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
            <span className="font-mono text-xs text-mc-subtle">
              {getUserIdentifier(currentUser)}
            </span>
          </div>

          <p className="font-mono text-xs text-mc-muted">
            {currentUser.email}
          </p>
        </div>

        <div className="flex-shrink-0 self-start sm:self-auto">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-mc-success/20 bg-mc-success/[0.08] px-3 py-1.5 text-xs font-semibold text-mc-success">
            <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-mc-success" />
            {currentUser.is_active
              ? "Active"
              : "Inactive"}
          </span>
        </div>
      </div>
    </div>
  );
}
