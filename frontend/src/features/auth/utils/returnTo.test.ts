import {
  describe,
  expect,
  it,
} from "vitest";

import {
  buildLoginPath,
  buildRequiredPasswordChangePath,
  DEFAULT_AUTHENTICATED_ROUTE,
  getReturnDestination,
  getSafeReturnTo,
} from "./returnTo";

describe("returnTo navigation", () => {
  it("accepts an internal route", () => {
    expect(
      getSafeReturnTo(
        "/missions/42?tab=activity#latest",
      ),
    ).toBe(
      "/missions/42?tab=activity#latest",
    );
  });

  it("rejects an external URL", () => {
    expect(
      getSafeReturnTo(
        "https://example.com/account",
      ),
    ).toBeNull();
  });

  it("rejects a protocol-relative URL", () => {
    expect(
      getSafeReturnTo(
        "//example.com/account",
      ),
    ).toBeNull();
  });

  it("rejects a relative path without a leading slash", () => {
    expect(
      getSafeReturnTo("missions/42"),
    ).toBeNull();
  });

  it("rejects backslash navigation", () => {
    expect(
      getSafeReturnTo(
        "/\\example.com/account",
      ),
    ).toBeNull();
  });

  it("rejects malformed encoding", () => {
    expect(
      getSafeReturnTo(
        "/missions/%E0%A4%A",
      ),
    ).toBeNull();
  });

  it.each([
    "/login",
    "/login?returnTo=/my-profile",
    "/logout",
    "/forgot-password",
    "/reset-password/user/token",
    "/activate/47/token",
    "/change-password/required",
  ])(
    "rejects authentication route %s",
    (route) => {
      expect(
        getSafeReturnTo(route),
      ).toBeNull();
    },
  );

  it("uses my profile as the fallback", () => {
    expect(
      getReturnDestination(
        "https://example.com",
      ),
    ).toBe(
      DEFAULT_AUTHENTICATED_ROUTE,
    );
  });

  it("builds an encoded login path", () => {
    expect(
      buildLoginPath(
        "/missions/42?tab=activity",
      ),
    ).toBe(
      "/login?returnTo=%2Fmissions%2F42%3Ftab%3Dactivity",
    );
  });

  it("builds an encoded password-change path", () => {
    expect(
      buildRequiredPasswordChangePath(
        "/missions/42",
      ),
    ).toBe(
      "/change-password/required?returnTo=%2Fmissions%2F42",
    );
  });

  it("does not add invalid returnTo values", () => {
    expect(
      buildLoginPath(
        "https://example.com",
      ),
    ).toBe("/login");

    expect(
      buildRequiredPasswordChangePath(
        "//example.com",
      ),
    ).toBe(
      "/change-password/required",
    );
  });
});
