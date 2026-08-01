import {
  useEffect,
  useState,
} from "react";
import type { ReactNode } from "react";
import {
  useNavigate,
} from "react-router";

import {
  ApiError,
  isAbortError,
} from "../api/apiClient";
import { getCurrentUser } from "../api/authApi";
import { AuthAlert } from "./AuthAlert";
import type { CurrentUser } from "../types/auth";
import { getFormError } from "../utils/authErrors";

export function RequireSessionAuth({
  children,
}: {
  children: (user: CurrentUser) => ReactNode;
}) {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] =
    useState<CurrentUser | null>(null);
  const [loading, setLoading] =
    useState(true);
  const [loadError, setLoadError] =
    useState<string | null>(null);

  useEffect(() => {
    const controller =
      new AbortController();

    async function loadUser() {
      try {
        setLoading(true);
        setLoadError(null);

        const user =
          await getCurrentUser(
            controller.signal,
          );

        if (user.must_change_password) {
          navigate(
            "/change-password/required",
            {
              replace: true,
            },
          );
          return;
        }

        setCurrentUser(user);
      } catch (error) {
        if (isAbortError(error)) {
          return;
        }

        if (
          error instanceof ApiError &&
          error.status === 401
        ) {
          navigate("/login", {
            replace: true,
          });
          return;
        }

        setLoadError(
          getFormError(
            error,
            "We could not verify your session right now.",
          ),
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadUser();

    return () => {
      controller.abort();
    };
  }, [navigate]);

  if (loading) {
    return (
      <div
        className="flex min-h-screen items-center justify-center"
        style={{
          background: "#0B0F14",
          color: "#E6EAF0",
        }}
      >
        <div
          className="rounded-xl border px-6 py-4 text-sm"
          style={{
            background: "#161D26",
            borderColor:
              "rgba(255,255,255,.08)",
          }}
        >
          Loading profile...
        </div>
      </div>
    );
  }

  if (!currentUser || loadError) {
    return (
      <div
        className="flex min-h-screen items-center justify-center px-6"
        style={{
          background: "#0B0F14",
        }}
      >
        <div
          className="flex max-w-md flex-col gap-4 rounded-xl border p-6"
          style={{
            background: "#161D26",
            borderColor:
              "rgba(255,255,255,.08)",
          }}
        >
          <AuthAlert variant="error">
            {loadError ??
              "Profile data is unavailable."}
          </AuthAlert>
        </div>
      </div>
    );
  }

  return <>{children(currentUser)}</>;
}

