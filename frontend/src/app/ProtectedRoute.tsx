import { useEffect, useState } from "react";
import { Navigate } from "react-router";

import {
  ApiError,
  isAbortError,
} from "../shared/api/apiClient";
import { getCurrentUser } from "../features/auth/api/authApi";
import { AppShell } from "../features/dashboard/components/AppShell";
import type { CurrentUser } from "../features/auth/types/auth";

type AuthState =
  | { status: "loading" }
  | { status: "authed"; user: CurrentUser }
  | { status: "unauthed" };

/* Route guard for authenticated pages. Resolves the current user from the
 * session cookie; unauthenticated visitors are redirected to sign in. The
 * backend session is the source of truth — this only reflects it. */
export function ProtectedRoute() {
  const [state, setState] = useState<AuthState>({
    status: "loading",
  });

  useEffect(() => {
    const controller = new AbortController();

    getCurrentUser(controller.signal)
      .then((user) => setState({ status: "authed", user }))
      .catch((error) => {
        if (isAbortError(error)) return;
        if (
          error instanceof ApiError &&
          (error.status === 401 || error.status === 403)
        ) {
          setState({ status: "unauthed" });
          return;
        }
        // Network or unexpected error: fail closed to the login screen.
        setState({ status: "unauthed" });
      });

    return () => controller.abort();
  }, []);

  if (state.status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-mc-bg">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-mc-border border-t-mc-accent" />
      </div>
    );
  }

  if (state.status === "unauthed") {
    return <Navigate to="/login" replace />;
  }

  if (state.user.must_change_password) {
    return <Navigate to="/change-password/required" replace />;
  }

  return <AppShell user={state.user} />;
}
