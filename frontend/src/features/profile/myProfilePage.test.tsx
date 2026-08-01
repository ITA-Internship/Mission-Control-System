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

function renderPage() {
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
    <RouterProvider router={router} />,
  );
}

function renderProtectedPage() {
  const router = createMemoryRouter(
    [
      {
        path: "/my-profile",
        element: (
          <RequireSessionAuth>
            {(currentUser) => (
              <MyProfilePage
                initialUser={currentUser}
              />
            )}
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
    <RouterProvider router={router} />,
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

describe("MyProfilePage", () => {
  it("loads and updates profile details", async () => {
    const user = userEvent.setup();

    mockJsonResponse(currentUserResponse);
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
      fetchMock.mock.calls[1]?.[0],
    ).toBe("/api/accounts/users/me/");
    expect(
      fetchMock.mock.calls[1]?.[1]
        ?.method,
    ).toBe("PATCH");
    expect(
      fetchMock.mock.calls[1]?.[1]?.body,
    ).toBeInstanceOf(FormData);
    expect(
      new Headers(
        fetchMock.mock.calls[1]?.[1]?.headers,
      ).get("Content-Type"),
    ).toBeNull();
    expect(
      screen.queryByText("Ready to save"),
    ).not.toBeInTheDocument();
  });

  it("shows profile validation errors", async () => {
    const user = userEvent.setup();

    mockJsonResponse(currentUserResponse);
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

    mockJsonResponse(currentUserResponse);
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
  });

  it("changes password successfully", async () => {
    const user = userEvent.setup();

    mockJsonResponse(currentUserResponse);
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
      fetchMock.mock.calls[1]?.[0],
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
    expect(fetchMock.mock.calls).toHaveLength(2);
  });

  it("uploads a selected avatar without a delayed state race", async () => {
    const user = userEvent.setup();
    const avatar = new File(
      ["avatar"],
      "avatar.png",
      { type: "image/png" },
    );

    mockJsonResponse(currentUserResponse);
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
        name: "Save Changes",
      }),
    );

    expect(
      await screen.findByText(
        "Profile changes saved successfully.",
      ),
    ).toBeInTheDocument();

    const requestBody = vi.mocked(
      globalThis.fetch,
    ).mock.calls[1]?.[1]?.body;
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

    mockJsonResponse(currentUserResponse);
    mockJsonResponse(currentUserResponse);

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

    await user.click(
      screen.getByRole("button", {
        name: "Save Changes",
      }),
    );

    await screen.findByText(
      "Profile changes saved successfully.",
    );
    const requestBody = vi.mocked(
      globalThis.fetch,
    ).mock.calls[1]?.[1]?.body;
    expect(requestBody).toBeInstanceOf(FormData);
    expect(
      (requestBody as FormData).get(
        "profile_picture",
      ),
    ).toBeNull();
  });

  it("shows incorrect current password error", async () => {
    const user = userEvent.setup();

    mockJsonResponse(currentUserResponse);
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
    ).not.toHaveLength(0);

    await waitFor(() => {
      expect(
        vi.mocked(globalThis.fetch)
          .mock.calls.length,
      ).toBe(2);
    });
  });

  it("removes a saved avatar through a JSON PATCH", async () => {
    const user = userEvent.setup();
    mockJsonResponse({
      ...currentUserResponse,
      profile_picture:
        "/api/accounts/users/47/profile-picture/",
    });
    mockJsonResponse({
      ...currentUserResponse,
      profile_picture: null,
    });

    renderPage();

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
        name: "Save Changes",
      }),
    );

    expect(
      await screen.findByText(
        "Profile changes saved successfully.",
      ),
    ).toBeInTheDocument();

    const requestOptions = vi.mocked(
      globalThis.fetch,
    ).mock.calls[1]?.[1];
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
    mockJsonResponse(currentUserResponse);
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

  it("redirects to login when password change loses the session", async () => {
    const user = userEvent.setup();
    mockJsonResponse(currentUserResponse);
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

  it("redirects unauthenticated users to login from the protected route", async () => {
    mockJsonResponse(
      {
        detail: "Authentication credentials were not provided.",
      },
      403,
    );

    renderProtectedPage();

    expect(
      await screen.findByText("Login page"),
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
