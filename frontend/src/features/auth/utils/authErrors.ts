import { ApiError } from "../../../shared/api/apiClient";
import { getApiDetail } from "../../../shared/utils/apiErrors";

/*
 * Auth-specific error predicates.
 *
 * Transport-level helpers live in shared/utils/apiErrors because they are
 * used across multiple features. They are re-exported here so existing auth,
 * profile and session imports do not need to change.
 */
export {
  getApiDetail,
  getApiFieldError,
  getFormError,
} from "../../../shared/utils/apiErrors";

type ApiErrorBody = Record<string, unknown>;

const SESSION_AUTH_CODES = new Set([
  "not_authenticated",
  "authentication_failed",
  "session_expired",
]);

function isRecord(
  value: unknown,
): value is ApiErrorBody {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function getErrorBody(
  error: unknown,
): ApiErrorBody | null {
  if (
    !(error instanceof ApiError) ||
    !isRecord(error.body)
  ) {
    return null;
  }

  return error.body;
}

export function getApiCode(
  error: unknown,
): string | undefined {
  const body = getErrorBody(error);

  return typeof body?.code === "string"
    ? body.code
    : undefined;
}

/** The session cookie is missing, expired or rejected. */
export function isSessionAuthenticationError(
  error: unknown,
): boolean {
  if (!(error instanceof ApiError)) {
    return false;
  }

  if (error.status === 401) {
    return true;
  }

  if (error.status !== 403) {
    return false;
  }

  const code =
    getApiCode(error)?.toLowerCase();

  if (
    code &&
    SESSION_AUTH_CODES.has(code)
  ) {
    return true;
  }

  const detail =
    getApiDetail(error)?.toLowerCase();

  if (!detail) {
    return false;
  }

  return (
    detail.includes(
      "authentication credentials were not provided",
    ) ||
    detail.includes("not authenticated") ||
    detail.includes("session expired") ||
    detail.includes("invalid session")
  );
}

/** The account must set a new password before any other request succeeds. */
export function isPasswordChangeRequiredError(
  error: unknown,
): boolean {
  if (
    !(error instanceof ApiError) ||
    error.status !== 403
  ) {
    return false;
  }

  return (
    getApiCode(error)?.toLowerCase() ===
    "password_change_required"
  );
}

export function isCsrfError(
  error: unknown,
): boolean {
  if (
    !(error instanceof ApiError) ||
    error.status !== 403
  ) {
    return false;
  }

  const code =
    getApiCode(error)?.toLowerCase();

  if (
    code === "csrf_failed" ||
    code === "csrf_failure"
  ) {
    return true;
  }

  const detail =
    getApiDetail(error)?.toLowerCase();

  return Boolean(
    detail?.includes("csrf"),
  );
}

export function isAuthorizationError(
  error: unknown,
): boolean {
  return (
    error instanceof ApiError &&
    error.status === 403 &&
    !isSessionAuthenticationError(error) &&
    !isPasswordChangeRequiredError(error) &&
    !isCsrfError(error)
  );
}

export function isRateLimitError(
  error: unknown,
): boolean {
  return (
    error instanceof ApiError &&
    error.status === 429
  );
}

export function isInvalidResetLinkError(
  error: unknown,
): boolean {
  if (
    !(error instanceof ApiError) ||
    ![400, 404].includes(error.status)
  ) {
    return false;
  }

  if (error.status === 404) {
    return true;
  }

  const code =
    getApiCode(error)?.toLowerCase();

  if (
    code === "invalid_reset_link" ||
    code === "reset_link_invalid" ||
    code === "reset_link_expired"
  ) {
    return true;
  }

  const detail =
    getApiDetail(error)?.toLowerCase();

  if (!detail) {
    return false;
  }

  return (
    detail.includes("reset link") &&
    (
      detail.includes("invalid") ||
      detail.includes("expired")
    )
  );
}

export function isInvalidActivationLinkError(
  error: unknown,
): boolean {
  if (
    !(error instanceof ApiError) ||
    ![400, 404].includes(error.status)
  ) {
    return false;
  }

  if (error.status === 404) {
    return true;
  }

  const code =
    getApiCode(error)?.toLowerCase();

  if (
    code === "invalid_activation_link" ||
    code === "activation_link_invalid" ||
    code === "activation_link_expired"
  ) {
    return true;
  }

  const detail =
    getApiDetail(error)?.toLowerCase();

  return Boolean(
    detail?.includes(
      "invalid or expired activation link",
    ) ||
      (
        detail?.includes("activation link") &&
        (
          detail.includes("invalid") ||
          detail.includes("expired")
        )
      ),
  );
}

export function isAlreadyActivatedError(
  error: unknown,
): boolean {
  if (!(error instanceof ApiError)) {
    return false;
  }

  const code =
    getApiCode(error)?.toLowerCase();

  if (
    code === "already_activated" ||
    code === "account_already_activated"
  ) {
    return true;
  }

  const detail =
    getApiDetail(error)?.toLowerCase();

  return Boolean(
    error.status === 400 &&
      (
        detail?.includes(
          "already activated",
        ) ||
        detail?.includes(
          "already been activated",
        )
      ),
  );
}