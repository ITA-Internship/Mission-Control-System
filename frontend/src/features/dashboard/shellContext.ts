import { useOutletContext } from "react-router";

import type { CurrentUser } from "../auth/types/auth";
import type { RoleCode } from "./types/dashboard";
import { ROLE_CODES } from "./types/dashboard";

export interface ShellContext {
  user: CurrentUser;
}

export function useShellContext(): ShellContext {
  return useOutletContext<ShellContext>();
}

/* Narrow the user's raw `role_code` string to a known RoleCode, or null. */
export function toRoleCode(
  value: string | null | undefined,
): RoleCode | null {
  if (value && (ROLE_CODES as string[]).includes(value)) {
    return value as RoleCode;
  }
  return null;
}

export function displayName(user: CurrentUser): string {
  const full = [user.first_name, user.last_name]
    .filter(Boolean)
    .join(" ")
    .trim();
  return full || user.username;
}

export function initials(user: CurrentUser): string {
  const first = user.first_name?.[0] ?? "";
  const last = user.last_name?.[0] ?? "";
  const combined = `${first}${last}`.trim();
  return (
    combined || user.username.slice(0, 2)
  ).toUpperCase();
}
