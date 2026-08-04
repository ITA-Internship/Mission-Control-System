import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";

import {
  getCurrentUser,
  signOut,
} from "../api/authApi";
import {
  isAbortError,
} from "../../../shared/api/apiClient";
import type { CurrentUser } from "../../../shared/types/accounts";
import {
  getFormError,
  isSessionAuthenticationError,
} from "../utils/authErrors";
import {
  AuthContext,
} from "./AuthContext";
import type {
  AuthContextValue,
  AuthStatus,
} from "./AuthContext";

export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [status, setStatus] =
    useState<AuthStatus>("loading");

  const [currentUser, setCurrentUser] =
    useState<CurrentUser | null>(null);

  const [error, setError] =
    useState<string | null>(null);

  const clearAuthentication =
    useCallback(() => {
      setCurrentUser(null);
      setStatus("unauthenticated");
      setError(null);
    }, []);

  const setAuthenticatedUser =
    useCallback((user: CurrentUser) => {
      setCurrentUser(user);
      setStatus("authenticated");
      setError(null);
    }, []);

  const refreshCurrentUser =
    useCallback(
      async (
        signal?: AbortSignal,
      ): Promise<CurrentUser | null> => {
        try {
          const user =
            await getCurrentUser(signal);

          setAuthenticatedUser(user);
          return user;
        } catch (requestError) {
          if (isAbortError(requestError)) {
            throw requestError;
          }

          if (
            isSessionAuthenticationError(
              requestError,
            )
          ) {
            clearAuthentication();
            return null;
          }

          setCurrentUser(null);
          setStatus("unauthenticated");
          setError(
            getFormError(
              requestError,
              "We could not verify your session right now.",
            ),
          );

          throw requestError;
        }
      },
      [
        clearAuthentication,
        setAuthenticatedUser,
      ],
    );

  const logout = useCallback(
    async (signal?: AbortSignal) => {
      await signOut(signal);
      clearAuthentication();
    },
    [clearAuthentication],
  );

  useEffect(() => {
    const controller =
        new AbortController();

    async function restoreSession() {
        try {
        const user = await getCurrentUser(
            controller.signal,
        );

        if (controller.signal.aborted) {
            return;
        }

        setAuthenticatedUser(user);
        } catch (requestError) {
        if (
            isAbortError(requestError) ||
            controller.signal.aborted
        ) {
            return;
        }

        if (
            isSessionAuthenticationError(
            requestError,
            )
        ) {
            clearAuthentication();
            return;
        }

        setCurrentUser(null);
        setStatus("unauthenticated");
        setError(
            getFormError(
            requestError,
            "We could not verify your session right now.",
            ),
        );
        }
    }

    void restoreSession();

    return () => {
        controller.abort();
    };
    }, [
    clearAuthentication,
    setAuthenticatedUser,
    ]);

  const value =
    useMemo<AuthContextValue>(
      () => ({
        status,
        currentUser,
        error,
        refreshCurrentUser,
        setAuthenticatedUser,
        clearAuthentication,
        logout,
      }),
      [
        status,
        currentUser,
        error,
        refreshCurrentUser,
        setAuthenticatedUser,
        clearAuthentication,
        logout,
      ],
    );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
