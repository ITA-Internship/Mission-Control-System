import {
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";

import userEvent from "@testing-library/user-event";

import {
  createMemoryRouter,
  Outlet,
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

import { AdministrationPage } from "./pages/AdministrationPage";

import type { ShellContext } from "../../shared/layout/shellContext";
import type { CurrentUser } from "../../shared/types/accounts";

interface RouteHandler {
  match: (url: string) => boolean;
  respond: (
    url: string,
    init?: RequestInit,
  ) => Response;
}

const CURRENT_USER: CurrentUser = {
  id: 1,
  username: "m.hale",
  email: "m.hale@mcs.mil",
  first_name: "Marcus",
  last_name: "Hale",
  rank: "Col.",
  contact: "",
  profile_picture: null,
  role: 1,
  role_code: "ADMIN",
  role_name: "Admin",
  unit: 1,
  is_active: true,
  must_change_password: false,
};

const ROLES = [
  {
    id: 1,
    code: "ADMIN",
    name: "Admin",
  },
  {
    id: 4,
    code: "OPERATOR",
    name: "Operator",
  },
];

const UNITS = [
  {
    id: 1,
    name: "1st Air Brigade",
    code: "1ST-AIR-BDE",
    description:
      "Primary aerial strike brigade.",
    is_active: true,
    drone_count: 24,
    user_count: 18,
  },
  {
    id: 2,
    name: "4th Logistics Squadron",
    code: "4TH-LOG-SQN",
    description:
      "Supply chain and logistics.",
    is_active: false,
    drone_count: 2,
    user_count: 3,
  },
];

const USERS = [
  {
    id: 1,
    username: "m.hale",
    email: "m.hale@mcs.mil",
    first_name: "Marcus",
    last_name: "Hale",
    role: 1,
    unit: 1,
    is_active: true,
    created_by_username: "system",
    last_login: "2026-07-30T08:14:00Z",
  },
  {
    id: 9,
    username: "a.sorel",
    email: "a.sorel@mcs.mil",
    first_name: "Anya",
    last_name: "Sorel",
    role: 4,
    unit: 2,
    is_active: false,
    created_by_username: "m.hale",
    last_login: null,
  },
];

const AUDIT_ENTRIES = [
  {
    id: 31,
    actor: 1,
    actor_username: "m.hale",
    target_user: 9,
    target_user_username: "a.sorel",
    action_type: "ACCOUNT_DEACTIVATED",
    result: "SUCCESS",
    description:
      "Account status changed to inactive.",
    ip_address: "10.20.1.42",
    user_agent: "Chrome/126 Win10",
    created_at: "2026-07-30T08:08:44Z",
  },
  {
    id: 30,
    actor: 7,
    actor_username: "b.larkin",
    target_user: null,
    target_user_username: null,
    action_type: "LOGIN_FAILED",
    result: "FAILED",
    description: "Invalid credentials.",
    ip_address: "203.0.113.7",
    user_agent: "curl/7.88.1",
    created_at: "2026-07-29T14:22:05Z",
  },
];

function jsonResponse(
  body: unknown,
  status = 200,
): Response {
  return new Response(
    JSON.stringify(body),
    {
      status,
      headers: {
        "Content-Type": "application/json",
      },
    },
  );
}

function paginated(results: unknown[]) {
  return {
    count: results.length,
    next: null,
    previous: null,
    results,
  };
}

function route(
  pattern: string,
  respond: RouteHandler["respond"],
): RouteHandler {
  return {
    match: (url) => url.startsWith(pattern),
    respond,
  };
}

/** Route the stubbed fetch by URL so parallel page loads stay deterministic. */
function stubApi(
  ...handlers: RouteHandler[]
) {
  const defaults: RouteHandler[] = [
    route("/api/accounts/users/me/", () =>
      jsonResponse(CURRENT_USER),
    ),
    route("/api/roles/", () =>
      jsonResponse(paginated(ROLES)),
    ),
    route(
      "/api/accounts/military-units/",
      () => jsonResponse(paginated(UNITS)),
    ),
    route("/api/accounts/audit-log/", () =>
      jsonResponse(
        paginated(AUDIT_ENTRIES),
      ),
    ),
    route("/api/accounts/users/", () =>
      jsonResponse(paginated(USERS)),
    ),
  ];

  const fetchMock = vi.mocked(
    globalThis.fetch,
  );

  fetchMock.mockImplementation(
    (input, init) => {
      const url = String(input);

      const handler = [
        ...handlers,
        ...defaults,
      ].find((candidate) =>
        candidate.match(url),
      );

      if (!handler) {
        throw new Error(
          `Unhandled request: ${url}`,
        );
      }

      return Promise.resolve(
        handler.respond(url, init),
      );
    },
  );

  return fetchMock;
}

/** Stand-in for the app shell, which hands the signed-in user to the page. */
function ShellStub({
  user,
}: {
  user: CurrentUser;
}) {
  const context: ShellContext = { user };

  return <Outlet context={context} />;
}

function renderConsole(
  initialEntry = "/administration",
  user: CurrentUser = CURRENT_USER,
) {
  const router = createMemoryRouter(
    [
      {
        path: "/administration",
        element: <ShellStub user={user} />,
        children: [
          {
            index: true,
            Component: AdministrationPage,
          },
        ],
      },
      {
        path: "/dashboard",
        element: <p>Dashboard</p>,
      },
    ],
    {
      initialEntries: [initialEntry],
    },
  );

  return {
    ...render(
      <RouterProvider router={router} />,
    ),
    router,
  };
}

function requestedUrls(): string[] {
  return vi
    .mocked(globalThis.fetch)
    .mock.calls.map((call) =>
      String(call[0]),
    );
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn());
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("users tab", () => {
  it("lists users with resolved role and unit references", async () => {
    stubApi();

    renderConsole();

    const row = (
      await screen.findByText("Anya Sorel")
    ).closest("tr")!;

    expect(
      within(
        screen.getByRole("table"),
      ).getByText("Marcus Hale"),
    ).toBeInTheDocument();

    expect(
      within(row).getByText("OPERATOR"),
    ).toBeInTheDocument();

    expect(
      within(row).getByText("4TH-LOG-SQN"),
    ).toBeInTheDocument();

    expect(
      within(row).getByText("Inactive"),
    ).toBeInTheDocument();

    expect(
      requestedUrls().some((url) =>
        url.startsWith(
          "/api/accounts/users/?page=1&page_size=10",
        ),
      ),
    ).toBe(true);
  });

  it("reports a missing user list endpoint instead of an empty table", async () => {
    stubApi(
      route("/api/accounts/users/?", () =>
        jsonResponse(
          { detail: "Not found." },
          404,
        ),
      ),
    );

    renderConsole();

    expect(
      await screen.findByText(
        "Users endpoint unavailable",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /GET \/api\/accounts\/users\/ endpoint yet/,
      ),
    ).toBeInTheDocument();
  });

  it("sends the create-user payload with a split display name", async () => {
    const user = userEvent.setup();

    const fetchMock = stubApi();

    renderConsole();

    await user.click(
      await screen.findByRole("button", {
        name: "Create User",
      }),
    );

    await user.type(
      screen.getByLabelText("Full name"),
      "Takeshi Mori",
    );

    await user.type(
      screen.getByLabelText("Username"),
      "t.mori",
    );

    await user.type(
      screen.getByLabelText("Email"),
      "t.mori@mcs.mil",
    );

    await user.selectOptions(
      screen.getByLabelText("Role"),
      "4",
    );

    await user.selectOptions(
      screen.getByLabelText("Unit"),
      "1",
    );

    await user.click(
      screen.getByRole("button", {
        name: /Create & Send Activation/,
      }),
    );

    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(
          (call) =>
            String(call[0]) ===
              "/api/accounts/users/" &&
            call[1]?.method === "POST",
        ),
      ).toBe(true);
    });

    const createCall =
      fetchMock.mock.calls.find(
        (call) =>
          String(call[0]) ===
            "/api/accounts/users/" &&
          call[1]?.method === "POST",
      )!;

    expect(
      JSON.parse(
        createCall[1]?.body as string,
      ),
    ).toEqual({
      username: "t.mori",
      email: "t.mori@mcs.mil",
      first_name: "Takeshi",
      last_name: "Mori",
      role: 4,
      unit: 1,
    });

    expect(
      await screen.findByText(
        /activation email has been sent/,
      ),
    ).toBeInTheDocument();
  });

  it("requires a reason before deactivating a user", async () => {
    const user = userEvent.setup();

    const fetchMock = stubApi(
      route(
        "/api/accounts/users/1/status/",
        () =>
          jsonResponse({
            detail:
              "User status updated successfully.",
            is_active: false,
          }),
      ),
    );

    renderConsole();

    await user.click(
      await screen.findByRole("button", {
        name: "Actions for Marcus Hale",
      }),
    );

    await user.click(
      screen.getByRole("menuitem", {
        name: "Deactivate",
      }),
    );

    await user.click(
      screen.getByRole("button", {
        name: "Deactivate",
      }),
    );

    expect(
      await screen.findByText(
        "A reason is required.",
      ),
    ).toBeInTheDocument();

    await user.type(
      screen.getByLabelText(
        /Reason \(recorded in audit log\)/,
      ),
      "Transferred out of unit",
    );

    await user.click(
      screen.getByRole("button", {
        name: "Deactivate",
      }),
    );

    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(
          (call) =>
            String(call[0]) ===
            "/api/accounts/users/1/status/",
        ),
      ).toBe(true);
    });

    const statusCall =
      fetchMock.mock.calls.find(
        (call) =>
          String(call[0]) ===
          "/api/accounts/users/1/status/",
      )!;

    expect(statusCall[1]?.method).toBe(
      "PATCH",
    );

    expect(
      JSON.parse(
        statusCall[1]?.body as string,
      ),
    ).toEqual({
      is_active: false,
      reason: "Transferred out of unit",
    });
  });
});

describe("military units tab", () => {
  it("shows unit rows and the toggle action", async () => {
    stubApi();

    renderConsole(
      "/administration?tab=units",
    );

    const row = (
      await screen.findByText(
        "4th Logistics Squadron",
      )
    ).closest("tr")!;

    expect(
      within(row).getByText("4TH-LOG-SQN"),
    ).toBeInTheDocument();

    expect(
      within(row).getByRole("button", {
        name: "Activate",
      }),
    ).toBeInTheDocument();
  });
});

describe("audit log tab", () => {
  it("applies action-type and result filters through the API", async () => {
    const user = userEvent.setup();

    stubApi();

    renderConsole(
      "/administration?tab=audit",
    );

    expect(
      await screen.findByText(
        "ACCOUNT_DEACTIVATED",
      ),
    ).toBeInTheDocument();

    await user.selectOptions(
      screen.getByLabelText(
        "Filter by action type",
      ),
      "LOGIN_FAILED",
    );

    await waitFor(() => {
      expect(
        requestedUrls().some(
          (url) =>
            url.includes(
              "/api/accounts/audit-log/?",
            ) &&
            url.includes(
              "action_type=LOGIN_FAILED",
            ),
        ),
      ).toBe(true);
    });

    expect(
      screen.getByText(
        "Action: LOGIN_FAILED",
      ),
    ).toBeInTheDocument();
  });

  it("exports the filtered log as CSV", async () => {
    const user = userEvent.setup();

    const createObjectUrl = vi.fn(
      () => "blob:audit",
    );

    const revokeObjectUrl = vi.fn();

    vi.stubGlobal("URL", {
      ...URL,
      createObjectURL: createObjectUrl,
      revokeObjectURL: revokeObjectUrl,
    });

    const clickSpy = vi
      .spyOn(
        HTMLAnchorElement.prototype,
        "click",
      )
      .mockImplementation(() => {});

    stubApi(
      route(
        "/api/accounts/audit-log/export/",
        () =>
          new Response(
            "ID,Date/Time\n31,2026-07-30",
            {
              headers: {
                "Content-Type": "text/csv",
                "Content-Disposition":
                  'attachment; filename="audit_logs.csv"',
              },
            },
          ),
      ),
    );

    renderConsole(
      "/administration?tab=audit",
    );

    await user.click(
      await screen.findByRole("button", {
        name: "Export CSV",
      }),
    );

    expect(
      await screen.findByText(
        /exported as CSV/,
      ),
    ).toBeInTheDocument();

    expect(createObjectUrl).toHaveBeenCalled();
    expect(clickSpy).toHaveBeenCalled();
  });
});

describe("role gating", () => {
  it("redirects non-admins away without issuing any request", async () => {
    const fetchMock = stubApi();

    const { router } = renderConsole(
      "/administration",
      {
        ...CURRENT_USER,
        role: 2,
        role_code: "COMMANDER",
        role_name: "Commander",
      },
    );

    await waitFor(() => {
      expect(
        router.state.location.pathname,
      ).toBe("/dashboard");
    });

    expect(
      screen.queryByRole("tab", {
        name: "Users",
      }),
    ).not.toBeInTheDocument();

    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("renders the console for admins", async () => {
    stubApi();

    const { router } = renderConsole();

    expect(
      await screen.findByRole("tab", {
        name: "Users",
      }),
    ).toBeInTheDocument();

    expect(
      router.state.location.pathname,
    ).toBe("/administration");
  });
});

describe("tab navigation", () => {
  it("opens the tab named in the query string", async () => {
    stubApi();

    renderConsole(
      "/administration?tab=audit",
    );

    const auditTab = await screen.findByRole(
      "tab",
      { name: "Audit Log" },
    );

    expect(auditTab).toHaveAttribute(
      "aria-selected",
      "true",
    );

    expect(
      screen.getByRole("tab", {
        name: "Users",
      }),
    ).toHaveAttribute(
      "aria-selected",
      "false",
    );
  });
});
