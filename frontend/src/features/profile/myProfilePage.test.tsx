import {
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
