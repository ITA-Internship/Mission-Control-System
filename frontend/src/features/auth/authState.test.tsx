import {
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import type {
  CurrentUser,
} from "../../shared/types/accounts";
import {
  AuthProvider,
} from "./context/AuthProvider";
import {
  useAuth,
} from "./hooks/useAuth";

const authenticatedUser: CurrentUser = {
  id: 47,
  username: "root.admin",
  email: "root.admin@example.com",
  first_name: "Root",
  last_name: "Admin",
  rank: null,
  contact: null,
  profile_picture: null,
  role: 1,
  role_name: "Administrator",
  role_code: "ADMIN",
  unit: null,
  is_active: true,
  must_change_password: false,
};

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

function AuthStateProbe({
  name,
}: {
  name: string;
}) {
  const {
    status,
    currentUser,
    error,
    refreshCurrentUser,
    setAuthenticatedUser,
    clearAuthentication,
    logout,
  } = useAuth();

  return (
    <div>
      <div data-testid={`${name}-status`}>
        {status}
      </div>

      <div data-testid={`${name}-username`}>
        {currentUser?.username ?? "none"}
      </div>

      <div data-testid={`${name}-error`}>
        {error ?? "none"}
      </div>

      <button
        type="button"
        onClick={() => {
          setAuthenticatedUser({
            ...authenticatedUser,
            username: "updated.admin",
          });
        }}
      >
        {name} set user
      </button>

      <button
        type="button"
        onClick={clearAuthentication}
      >
        {name} clear authentication
      </button>

      <button
        type="button"
        onClick={() => {
          void refreshCurrentUser().catch(
            () => undefined,
          );
        }}
      >
        {name} refresh user
      </button>

      <button
        type="button"
        onClick={() => {
          void logout().catch(
            () => undefined,
          );
        }}
      >
        {name} logout
      </button>
    </div>
  );
}

describe("AuthProvider", () => {
  it("restores and shares the authenticated session", async () => {
    mockJsonResponse(authenticatedUser);

    const fetchMock = vi.mocked(
      globalThis.fetch,
    );

    render(
      <AuthProvider>
        <AuthStateProbe name="first" />
        <AuthStateProbe name="second" />
      </AuthProvider>,
    );

    expect(
      await screen.findByTestId(
        "first-username",
      ),
    ).toHaveTextContent("root.admin");

    expect(
      screen.getByTestId(
        "second-username",
      ),
    ).toHaveTextContent("root.admin");

    expect(
      screen.getByTestId("first-status"),
    ).toHaveTextContent("authenticated");

    expect(
      screen.getByTestId("second-status"),
    ).toHaveTextContent("authenticated");

    expect(fetchMock).toHaveBeenCalledTimes(1);

    expect(
      fetchMock.mock.calls[0]?.[0],
    ).toBe("/api/accounts/users/me/");
  });

  it("represents a missing session as unauthenticated", async () => {
    mockJsonResponse(
      {
        detail:
          "Authentication credentials were not provided.",
      },
      401,
    );

    render(
      <AuthProvider>
        <AuthStateProbe name="probe" />
      </AuthProvider>,
    );

    expect(
      await screen.findByTestId(
        "probe-status",
      ),
    ).toHaveTextContent("unauthenticated");

    expect(
      screen.getByTestId(
        "probe-username",
      ),
    ).toHaveTextContent("none");

    expect(
      screen.getByTestId("probe-error"),
    ).toHaveTextContent("none");
  });

  it("updates and clears the shared authentication state", async () => {
    const user = userEvent.setup();

    mockJsonResponse(
      {
        detail:
          "Authentication credentials were not provided.",
      },
      401,
    );

    render(
      <AuthProvider>
        <AuthStateProbe name="first" />
        <AuthStateProbe name="second" />
      </AuthProvider>,
    );

    expect(
      await screen.findByTestId(
        "first-status",
      ),
    ).toHaveTextContent("unauthenticated");

    await user.click(
      screen.getByRole("button", {
        name: "first set user",
      }),
    );

    expect(
      screen.getByTestId(
        "first-username",
      ),
    ).toHaveTextContent("updated.admin");

    expect(
      screen.getByTestId(
        "second-username",
      ),
    ).toHaveTextContent("updated.admin");

    expect(
      screen.getByTestId("first-status"),
    ).toHaveTextContent("authenticated");

    await user.click(
      screen.getByRole("button", {
        name: "second clear authentication",
      }),
    );

    expect(
      screen.getByTestId(
        "first-username",
      ),
    ).toHaveTextContent("none");

    expect(
      screen.getByTestId(
        "second-username",
      ),
    ).toHaveTextContent("none");

    expect(
      screen.getByTestId("first-status"),
    ).toHaveTextContent("unauthenticated");
  });

  it("refreshes the current user", async () => {
    const user = userEvent.setup();

    mockJsonResponse(authenticatedUser);

    mockJsonResponse({
      ...authenticatedUser,
      username: "refreshed.admin",
    });

    render(
      <AuthProvider>
        <AuthStateProbe name="probe" />
      </AuthProvider>,
    );

    expect(
      await screen.findByTestId(
        "probe-username",
      ),
    ).toHaveTextContent("root.admin");

    await user.click(
      screen.getByRole("button", {
        name: "probe refresh user",
      }),
    );

    expect(
      await screen.findByText(
        "refreshed.admin",
      ),
    ).toBeInTheDocument();

    expect(
      vi.mocked(globalThis.fetch),
    ).toHaveBeenCalledTimes(2);
  });

  it("clears authentication after successful logout", async () => {
    const user = userEvent.setup();

    mockJsonResponse(authenticatedUser);

    mockJsonResponse({
      detail: "Signed out successfully.",
    });

    const fetchMock = vi.mocked(
      globalThis.fetch,
    );

    render(
      <AuthProvider>
        <AuthStateProbe name="probe" />
      </AuthProvider>,
    );

    expect(
      await screen.findByTestId(
        "probe-username",
      ),
    ).toHaveTextContent("root.admin");

    await user.click(
      screen.getByRole("button", {
        name: "probe logout",
      }),
    );

    await waitFor(() => {
      expect(
        screen.getByTestId(
          "probe-status",
        ),
      ).toHaveTextContent(
        "unauthenticated",
      );
    });

    expect(
      screen.getByTestId(
        "probe-username",
      ),
    ).toHaveTextContent("none");

    expect(fetchMock).toHaveBeenCalledTimes(2);

    expect(
      fetchMock.mock.calls[1]?.[0],
    ).toBe("/api/accounts/logout/");

    expect(
      fetchMock.mock.calls[1]?.[1]
        ?.method,
    ).toBe("POST");
  });

  it("preserves authentication when logout fails", async () => {
    const user = userEvent.setup();

    mockJsonResponse(authenticatedUser);

    mockJsonResponse(
      {
        detail:
          "The logout request failed.",
      },
      500,
    );

    const fetchMock = vi.mocked(
      globalThis.fetch,
    );

    render(
      <AuthProvider>
        <AuthStateProbe name="probe" />
      </AuthProvider>,
    );

    expect(
      await screen.findByTestId(
        "probe-username",
      ),
    ).toHaveTextContent("root.admin");

    await user.click(
      screen.getByRole("button", {
        name: "probe logout",
      }),
    );

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(
        2,
      );
    });

    expect(
      screen.getByTestId(
        "probe-status",
      ),
    ).toHaveTextContent("authenticated");

    expect(
      screen.getByTestId(
        "probe-username",
      ),
    ).toHaveTextContent("root.admin");
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
