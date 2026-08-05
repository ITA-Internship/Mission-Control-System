import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
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

  const initialSessionRequestRef =
    useRef<Promise<CurrentUser> | null>(null);

  const authRevisionRef = useRef(0);

  const clearAuthentication =
    useCallback(() => {
        authRevisionRef.current += 1;

        setCurrentUser(null);
        setStatus("unauthenticated");
        setError(null);
    }, []);

  const setAuthenticatedUser =
    useCallback((user: CurrentUser) => {
        authRevisionRef.current += 1;

        setCurrentUser(user);
        setStatus("authenticated");
        setError(null);
    }, []);

    const refreshCurrentUser =
        useCallback(
        async (
            signal?: AbortSignal,
        ): Promise<CurrentUser | null> => {
            const revisionAtStart =
            authRevisionRef.current;

            try {
            const user =
                await getCurrentUser(signal);

            if (
                revisionAtStart !==
                authRevisionRef.current
            ) {
                throw new DOMException(
                "Stale authentication request.",
                "AbortError",
                );
            }

            setAuthenticatedUser(user);

            return user;
            } catch (requestError) {
            if (isAbortError(requestError)) {
                throw requestError;
            }

            if (
                revisionAtStart !==
                authRevisionRef.current
            ) {
                throw new DOMException(
                "Stale authentication request.",
                "AbortError",
                );
            }

            if (
                isSessionAuthenticationError(
                requestError,
                )
            ) {
                clearAuthentication();

                return null;
            }

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
        let isActive = true;

        const revisionAtStart =
        authRevisionRef.current;

        initialSessionRequestRef.current ??=
        getCurrentUser();

        void initialSessionRequestRef.current
        .then((user) => {
            if (
            !isActive ||
            revisionAtStart !==
                authRevisionRef.current
            ) {
            return;
            }

            setAuthenticatedUser(user);
        })
        .catch((requestError) => {
            if (
            !isActive ||
            revisionAtStart !==
                authRevisionRef.current ||
            isAbortError(requestError)
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
        });

        return () => {
        isActive = false;
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
