import {
  ApiError,
  NetworkError,
} from "../../../shared/api/apiClient";

type ApiErrorBody =
  Record<string, unknown>;

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

export function getApiDetail(
  error: unknown,
): string | undefined {
  if (!(error instanceof ApiError)) {
    return undefined;
  }

  if (typeof error.body === "string") {
    return error.body;
  }

  const body = getErrorBody(error);

  return typeof body?.detail === "string"
    ? body.detail
    : undefined;
}

export function getApiCode(
  error: unknown,
): string | undefined {
  const body = getErrorBody(error);

  return typeof body?.code === "string"
    ? body.code
    : undefined;
}

export function getApiFieldError(
  error: unknown,
  field: string,
): string | undefined {
  const body = getErrorBody(error);

  if (!body) {
    return undefined;
  }

  const fieldError = body[field];

  if (typeof fieldError === "string") {
    return fieldError;
  }

  if (Array.isArray(fieldError)) {
    return fieldError.find(
      (value): value is string =>
        typeof value === "string",
    );
  }

  return undefined;
}

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
    getApiCode(error) ===
    "password_change_required"
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
    detail?.includes("already activated"),
  );
}

export function isInvalidActivationLinkError(
  error: unknown,
): boolean {
  if (
    !(error instanceof ApiError) ||
    error.status !== 400
  ) {
    return false;
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

export function isInvalidResetLinkError(
  error: unknown,
): boolean {
  if (
    !(error instanceof ApiError) ||
    ![400, 404].includes(error.status)
  ) {
    return false;
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

export function getFormError(
  error: unknown,
  fallback: string,
): string {
  if (error instanceof NetworkError) {
    return (
      "Unable to reach Mission Control. " +
      "Check your connection and try again."
    );
  }

  if (isRateLimitError(error)) {
    return (
      "Too many requests. " +
      "Please wait a moment and try again."
    );
  }

  if (isCsrfError(error)) {
    return (
      "Your security session could not be verified. " +
      "Refresh the page and try again."
    );
  }

  if (isAuthorizationError(error)) {
    return (
      "You do not have permission " +
      "to perform this action."
    );
  }

  if (error instanceof ApiError) {
    /*
     * Never display backend details for server errors.
     * They may contain implementation information.
     */
    if (error.status >= 500) {
      return fallback;
    }

    return getApiDetail(error) ?? fallback;
  }

  return fallback;
}
