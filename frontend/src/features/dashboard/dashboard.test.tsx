import {
  render,
  renderHook,
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

import { visibleNavItems } from "../../shared/layout/navigation";
import { TopBar } from "../../shared/layout/TopBar";
import type { CurrentUser } from "../../shared/types/accounts";
import type { SectionState } from "../../shared/types/api";
import type { DefectListItem } from "../../shared/types/repairs";
import {
  formatShortDate,
  formatUtcTime,
  humanizeEnum,
} from "../../shared/utils/format";
import { DefectsPanel } from "./components/DefectsPanel";
import { KpiTiles } from "./components/KpiTiles";
import { useDashboardData } from "./hooks/useDashboardData";
import { KPI_ROLES } from "./rbac";
import type { DashboardSummary } from "./types/dashboard";

/* ---------- fixtures ---------- */

function makeUser(overrides: Partial<CurrentUser> = {}): CurrentUser {
  return {
    id: 1,
    username: "jdoe",
    email: "jdoe@example.com",
    first_name: "Jane",
    last_name: "Doe",
    rank: "Captain",
    contact: null,
    profile_picture: null,
    role: 1,
    role_code: "ADMIN",
    role_name: "Administrator",
    unit: null,
    is_active: true,
    must_change_password: false,
    ...overrides,
  };
}

function makeSummary(
  overrides: Partial<DashboardSummary> = {},
): DashboardSummary {
  return {
    activeMissions: 3,
    fleetTotal: 12,
    fleet: [],
    openDefects: 7,
    criticalDefects: 0,
    highDefects: 4,
    inMaintenance: 5,
    health: "operational",
    ...overrides,
  };
}

function successSummary(
  overrides: Partial<DashboardSummary> = {},
): SectionState<DashboardSummary> {
  return { status: "success", data: makeSummary(overrides) };
}

function defect(
  id: number,
  severity: DefectListItem["severity"],
  createdAt: string,
): DefectListItem {
  return {
    id,
    drone: id,
    defect_type: "ROTOR_FAILURE",
    severity,
    detected_at: createdAt,
    reporter: null,
    created_at: createdAt,
  };
}

/* Route fetch responses by URL so the parallel loads in useDashboardData
 * resolve deterministically regardless of ordering. */
function paginated(results: unknown[], count = results.length) {
  return { count, next: null, previous: null, results };
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

/* ---------- RBAC matrix ---------- */

describe("dashboard RBAC", () => {
  it("shows only the dashboard nav item when the role is unknown", () => {
    const items = visibleNavItems(null);
    expect(items.map((item) => item.id)).toEqual(["dashboard"]);
  });

  it("hides Repairs and Administration from an Operator", () => {
    const ids = visibleNavItems("OPERATOR").map((item) => item.id);
    expect(ids).toContain("missions");
    expect(ids).toContain("media");
    expect(ids).not.toContain("repairs");
    expect(ids).not.toContain("administration");
  });

  it("gates KPI tiles by role", () => {
    expect(KPI_ROLES["open-defects"].has("TECHNICIAN")).toBe(true);
    expect(KPI_ROLES["open-defects"].has("OPERATOR")).toBe(false);
    expect(KPI_ROLES["system-health"].has("VIEWER")).toBe(false);
  });
});

/* ---------- formatting ---------- */

describe("format helpers", () => {
  it("formats time in UTC", () => {
    expect(formatUtcTime("2026-07-31T09:05:00Z")).toBe("09:05 UTC");
    expect(formatUtcTime(null)).toBe("—");
  });

  it("formats short dates in UTC regardless of machine timezone", () => {
    // 23:30Z rolls into the next day in any positive-offset zone; the UTC pin
    // must keep it on the 31st. Compare (locale-independently) against the same
    // instant explicitly forced to UTC — this fails if the pin is ever dropped.
    const iso = "2026-07-31T23:30:00Z";
    const utcRef = new Date(iso).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      timeZone: "UTC",
    });
    expect(formatShortDate(iso)).toBe(utcRef);
    expect(formatShortDate(iso)).toContain("31");
  });

  it("humanizes screaming-snake enums", () => {
    expect(humanizeEnum("ROTOR_FAILURE")).toBe("Rotor failure");
    expect(humanizeEnum(null)).toBe("—");
  });
});

/* ---------- KpiTiles alert gating (regression for the always-red tile) ---------- */

describe("KpiTiles", () => {
  it("does not paint Open Defects red when there are no critical defects", () => {
    render(
      <KpiTiles
        role="ADMIN"
        summary={successSummary({ openDefects: 7, criticalDefects: 0 })}
      />,
    );
    expect(screen.getByText("7").className).not.toContain("text-mc-error");
  });

  it("escalates Open Defects to red when a critical defect exists", () => {
    render(
      <KpiTiles
        role="ADMIN"
        summary={successSummary({ openDefects: 7, criticalDefects: 2 })}
      />,
    );
    expect(screen.getByText("7").className).toContain("text-mc-error");
  });

  it("renders skeletons (no values) while loading", () => {
    render(
      <KpiTiles role="ADMIN" summary={{ status: "loading", data: null }} />,
    );
    expect(screen.queryByText("7")).not.toBeInTheDocument();
  });
});

/* ---------- DefectsPanel ---------- */

describe("DefectsPanel", () => {
  it("orders critical defects first, then by most recent", () => {
    const state: SectionState<DefectListItem[]> = {
      status: "success",
      data: [
        defect(11, "LOW", "2026-07-31T10:00:00Z"),
        defect(22, "CRITICAL", "2026-07-30T10:00:00Z"),
        defect(33, "MEDIUM", "2026-07-31T12:00:00Z"),
      ],
    };
    render(<DefectsPanel state={state} />);

    const order = screen
      .getAllByText(/Drone #/)
      .map((node) => node.textContent);
    expect(order).toEqual(["Drone #22", "Drone #33", "Drone #11"]);
  });

  it("shows a restricted state on a 403-derived section", () => {
    render(
      <DefectsPanel state={{ status: "restricted", data: null }} />,
    );
    expect(screen.getByText("Restricted access")).toBeInTheDocument();
  });
});

/* ---------- TopBar user menu accessibility ---------- */

function renderTopBar() {
  const router = createMemoryRouter(
    [
      {
        path: "/",
        element: (
          <TopBar
            pageTitle="Dashboard"
            collapsed={false}
            user={makeUser()}
            onMobileMenu={() => {}}
          />
        ),
      },
      { path: "/login", element: <div>LOGIN SCREEN</div> },
    ],
    { initialEntries: ["/"] },
  );
  return render(<RouterProvider router={router} />);
}

describe("TopBar user menu", () => {
  it("toggles aria-expanded and closes on Escape", async () => {
    const user = userEvent.setup();
    renderTopBar();

    const trigger = screen.getByRole("button", { expanded: false });
    expect(trigger).toHaveAttribute("aria-haspopup", "menu");

    await user.click(trigger);
    expect(trigger).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("menu")).toBeInTheDocument();

    await user.keyboard("{Escape}");
    expect(trigger).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  });

  it("signs out to the login screen", async () => {
    const user = userEvent.setup();
    renderTopBar();

    await user.click(screen.getByRole("button", { expanded: false }));
    await user.click(screen.getByRole("menuitem", { name: /sign out/i }));

    expect(await screen.findByText("LOGIN SCREEN")).toBeInTheDocument();
  });
});

/* ---------- useDashboardData role gating ---------- */

describe("useDashboardData", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/health/")) {
          return Promise.resolve(
            jsonResponse({ status: "healthy", dependencies: {} }),
          );
        }
        if (url.includes("page_size=1")) {
          // Any KPI count endpoint.
          return Promise.resolve(jsonResponse(paginated([], 4)));
        }
        if (url.includes("/api/missions/")) {
          return Promise.resolve(
            jsonResponse(paginated([{ id: 1, title: "Recon" }])),
          );
        }
        if (url.includes("/api/repairs/defects/")) {
          return Promise.resolve(jsonResponse(paginated([])));
        }
        if (url.includes("/api/accounts/audit-log/")) {
          return Promise.resolve(jsonResponse(paginated([])));
        }
        return Promise.resolve(jsonResponse(paginated([])));
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads every section for an Admin", async () => {
    const { result } = renderHook(() => useDashboardData("ADMIN"));

    await waitFor(() => {
      expect(result.current.summary.status).toBe("success");
    });
    expect(result.current.missions.status).toBe("success");
    expect(result.current.audit.status).toBe("success");
    expect(result.current.summary.data?.health).toBe("operational");
  });

  it("marks defects and audit restricted for an Operator without fetching them", () => {
    const { result } = renderHook(() => useDashboardData("OPERATOR"));

    // Restricted sections are derived synchronously from the role, never fetched.
    expect(result.current.defects.status).toBe("restricted");
    expect(result.current.audit.status).toBe("restricted");

    const fetchMock = vi.mocked(globalThis.fetch);
    const requested = fetchMock.mock.calls.map((call) => String(call[0]));
    expect(requested.some((url) => url.includes("audit-log"))).toBe(false);
  });

  it("degrades a 403 missions response to a restricted section", async () => {
    vi.mocked(globalThis.fetch).mockImplementation((input) => {
      const url = String(input);
      if (url.includes("/api/missions/") && !url.includes("page_size=1")) {
        return Promise.resolve(jsonResponse({ detail: "Forbidden" }, 403));
      }
      if (url.includes("/api/health/")) {
        return Promise.resolve(
          jsonResponse({ status: "healthy", dependencies: {} }),
        );
      }
      return Promise.resolve(jsonResponse(paginated([], 0)));
    });

    const { result } = renderHook(() => useDashboardData("ADMIN"));

    await waitFor(() => {
      expect(result.current.missions.status).toBe("restricted");
    });
  });
});
