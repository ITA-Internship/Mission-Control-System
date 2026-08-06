import {
  render,
  screen,
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

import { AppShell } from "./AppShell";
import type { CurrentUser } from "../types/accounts";

const currentUser: CurrentUser = {
  id: 47,
  username: "commander.chen",
  email: "s.chen@mil-ops.gov",
  first_name: "Sarah",
  last_name: "Chen",
  rank: "Major",
  contact: "+1 (703) 555-0192",
  profile_picture: null,
  role: 2,
  role_code: "COMMANDER",
  role_name: "Commander",
  unit: 3,
  unit_name: "3rd UAS Battalion",
  unit_code: "UAS-3",
  is_active: true,
  must_change_password: false,
};

function renderShell(
  initialPath = "/dashboard",
) {
  const router = createMemoryRouter(
    [
      {
        element: (
          <AppShell user={currentUser} />
        ),
        children: [
          {
            path: "/dashboard",
            element: <div>Dashboard page</div>,
          },
          {
            path: "/my-profile",
            element: <div>Profile page</div>,
          },
        ],
      },
      {
        path: "/login",
        element: <div>Login page</div>,
      },
    ],
    {
      initialEntries: [initialPath],
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

describe("AppShell account menu", () => {
  it("reaches the profile page from the dashboard", async () => {
    const user = userEvent.setup();

    renderShell();

    expect(
      screen.getByText("Dashboard page"),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", {
        name: "Open account menu",
      }),
    );
    await user.click(
      screen.getByRole("menuitem", {
        name: "My profile",
      }),
    );

    expect(
      await screen.findByText(
        "Profile page",
      ),
    ).toBeInTheDocument();
  });

  it("titles the shell for the profile route", () => {
    renderShell("/my-profile");

    expect(
      screen.getByRole("heading", {
        name: "My Profile",
      }),
    ).toBeInTheDocument();
  });

  /* Regression: sign out must end the Django session, not just redirect. */
  it("posts to the logout endpoint before returning to sign in", async () => {
    const user = userEvent.setup();
    mockJsonResponse({
      detail: "Signed out successfully.",
    });

    renderShell();

    await user.click(
      screen.getByRole("button", {
        name: "Open account menu",
      }),
    );
    await user.click(
      screen.getByRole("menuitem", {
        name: "Sign out",
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

  it("still returns to sign in when logout fails", async () => {
    const user = userEvent.setup();
    mockJsonResponse(
      { detail: "Server error." },
      500,
    );

    renderShell();

    await user.click(
      screen.getByRole("button", {
        name: "Open account menu",
      }),
    );
    await user.click(
      screen.getByRole("menuitem", {
        name: "Sign out",
      }),
    );

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
