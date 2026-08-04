import { createContext } from "react";

import type { CurrentUser } from "../../../shared/types/accounts";

export type AuthStatus =
  | "loading"
  | "authenticated"
  | "unauthenticated";

export interface AuthContextValue {
  status: AuthStatus;
  currentUser: CurrentUser | null;
  error: string | null;

  refreshCurrentUser: (
    signal?: AbortSignal,
  ) => Promise<CurrentUser | null>;

  setAuthenticatedUser: (
    user: CurrentUser,
  ) => void;

  clearAuthentication: () => void;

  logout: (
    signal?: AbortSignal,
  ) => Promise<void>;
}

export const AuthContext =
  createContext<AuthContextValue | null>(null);
