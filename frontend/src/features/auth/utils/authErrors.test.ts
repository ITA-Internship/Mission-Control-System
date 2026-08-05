import {
  describe,
  expect,
  it,
} from "vitest";

import {
  ApiError,
  NetworkError,
} from "../../../shared/api/apiClient";
import {
  getFormError,
  isAuthorizationError,
  isCsrfError,
  isPasswordChangeRequiredError,
  isRateLimitError,
  isSessionAuthenticationError,
} from "./authErrors";

describe("authentication error handling", () => {
  it("classifies a 401 as a session authentication error", () => {
    const error = new ApiError(
      401,
      {
        detail:
          "Authentication credentials were not provided.",
      },
    );

    expect(
      isSessionAuthenticationError(error),
    ).toBe(true);
  });

  it("classifies an authentication-related 403", () => {
    const error = new ApiError(
      403,
      {
        detail:
          "Authentication credentials were not provided.",
        code: "not_authenticated",
      },
    );

    expect(
      isSessionAuthenticationError(error),
    ).toBe(true);

    expect(
      isAuthorizationError(error),
    ).toBe(false);
  });

  it("distinguishes a genuine authorization 403", () => {
    const error = new ApiError(
      403,
      {
        detail:
          "You do not have permission to perform this action.",
      },
    );

    expect(
      isSessionAuthenticationError(error),
    ).toBe(false);

    expect(
      isAuthorizationError(error),
    ).toBe(true);

    expect(
      getFormError(
        error,
        "Fallback message.",
      ),
    ).toBe(
      "You do not have permission to perform this action.",
    );
  });

  it("classifies password-change enforcement separately", () => {
    const error = new ApiError(
      403,
      {
        detail:
          "Password change is required.",
        code: "password_change_required",
      },
    );

    expect(
      isPasswordChangeRequiredError(error),
    ).toBe(true);

    expect(
      isAuthorizationError(error),
    ).toBe(false);
  });

  it("classifies a CSRF failure", () => {
    const error = new ApiError(
      403,
      {
        detail:
          "CSRF verification failed.",
      },
    );

    expect(isCsrfError(error)).toBe(true);

    expect(
      getFormError(
        error,
        "Fallback message.",
      ),
    ).toBe(
      "Your security session could not be verified. " +
        "Refresh the page and try again.",
    );
  });

  it("returns an understandable rate-limit message", () => {
    const error = new ApiError(
      429,
      {
        detail:
          "Request was throttled.",
      },
    );

    expect(
      isRateLimitError(error),
    ).toBe(true);

    expect(
      getFormError(
        error,
        "Fallback message.",
      ),
    ).toBe(
      "Too many requests. " +
        "Please wait a moment and try again.",
    );
  });

  it("returns a safe network message", () => {
    expect(
      getFormError(
        new NetworkError(),
        "Fallback message.",
      ),
    ).toBe(
      "Unable to reach Mission Control. " +
        "Check your connection and try again.",
    );
  });

  it("does not expose server-error details", () => {
    const error = new ApiError(
      500,
      {
        detail:
          "Internal Django traceback and database details.",
      },
    );

    expect(
      getFormError(
        error,
        "Something went wrong. Please try again.",
      ),
    ).toBe(
      "Something went wrong. Please try again.",
    );
  });
});
