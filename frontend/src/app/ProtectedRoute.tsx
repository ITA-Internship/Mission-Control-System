import {
  Navigate,
  useLocation,
} from "react-router";

import {
  buildLoginPath,
  buildRequiredPasswordChangePath,
} from "../features/auth/utils/returnTo";

import {
  useAuth,
} from "../features/auth/hooks/useAuth";
import { AppShell } from "../shared/layout/AppShell";

export function ProtectedRoute() {
  const {
    status,
    currentUser,
    error,
  } = useAuth();

  const location = useLocation();

  const requestedRoute = [
    location.pathname,
    location.search,
    location.hash,
  ].join("");

  if (status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-mc-bg">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-mc-border border-t-mc-accent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-mc-bg">
        <p>{error}</p>
      </div>
    );
  }

  if (
    status === "unauthenticated" ||
    !currentUser
  ) {
    return (
      <Navigate
        to={buildLoginPath(
          requestedRoute,
        )}
        replace
      />
    );
  }

  if (currentUser.must_change_password) {
    return (
      <Navigate
        to={buildRequiredPasswordChangePath(
          requestedRoute,
        )}
        replace
      />
    );
  }

  return (
    <AppShell user={currentUser} />
  );
}
