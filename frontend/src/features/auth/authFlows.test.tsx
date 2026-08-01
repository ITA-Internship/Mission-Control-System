import type {
  ComponentType,
} from "react";

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

import {
  PasswordInput,
} from "./components/PasswordInput";

import {
  SubmitButton,
} from "./components/SubmitButton";

import {
  ActivateAccountPage,
} from "./pages/ActivateAccountPage";

import {
  ForgotPasswordPage,
} from "./pages/ForgotPasswordPage";

import {
  LoginPage,
} from "./pages/LoginPage";

import {
  RequiredPasswordChangePage,
} from "./pages/RequiredPasswordChangePage";

import {
  RequireSessionAuth,
} from "./components/RequireSessionAuth";

import {
  ResetPasswordPage,
} from "./pages/ResetPasswordPage";

function renderRoute(
  path: string,
  routePath: string,
  Component: ComponentType,
) {
  const router = createMemoryRouter(
    [
      {
        path: routePath,
        Component,
      },
    ],
    {
      initialEntries: [
        path,
      ],
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
  const fetchMock = vi.mocked(
    globalThis.fetch,
  );

  fetchMock.mockResolvedValueOnce(
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

describe("shared auth controls", () => {
  it("shows and hides a password", async () => {
    const user = userEvent.setup();

    render(
      <PasswordInput
        id="password"
        name="password"
        label="Password"
        defaultValue="Secret123!"
      />,
    );

    const input =
      screen.getByLabelText("Password");

    expect(input).toHaveAttribute(
      "type",
      "password",
    );

    await user.click(
      screen.getByRole(
        "button",
        {
          name: "Show password",
        },
      ),
    );

    expect(input).toHaveAttribute(
      "type",
      "text",
    );

    expect(
      screen.getByRole(
        "button",
        {
          name: "Hide password",
        },
      ),
    ).toBeInTheDocument();
  });

  it("disables a loading submit button", () => {
    render(
      <SubmitButton
        isLoading
        loadingLabel="Submitting"
      >
        Submit
      </SubmitButton>,
    );

    const button =
      screen.getByRole(
        "button",
        {
          name: "Submitting",
        },
      );

    expect(button).toBeDisabled();
    expect(button).toHaveAttribute(
      "aria-busy",
      "true",
    );
  });
});

describe("forgot password", () => {
  it("shows a generic success message", async () => {
    const user = userEvent.setup();

    mockJsonResponse({
      detail:
        "If an account with this email exists, a password reset link has been sent.",
    });

    renderRoute(
      "/forgot-password",
      "/forgot-password",
      ForgotPasswordPage,
    );

    await user.type(
      screen.getByLabelText("Email"),
      "user@example.com",
    );

    await user.click(
      screen.getByRole(
        "button",
        {
          name: "Send reset link",
        },
      ),
    );

    expect(
      await screen.findByText(
        /If an account exists for this email address/i,
      ),
    ).toBeInTheDocument();

    const fetchMock = vi.mocked(
      globalThis.fetch,
    );

    const [
      requestUrl,
      requestOptions,
    ] = fetchMock.mock.calls[0];

    expect(requestUrl).toBe(
      "/api/accounts/users/password-reset/",
    );

    expect(
      JSON.parse(
        requestOptions?.body as string,
      ),
    ).toEqual({
      email: "user@example.com",
    });
  });

  it("shows a network error", async () => {
    const user = userEvent.setup();

    vi.mocked(
      globalThis.fetch,
    ).mockRejectedValueOnce(
      new TypeError("Network error"),
    );

    renderRoute(
      "/forgot-password",
      "/forgot-password",
      ForgotPasswordPage,
    );

    await user.type(
      screen.getByLabelText("Email"),
      "user@example.com",
    );

    await user.click(
      screen.getByRole(
        "button",
        {
          name: "Send reset link",
        },
      ),
    );

    expect(
      await screen.findByText(
        /Unable to reach Mission Control/i,
      ),
    ).toBeInTheDocument();
  });
});

describe("login", () => {
  it("signs in and redirects to my profile", async () => {
    const user = userEvent.setup();

    mockJsonResponse({
      detail: "CSRF cookie set.",
    });
    mockJsonResponse({
      id: 47,
      username: "root.admin",
      email: "root.admin@example.com",
      first_name: "Root",
      last_name: "Admin",
      rank: null,
      contact: null,
      profile_picture: null,
      role: 1,
      unit: null,
      is_active: true,
      must_change_password: false,
    });

    const router = createMemoryRouter(
      [
        {
          path: "/login",
          Component: LoginPage,
        },
        {
          path: "/my-profile",
          element: <div>My Profile</div>,
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
        initialEntries: ["/login"],
      },
    );

    render(
      <RouterProvider router={router} />,
    );

    await user.type(
      screen.getByLabelText("Email or Username"),
      "root.admin@example.com",
    );

    await user.type(
      screen.getByLabelText("Password"),
      "Test@1234",
    );

    await user.click(
      screen.getByRole(
        "button",
        {
          name: "Sign in",
        },
      ),
    );

    expect(
      await screen.findByText("My Profile"),
    ).toBeInTheDocument();

    const fetchMock = vi.mocked(
      globalThis.fetch,
    );

    const [
      firstRequestUrl,
    ] = fetchMock.mock.calls[0];
    const [
      secondRequestUrl,
      secondRequestOptions,
    ] = fetchMock.mock.calls[1];

    expect(firstRequestUrl).toBe(
      "/api/accounts/login/",
    );

    expect(secondRequestUrl).toBe(
      "/api/accounts/login/",
    );

    expect(
      JSON.parse(
        secondRequestOptions?.body as string,
      ),
    ).toEqual({
      identifier:
        "root.admin@example.com",
      password: "Test@1234",
    });
  });
});

describe("required password change", () => {
  function renderRequiredPasswordRoute() {
    const router = createMemoryRouter(
      [
        {
          path: "/change-password/required",
          element: (
            <RequireSessionAuth
              requirePasswordChange
            >
              {() => (
                <RequiredPasswordChangePage />
              )}
            </RequireSessionAuth>
          ),
        },
        {
          path: "/login",
          element: <div>Login page</div>,
        },
        {
          path: "/my-profile",
          element: <div>My Profile page</div>,
        },
      ],
      {
        initialEntries: [
          "/change-password/required",
        ],
      },
    );

    return render(
      <RouterProvider router={router} />,
    );
  }

  const requiredUser = {
    id: 47,
    username: "root.admin",
    email: "root.admin@example.com",
    first_name: "Root",
    last_name: "Admin",
    rank: null,
    contact: null,
    profile_picture: null,
    role: 1,
    unit: null,
    is_active: true,
    must_change_password: true,
  };

  it("redirects users without a session to login", async () => {
    mockJsonResponse(
      {
        detail:
          "Authentication credentials were not provided.",
      },
      401,
    );

    renderRequiredPasswordRoute();

    expect(
      await screen.findByText("Login page"),
    ).toBeInTheDocument();
  });

  it("redirects users who do not require a password change", async () => {
    mockJsonResponse({
      ...requiredUser,
      must_change_password: false,
    });

    renderRequiredPasswordRoute();

    expect(
      await screen.findByText(
        "My Profile page",
      ),
    ).toBeInTheDocument();
  });

  it("changes the required password and continues", async () => {
    const user = userEvent.setup();
    mockJsonResponse(requiredUser);
    mockJsonResponse({
      detail:
        "Password has been successfully changed.",
    });

    renderRequiredPasswordRoute();

    await user.type(
      await screen.findByLabelText(
        "Current password",
      ),
      "OldPassword123!",
    );
    await user.type(
      screen.getByLabelText("New password"),
      "NewPassword123!",
    );
    await user.type(
      screen.getByLabelText(
        "Confirm new password",
      ),
      "NewPassword123!",
    );
    await user.click(
      screen.getByRole("button", {
        name: "Save and continue",
      }),
    );

    expect(
      await screen.findByText(
        "My Profile page",
      ),
    ).toBeInTheDocument();
  });

  it("redirects to login when the session expires during submission", async () => {
    const user = userEvent.setup();
    mockJsonResponse(requiredUser);
    mockJsonResponse(
      { detail: "Session expired." },
      401,
    );

    renderRequiredPasswordRoute();

    await user.type(
      await screen.findByLabelText(
        "Current password",
      ),
      "OldPassword123!",
    );
    await user.type(
      screen.getByLabelText("New password"),
      "NewPassword123!",
    );
    await user.type(
      screen.getByLabelText(
        "Confirm new password",
      ),
      "NewPassword123!",
    );
    await user.click(
      screen.getByRole("button", {
        name: "Save and continue",
      }),
    );

    expect(
      await screen.findByText("Login page"),
    ).toBeInTheDocument();
  });
});

describe("reset password", () => {
  it("rejects mismatching passwords", async () => {
    const user = userEvent.setup();

    renderRoute(
      "/reset-password/demo-uid/demo-token",
      "/reset-password/:uid/:token",
      ResetPasswordPage,
    );

    await user.type(
      screen.getByLabelText(
        "New password",
      ),
      "StrongPassword123!",
    );

    await user.type(
      screen.getByLabelText(
        "Confirm new password",
      ),
      "DifferentPassword123!",
    );

    await user.click(
      screen.getByRole(
        "button",
        {
          name: "Update password",
        },
      ),
    );

    expect(
      screen.getByText(
        "Passwords do not match.",
      ),
    ).toBeInTheDocument();

    expect(
      globalThis.fetch,
    ).not.toHaveBeenCalled();
  });

  it("submits only new_password", async () => {
    const user = userEvent.setup();

    mockJsonResponse({
      detail:
        "Password has been reset successfully.",
    });

    renderRoute(
      "/reset-password/demo-uid/demo-token",
      "/reset-password/:uid/:token",
      ResetPasswordPage,
    );

    await user.type(
      screen.getByLabelText(
        "New password",
      ),
      "StrongPassword123!",
    );

    await user.type(
      screen.getByLabelText(
        "Confirm new password",
      ),
      "StrongPassword123!",
    );

    await user.click(
      screen.getByRole(
        "button",
        {
          name: "Update password",
        },
      ),
    );

    expect(
      await screen.findByText(
        "Password updated",
      ),
    ).toBeInTheDocument();

    const fetchMock = vi.mocked(
      globalThis.fetch,
    );

    const [
      ,
      requestOptions,
    ] = fetchMock.mock.calls[0];

    expect(
      JSON.parse(
        requestOptions?.body as string,
      ),
    ).toEqual({
      new_password:
        "StrongPassword123!",
    });
  });

  it("shows invalid state without route parameters", () => {
    renderRoute(
      "/reset-password",
      "/reset-password/*",
      ResetPasswordPage,
    );

    expect(
      screen.getByText(
        "Invalid or expired link",
      ),
    ).toBeInTheDocument();
  });
});

describe("account activation", () => {
  it("activates an account", async () => {
    const user = userEvent.setup();

    mockJsonResponse({
      detail:
        "Your account has been activated. You can now log in.",
    });

    renderRoute(
      "/activate/15/demo-token",
      "/activate/:userId/:token",
      ActivateAccountPage,
    );

    await user.type(
      screen.getByLabelText(
        "New password",
      ),
      "StrongPassword123!",
    );

    await user.type(
      screen.getByLabelText(
        "Confirm new password",
      ),
      "StrongPassword123!",
    );

    await user.click(
      screen.getByRole(
        "button",
        {
          name: "Activate account",
        },
      ),
    );

    expect(
      await screen.findByText(
        "Your account is active",
      ),
    ).toBeInTheDocument();

    const fetchMock = vi.mocked(
      globalThis.fetch,
    );

    const [
      ,
      requestOptions,
    ] = fetchMock.mock.calls[0];

    expect(
      JSON.parse(
        requestOptions?.body as string,
      ),
    ).toEqual({
      password:
        "StrongPassword123!",
    });
  });

  it("shows invalid activation-link state", async () => {
    const user = userEvent.setup();

    mockJsonResponse(
      {
        detail:
          "Invalid or expired activation link.",
      },
      400,
    );

    renderRoute(
      "/activate/15/invalid-token",
      "/activate/:userId/:token",
      ActivateAccountPage,
    );

    await user.type(
      screen.getByLabelText(
        "New password",
      ),
      "StrongPassword123!",
    );

    await user.type(
      screen.getByLabelText(
        "Confirm new password",
      ),
      "StrongPassword123!",
    );

    await user.click(
      screen.getByRole(
        "button",
        {
          name: "Activate account",
        },
      ),
    );

    expect(
      await screen.findByText(
        "Invalid or expired link",
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
