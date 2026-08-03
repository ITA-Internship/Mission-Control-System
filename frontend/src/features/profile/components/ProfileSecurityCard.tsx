import {
  Activity,
  Clock,
  Lock,
} from "lucide-react";

import type { CurrentUser } from "../../../shared/types/accounts";
import { getUserIdentifier } from "../utils/profileUtils";
import {
  Card,
  FieldLabel,
} from "./ProfilePrimitives";

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
    <Card
      id="security"
      title="Account & Security"
    >
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <FieldLabel>
            Account Status
          </FieldLabel>
          <span
            className="inline-flex w-fit items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold"
            style={{
              color: "#3FB950",
              background:
                "rgba(63,185,80,.1)",
              borderColor:
                "rgba(63,185,80,.25)",
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

        <div className="flex flex-col gap-1.5">
          <FieldLabel>Account ID</FieldLabel>
          <span
            className="text-sm font-mono"
            style={{
              color: "#8A94A6",
            }}
          >
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
                style={{
                  color: "#8A94A6",
                }}
              />
              <span
                className="text-sm font-mono"
                style={{
                  color: "#8A94A6",
                }}
              >
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
            <span
              className="text-sm"
              style={{
                color: "#8A94A6",
              }}
            >
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
                style={{
                  color: "#8A94A6",
                }}
              />
              <span
                className="text-sm font-mono"
                style={{
                  color: "#8A94A6",
                }}
              >
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
              style={{
                color: "#8A94A6",
              }}
            />
            <span
              className="text-sm"
              style={{
                color: "#8A94A6",
              }}
            >
              Password
            </span>
          </div>
        </div>
      </div>

      <p
        className="mt-5 text-xs"
        style={{
          color: "#4A5568",
        }}
      >
        Account status, role, and unit are administrator-managed. Contact your system admin for changes.
      </p>
    </Card>
  );
}
