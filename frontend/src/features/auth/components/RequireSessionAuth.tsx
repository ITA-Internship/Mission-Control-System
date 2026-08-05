import type { ReactNode } from "react";
import {
  Navigate,
  useLocation,
} from "react-router";

import {
  buildLoginPath,
  buildRequiredPasswordChangePath,
  DEFAULT_AUTHENTICATED_ROUTE,
  getSafeReturnTo,
} from "../utils/returnTo";

import type {
  CurrentUser,
} from "../../../shared/types/accounts";
import {
  useAuth,
} from "../hooks/useAuth";
import { AuthAlert } from "./AuthAlert";

export function RequireSessionAuth({
  children,
  requirePasswordChange = false,
}: {
  children: (
    user: CurrentUser,
  ) => ReactNode;
  requirePasswordChange?: boolean;
}) {
  const {
    status,
    currentUser,
    error,
  } = useAuth();

  const location = useLocation();

  const returnToFromQuery =
    getSafeReturnTo(
      new URLSearchParams(
        location.search,
      ).get("returnTo"),
    );

  const currentRoute =
    getSafeReturnTo(
      [
        location.pathname,
        location.search,
        location.hash,
      ].join(""),
    );

  const requestedReturnTo =
    requirePasswordChange
      ? returnToFromQuery
      : currentRoute;

  if (status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center">
        Loading profile...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center px-6">
        <AuthAlert variant="error">
          {error}
        </AuthAlert>
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
          requestedReturnTo,
        )}
        replace
      />
    );
  }

  if (
    currentUser.must_change_password &&
    !requirePasswordChange
  ) {
    return (
      <Navigate
        to={buildRequiredPasswordChangePath(
          requestedReturnTo,
        )}
        replace
      />
    );
  }

  if (
    !currentUser.must_change_password &&
    requirePasswordChange
  ) {
    return (
      <Navigate
        to={
          returnToFromQuery ??
          DEFAULT_AUTHENTICATED_ROUTE
        }
        replace
      />
    );
  }

  return <>{children(currentUser)}</>;
}
