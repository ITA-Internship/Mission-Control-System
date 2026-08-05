import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  createMemoryRouter,
  RouterProvider,
} from "react-router";
import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import { RequireSessionAuth } from "../auth/components/RequireSessionAuth";
import { MyProfilePage } from "./pages/MyProfilePage";
import { useState } from "react";
import type { ReactNode } from "react";

import { signOut } from "../auth/api/authApi";
import {
  AuthContext,
} from "../auth/context/AuthContext";
import type {
  AuthContextValue,
} from "../auth/context/AuthContext";
import type {
  CurrentUser,
} from "../../shared/types/accounts";

const currentUserResponse = {
  id: 47,
  username: "commander.chen",
  email: "s.chen@mil-ops.gov",
  first_name: "Sarah",
  last_name: "Chen",
  rank: "Major",
  contact: "+1 (703) 555-0192",
  profile_picture: null,
  role: 2,
  role_name: "Commander",
  role_code: "COMMANDER",
  unit: 3,
  unit_name: "3rd UAS Battalion",
  unit_code: "UAS-3",
  is_active: true,
  must_change_password: false,
};

function renderPage(
  initialUser: CurrentUser =
    currentUserResponse,
) {
  const router = createMemoryRouter(
    [
      {
        path: "/my-profile",
        Component: MyProfilePage,
      },
      {
        path: "/login",
        element: <div>Login page</div>,
      },
      {
        path: "/change-password/required",
        element: (
          <div>
            Password change required
          </div>
        ),
      },
    ],
    {
      initialEntries: ["/my-profile"],
    },
  );

  return render(
    <TestAuthProvider
      initialUser={initialUser}
    >
      <RouterProvider router={router} />
    </TestAuthProvider>,
  );
}

function renderProtectedPage() {
  const router = createMemoryRouter(
    [
      {
        path: "/my-profile",
        element: (
          <RequireSessionAuth>
            {() => <MyProfilePage />}
          </RequireSessionAuth>
        ),
      },
      {
        path: "/login",
        element: <div>Login page</div>,
      },
      {
        path: "/change-password/required",
        element: (
          <div>
            Password change required
          </div>
        ),
      },
    ],
    {
      initialEntries: ["/my-profile"],
    },
  );

  return render(
    <TestAuthProvider
      initialUser={null}
    >
      <RouterProvider router={router} />
    </TestAuthProvider>,
  );
}

function mockJsonResponse(
  body: unknown,
  status = 200,
) {
  vi.mocked(globalThis.fetch)
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify(body),
        {
          status,
          headers: {
            "Content-Type":
              "application/json",
          },
        },
      ),
    );
}

type TestAuthProviderProps = {
  children: ReactNode;
  initialUser: CurrentUser | null;
};

function TestAuthProvider({
  children,
  initialUser,
}: TestAuthProviderProps) {
  const [
    currentUser,
    setCurrentUser,
  ] = useState<CurrentUser | null>(
    initialUser,
  );

  const value: AuthContextValue = {
    status: currentUser
      ? "authenticated"
      : "unauthenticated",

    currentUser,

    error: null,

    refreshCurrentUser: async () =>
      currentUser,

    setAuthenticatedUser: (user) => {
      setCurrentUser(user);
    },

    clearAuthentication: () => {
      setCurrentUser(null);
    },

    logout: async (signal) => {
      await signOut(signal);
      setCurrentUser(null);
    },
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

describe("MyProfilePage", () => {
  it("loads and updates profile details", async () => {
    const user = userEvent.setup();

    mockJsonResponse({
    ...currentUserResponse,
    rank: "Lt. Colonel",
    contact: "+1 (703) 555-0100",
  });

    renderPage();

    expect(
      await screen.findByText(
        "Major Sarah Chen",
      ),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", {
        name: "Edit Profile",
      }),
    );

    expect(
      screen.getByLabelText("First name"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Last name"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Rank"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Phone / Contact"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Current Password"),
    ).toBeInTheDocument();

    const rankInput =
      screen.getByPlaceholderText(
        "e.g. Major",
      );
    const contactInput =
      screen.getByPlaceholderText(
        "+1 (000) 000-0000",
      );

    await user.clear(rankInput);
    await user.type(
      rankInput,
      "Lt. Colonel",
    );
    await user.clear(contactInput);
    await user.type(
      contactInput,
      "+1 (703) 555-0100",
    );

    await user.click(
      screen.getByRole("button", {
        name: "Save Changes",
      }),
    );

    expect(
      await screen.findByText(
        "Profile changes saved successfully.",
      ),
    ).toBeInTheDocument();

    const fetchMock = vi.mocked(
      globalThis.fetch,
    );
    expect(
      fetchMock.mock.calls[0]?.[0],
    ).toBe("/api/accounts/users/me/");

    expect(
      fetchMock.mock.calls[0]?.[1]
        ?.method,
    ).toBe("PATCH");

    expect(
      fetchMock.mock.calls[0]?.[1]?.body,
    ).toBeInstanceOf(FormData);

    expect(
      new Headers(
        fetchMock.mock.calls[0]?.[1]?.headers,
      ).get("Content-Type"),
    ).toBeNull();
    expect(
      screen.queryByText("Ready to save"),
    ).not.toBeInTheDocument();
  });

  it("shows profile validation errors", async () => {
    const user = userEvent.setup();

    mockJsonResponse(
      {
        contact: [
          "Enter a valid contact value.",
        ],
      },
      400,
    );

    renderPage();

    await screen.findByText(
      "Major Sarah Chen",
    );

    await user.click(
      screen.getByRole("button", {
        name: "Edit Profile",
      }),
    );

    const contactInput =
      screen.getByPlaceholderText(
        "+1 (000) 000-0000",
      );
    await user.clear(contactInput);
    await user.type(
      contactInput,
      "bad-contact",
    );

    await user.click(
      screen.getByRole("button", {
        name: "Save Changes",
      }),
    );

    expect(
      await screen.findAllByText(
        "Enter a valid contact value.",
      ),
    ).not.toHaveLength(0);
  });

  it("shows a save error when profile update fails", async () => {
    const user = userEvent.setup();

    mockJsonResponse(
      {
        detail:
          "Profile update failed.",
      },
      500,
    );

    renderPage();

    await screen.findByText(
      "Major Sarah Chen",
    );

    await user.click(
      screen.getByRole("button", {
        name: "Edit Profile",
      }),
    );

    await user.click(
      screen.getByRole("button", {
        name: "Save Changes",
      }),
    );

    expect(
      await screen.findByText(
        "We could not save your profile changes.",
      ),
    ).toBeInTheDocument();

    expect(
      screen.queryByText(
        "Internal database traceback.",
      ),
    ).not.toBeInTheDocument();
  });

  it("changes password successfully", async () => {
    const user = userEvent.setup();

    mockJsonResponse({
      detail:
        "Password has been successfully changed.",
    });

    renderPage();

    await screen.findByText(
      "Major Sarah Chen",
    );

    await user.type(
      screen.getByPlaceholderText(
        "Enter current password",
      ),
      "OldPassword123!",
    );
    await user.type(
      screen.getByPlaceholderText(
        "Enter new password",
      ),
      "NewPassword123!",
    );
    await user.type(
      screen.getByPlaceholderText(
        "Confirm new password",
      ),
      "NewPassword123!",
    );

    await user.click(
      screen.getByRole("button", {
        name: "Update Password",
      }),
    );

    expect(
      await screen.findByText(
        "Password has been successfully changed.",
      ),
    ).toBeInTheDocument();

    const fetchMock = vi.mocked(
      globalThis.fetch,
    );
    expect(
      fetchMock.mock.calls[0]?.[0],
    ).toBe(
      "/api/accounts/users/me/change-password/",
    );

    await user.click(
      screen.getByRole("button", {
        name: "Dismiss message",
      }),
    );

    expect(
      screen.queryByText(
        "Password has been successfully changed.",
      ),
    ).not.toBeInTheDocument();
    expect(fetchMock.mock.calls).toHaveLength(1);
  });

  it("uploads a selected avatar without a delayed state race", async () => {
    const user = userEvent.setup();
    const avatar = new File(
      ["avatar"],
      "avatar.png",
      { type: "image/png" },
    );

    mockJsonResponse({
      ...currentUserResponse,
      profile_picture:
        "/api/accounts/users/47/profile-picture/",
    });

    renderPage();

    await screen.findByText(
      "Major Sarah Chen",
    );
    await user.upload(
      screen.getByLabelText(
        "Choose profile avatar",
      ),
      avatar,
    );

    expect(
      screen.getByText("Ready to save"),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", {
        name: "Save all changes",
      }),
    );

    expect(
      await screen.findByText(
        "Profile changes saved successfully.",
      ),
    ).toBeInTheDocument();

    const requestBody = vi.mocked(
      globalThis.fetch,
    ).mock.calls[0]?.[1]?.body;
    expect(requestBody).toBeInstanceOf(FormData);
    expect(
      (requestBody as FormData).get(
        "profile_picture",
      ),
    ).toBe(avatar);
    expect(
      screen.queryByText("Ready to save"),
    ).not.toBeInTheDocument();
  });

  it("keeps pending avatar actions visible after drag leave", async () => {
    const user = userEvent.setup();
    const avatar = new File(
      ["avatar"],
      "avatar.png",
      { type: "image/png" },
    );

    renderPage();

    await screen.findByText(
      "Major Sarah Chen",
    );
    await user.upload(
      screen.getByLabelText(
        "Choose profile avatar",
      ),
      avatar,
    );

    const dropZone = screen.getByRole(
      "button",
      {
        name: "Upload profile avatar",
      },
    );
    fireEvent.dragOver(dropZone);
    fireEvent.dragLeave(dropZone);

    expect(
      screen.getByText("Ready to save"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: "Save all changes",
      }),
    ).toBeEnabled();
  });

  it("clears a pending avatar when the next selected file is invalid", async () => {
    const user = userEvent.setup();
    const validAvatar = new File(
      ["avatar"],
      "avatar.png",
      { type: "image/png" },
    );
    const invalidAvatar = new File(
      ["invalid"],
      "avatar.gif",
      { type: "image/gif" },
    );

    renderPage();

    await screen.findByText(
      "Major Sarah Chen",
    );
    const fileInput = screen.getByLabelText(
      "Choose profile avatar",
    );
    await user.upload(fileInput, validAvatar);
    fireEvent.change(fileInput, {
      target: {
        files: [invalidAvatar],
      },
    });

    expect(
      screen.getByText(
        "Invalid file type. Accepted: JPG, PNG, WEBP.",
      ),
    ).toBeInTheDocument();

    expect(
      screen.queryByRole("button", {
        name: "Save all changes",
      }),
    ).not.toBeInTheDocument();
    expect(
      vi.mocked(globalThis.fetch).mock.calls,
    ).toHaveLength(0);
  });

  it("cancels a pending avatar directly from the avatar card", async () => {
    const user = userEvent.setup();
    const avatar = new File(
      ["avatar"],
      "avatar.png",
      { type: "image/png" },
    );

    renderPage();

    await screen.findByText(
      "Major Sarah Chen",
    );
    await user.upload(
      screen.getByLabelText(
        "Choose profile avatar",
      ),
      avatar,
    );
    await user.click(
      screen.getByRole("button", {
        name: "Cancel avatar change",
      }),
    );

    expect(
      screen.queryByText("Ready to save"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: "Save all changes",
      }),
    ).not.toBeInTheDocument();
    expect(
      vi.mocked(globalThis.fetch).mock.calls,
    ).toHaveLength(0);
  });

  it(
    "falls back to initials when protected avatar images fail to load",
    async () => {
      renderPage({
        ...currentUserResponse,
        profile_picture:
          "/api/accounts/users/47/profile-picture/",
      });

      await screen.findByText(
        "Major Sarah Chen",
      );

      const avatarImages =
        screen.getAllByRole("img");

      expect(avatarImages).toHaveLength(3);

      avatarImages.forEach((image) => {
        fireEvent.error(image);
      });

      await waitFor(() => {
        expect(
          screen.queryAllByRole("img"),
        ).toHaveLength(0);
      });

      expect(
        screen.getAllByText("SC").length,
      ).toBeGreaterThan(0);
    },
  );

  it("clears a stale avatar API error after selecting another file", async () => {
    const user = userEvent.setup();
    const firstAvatar = new File(
      ["first"],
      "first.png",
      { type: "image/png" },
    );
    const replacementAvatar = new File(
      ["replacement"],
      "replacement.png",
      { type: "image/png" },
    );

    mockJsonResponse(
      {
        profile_picture: [
          "The selected image could not be processed.",
        ],
      },
      400,
    );

    renderPage();

    await screen.findByText(
      "Major Sarah Chen",
    );
    const fileInput = screen.getByLabelText(
      "Choose profile avatar",
    );
    await user.upload(fileInput, firstAvatar);
    await user.click(
      screen.getByRole("button", {
        name: "Save all changes",
      }),
    );

    expect(
      await screen.findByText(
        "The selected image could not be processed.",
      ),
    ).toBeInTheDocument();

    await user.upload(
      fileInput,
      replacementAvatar,
    );

    expect(
      screen.queryByText(
        "The selected image could not be processed.",
      ),
    ).not.toBeInTheDocument();
  });

  it("shows incorrect current password error", async () => {
    const user = userEvent.setup();

    mockJsonResponse(
      {
        old_password: [
          "Incorrect old password.",
        ],
      },
      400,
    );

    renderPage();

    await screen.findByText(
      "Major Sarah Chen",
    );

    await user.type(
      screen.getByPlaceholderText(
        "Enter current password",
      ),
      "WrongPassword!",
    );
    await user.type(
      screen.getByPlaceholderText(
        "Enter new password",
      ),
      "NewPassword123!",
    );
    await user.type(
      screen.getByPlaceholderText(
        "Confirm new password",
      ),
      "NewPassword123!",
    );

    await user.click(
      screen.getByRole("button", {
        name: "Update Password",
      }),
    );

    expect(
      await screen.findAllByText(
        "Incorrect old password.",
      ),
    ).toHaveLength(1);

    await waitFor(() => {
      expect(
        vi.mocked(globalThis.fetch)
          .mock.calls.length,
      ).toBe(1);
    });
  });

  it("removes a saved avatar through a JSON PATCH", async () => {
    const user = userEvent.setup();

    mockJsonResponse({
      ...currentUserResponse,
      profile_picture: null,
    });

    renderPage({
      ...currentUserResponse,
      profile_picture:
        "/api/accounts/users/47/profile-picture/",
    });

    await screen.findByText(
      "Major Sarah Chen",
    );
    await user.click(
      screen.getByRole("button", {
        name: "Remove selected avatar",
      }),
    );
    await user.click(
      screen.getByRole("button", {
        name: "Save all changes",
      }),
    );

    expect(
      await screen.findByText(
        "Profile changes saved successfully.",
      ),
    ).toBeInTheDocument();

    const requestOptions = vi.mocked(
      globalThis.fetch,
    ).mock.calls[0]?.[1];
    expect(requestOptions?.method).toBe("PATCH");
    expect(
      new Headers(
        requestOptions?.headers,
      ).get("Content-Type"),
    ).toBe("application/json");
    expect(
      JSON.parse(requestOptions?.body as string)
        .profile_picture,
    ).toBeNull();
  });

  it("redirects to login when profile saving loses the session", async () => {
    const user = userEvent.setup();
    mockJsonResponse(
      {
        detail:
          "Authentication credentials were not provided.",
      },
      403,
    );

    renderPage();

    await screen.findByText(
      "Major Sarah Chen",
    );
    await user.click(
      screen.getByRole("button", {
        name: "Edit Profile",
      }),
    );
    await user.click(
      screen.getByRole("button", {
        name: "Save Changes",
      }),
    );

    expect(
      await screen.findByText("Login page"),
    ).toBeInTheDocument();
  });

  it("redirects to required password change when the backend enforces it", async () => {
    const user = userEvent.setup();
    mockJsonResponse(
      {
        detail:
          "Password change is required before accessing this resource.",
        code: "password_change_required",
      },
      403,
    );

    renderPage();

    await screen.findByText(
      "Major Sarah Chen",
    );
    await user.click(
      screen.getByRole("button", {
        name: "Edit Profile",
      }),
    );
    await user.click(
      screen.getByRole("button", {
        name: "Save Changes",
      }),
    );

    expect(
      await screen.findByText(
        "Password change required",
      ),
    ).toBeInTheDocument();
  });

  it("redirects to login when password change loses the session", async () => {
    const user = userEvent.setup();
    mockJsonResponse(
      {
        detail:
          "Authentication credentials were not provided.",
      },
      403,
    );

    renderPage();

    await screen.findByText(
      "Major Sarah Chen",
    );
    await user.type(
      screen.getByLabelText("Current Password"),
      "OldPassword123!",
    );
    await user.type(
      screen.getByLabelText("New Password"),
      "NewPassword123!",
    );
    await user.type(
      screen.getByLabelText(
        "Confirm New Password",
      ),
      "NewPassword123!",
    );
    await user.click(
      screen.getByRole("button", {
        name: "Update Password",
      }),
    );

    expect(
      await screen.findByText("Login page"),
    ).toBeInTheDocument();
  });

  it("signs out from the account menu", async () => {
    const user = userEvent.setup();
    mockJsonResponse({
      detail: "Signed out successfully.",
    });

    renderPage();

    await screen.findByText(
      "Major Sarah Chen",
    );
    await user.click(
      screen.getByRole("button", {
        name: "Open account menu",
      }),
    );
    await user.click(
      screen.getByRole("button", {
        name: "Sign Out",
      }),
    );

    expect(
      await screen.findByText("Login page"),
    ).toBeInTheDocument();
    expect(
      vi.mocked(globalThis.fetch)
        .mock.calls[0]?.[0],
    ).toBe("/api/accounts/logout/");
    expect(
      vi.mocked(globalThis.fetch)
        .mock.calls[0]?.[1]?.method,
    ).toBe("POST");
  });

  it("opens profile sections from the workspace navigation", async () => {
    const user = userEvent.setup();

    renderPage();

    await screen.findByText(
      "Major Sarah Chen",
    );
    await user.click(
      screen.getByRole("button", {
        name: "Open profile settings from navigation",
      }),
    );

    expect(
      screen.getByRole("button", {
        name: "Account & Security",
      }),
    ).toHaveAttribute("aria-current", "page");

    await user.click(
      screen.getByRole("button", {
        name: "Open my profile from sidebar",
      }),
    );

    expect(
      screen.getByRole("button", {
        name: "Profile Details",
      }),
    ).toHaveAttribute("aria-current", "page");

    await user.click(
      screen.getByRole("button", {
        name: "Open account menu",
      }),
    );
    await user.click(
      screen.getByRole("button", {
        name: "Open my profile",
      }),
    );

    expect(
      screen.getByRole("button", {
        name: "Profile Details",
      }),
    ).toHaveAttribute("aria-current", "page");
    expect(
      screen.queryByRole("button", {
        name: "Open my profile",
      }),
    ).not.toBeInTheDocument();

    await user.click(
      screen.getByRole("button", {
        name: "Open account menu",
      }),
    );
    await user.click(
      screen.getByRole("button", {
        name: "Open profile settings",
      }),
    );

    expect(
      screen.getByRole("button", {
        name: "Account & Security",
      }),
    ).toHaveAttribute("aria-current", "page");
  });

  it("redirects unauthenticated users to login from the protected route", async () => {
    renderProtectedPage();

    expect(
      await screen.findByText("Login page"),
    ).toBeInTheDocument();

    expect(
      globalThis.fetch,
    ).not.toHaveBeenCalled();
  });

  it("shows an access error for a genuine authorization failure", async () => {
    const user = userEvent.setup();

    mockJsonResponse(
      {
        detail:
          "You do not have permission to update this profile.",
      },
      403,
    );

    renderPage();

    await screen.findByText(
      "Major Sarah Chen",
    );

    await user.click(
      screen.getByRole("button", {
        name: "Edit Profile",
      }),
    );

    await user.click(
      screen.getByRole("button", {
        name: "Save Changes",
      }),
    );

    expect(
      await screen.findByText(
        "You do not have permission to perform this action.",
      ),
    ).toBeInTheDocument();

    expect(
      screen.queryByText("Login page"),
    ).not.toBeInTheDocument();
  });

  it("shows a safe CSRF failure message", async () => {
    const user = userEvent.setup();

    // Initial profile update fails because the CSRF token is stale.
    mockJsonResponse(
      {
        detail:
          "CSRF verification failed. Request aborted.",
      },
      403,
    );

    // API client refreshes the CSRF cookie.
    mockJsonResponse({
      detail: "CSRF cookie set.",
    });

    // The single retried profile update also fails.
    mockJsonResponse(
      {
        detail:
          "CSRF verification failed. Request aborted.",
      },
      403,
    );

    renderPage();

    await screen.findByText(
      "Major Sarah Chen",
    );

    await user.click(
      screen.getByRole("button", {
        name: "Edit Profile",
      }),
    );

    await user.click(
      screen.getByRole("button", {
        name: "Save Changes",
      }),
    );

    expect(
      await screen.findByText(
        "Your security session could not be verified. " +
          "Refresh the page and try again.",
      ),
    ).toBeInTheDocument();
  });

  it("shows a retry-later message for rate limiting", async () => {
    const user = userEvent.setup();

    mockJsonResponse(
      {
        detail:
          "Request was throttled.",
      },
      429,
    );

    renderPage();

    await screen.findByText(
      "Major Sarah Chen",
    );

    await user.click(
      screen.getByRole("button", {
        name: "Edit Profile",
      }),
    );

    await user.click(
      screen.getByRole("button", {
        name: "Save Changes",
      }),
    );

    expect(
      await screen.findByText(
        "Too many requests. " +
          "Please wait a moment and try again.",
      ),
    ).toBeInTheDocument();
  });

  it("shows a safe network error", async () => {
    const user = userEvent.setup();

    vi.mocked(
      globalThis.fetch,
    ).mockRejectedValueOnce(
      new TypeError("Network failure"),
    );

    renderPage();

    await screen.findByText(
      "Major Sarah Chen",
    );

    await user.click(
      screen.getByRole("button", {
        name: "Edit Profile",
      }),
    );

    await user.click(
      screen.getByRole("button", {
        name: "Save Changes",
      }),
    );

    expect(
      await screen.findByText(
        "Unable to reach Mission Control. " +
          "Check your connection and try again.",
      ),
    ).toBeInTheDocument();
  });
});

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});
