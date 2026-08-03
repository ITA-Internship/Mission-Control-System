import { useCallback } from "react";

import { getCurrentUser } from "../../auth/api/authApi";
import { useAsyncData } from "../../../shared/hooks/useAsyncData";
import type { CurrentUser } from "../../auth/types/auth";
import type { AsyncData } from "../../../shared/hooks/useAsyncData";

export function useCurrentUser(): AsyncData<CurrentUser> {
  const load = useCallback(
    (signal: AbortSignal) =>
      getCurrentUser(signal),
    [],
  );

  return useAsyncData(load);
}

export function getUserDisplayName(
  user: CurrentUser | null,
): string {
  if (!user) {
    return "Signed-in user";
  }

  const fullName = [
    user.first_name,
    user.last_name,
  ]
    .filter(Boolean)
    .join(" ")
    .trim();

  return fullName || user.username;
}
