import type { ReactNode } from "react";
import { Navigate } from "react-router";

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
        to="/login"
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
        to="/change-password/required"
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
        to="/my-profile"
        replace
      />
    );
  }

  return <>{children(currentUser)}</>;
}
