import {
  Activity,
  Clock,
  Lock,
} from "lucide-react";

import { Panel } from "../../../shared/components/Panel";
import type { CurrentUser } from "../../../shared/types/accounts";
import { getUserIdentifier } from "../utils/profileUtils";
import { FieldLabel } from "./ProfilePrimitives";

export function ProfileSecurityCard({
  currentUser,
  createdAtLabel,
  lastLoginLabel,
}: {
  currentUser: CurrentUser;
  createdAtLabel: string | null;
  lastLoginLabel: string | null;
}) {
  return (
    <Panel
      id="security"
      title="Account & Security"
    >
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <FieldLabel>
            Account Status
          </FieldLabel>
          <span className="inline-flex w-fit items-center gap-1.5 rounded-full border border-mc-success/25 bg-mc-success/10 px-2.5 py-1 text-xs font-semibold text-mc-success">
            <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-mc-success" />
            {currentUser.is_active
              ? "Active"
              : "Inactive"}
          </span>
        </div>

        <div className="flex flex-col gap-1.5">
          <FieldLabel>Account ID</FieldLabel>
          <span className="font-mono text-sm text-mc-muted">
            {getUserIdentifier(currentUser)}
          </span>
        </div>

        {createdAtLabel ? (
          <div className="flex flex-col gap-1.5">
            <FieldLabel>
              Date Joined
            </FieldLabel>
            <div className="flex items-center gap-2">
              <Clock
                size={13}
                className="text-mc-muted"
              />
              <span className="font-mono text-sm text-mc-muted">
                {createdAtLabel}
              </span>
            </div>
          </div>
        ) : null}

        {currentUser.created_by_username ? (
          <div className="flex flex-col gap-1.5">
            <FieldLabel>
              Account Created By
            </FieldLabel>
            <span className="text-sm text-mc-muted">
              {currentUser.created_by_username}
            </span>
          </div>
        ) : null}

        {lastLoginLabel ? (
          <div className="flex flex-col gap-1.5">
            <FieldLabel>
              Last Login
            </FieldLabel>
            <div className="flex items-center gap-2">
              <Activity
                size={13}
                className="text-mc-muted"
              />
              <span className="font-mono text-sm text-mc-muted">
                {lastLoginLabel}
              </span>
            </div>
          </div>
        ) : null}

        <div className="flex flex-col gap-1.5">
          <FieldLabel>
            Authentication
          </FieldLabel>
          <div className="flex items-center gap-2">
            <Lock
              size={13}
              className="text-mc-muted"
            />
            <span className="text-sm text-mc-muted">
              Password
            </span>
          </div>
        </div>
      </div>

      <p className="mt-5 text-xs text-mc-subtle">
        Account status, role, and unit are administrator-managed. Contact your system admin for changes.
      </p>
    </Panel>
  );
}
