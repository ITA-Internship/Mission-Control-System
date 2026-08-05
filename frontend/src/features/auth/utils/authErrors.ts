import { ApiError } from "../../../shared/api/apiClient";
import { getApiDetail } from "../../../shared/utils/apiErrors";

/*
 * Auth-specific error predicates.
 *
 * The transport-level helpers (`getApiDetail`, `getApiFieldError`,
 * `getFormError`) live in `shared/utils/apiErrors` because every feature needs
 * them; they are re-exported here so auth, profile and session callers can keep
 * importing their error helpers from one module.
 */
export {
  getApiDetail,
  getApiFieldError,
  getFormError,
} from "../../../shared/utils/apiErrors";

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
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

  const detail = (
    getApiDetail(error) ?? ""
  ).toLowerCase();

  return (
    detail.includes(
      "authentication credentials were not provided",
    ) || detail.includes("not authenticated")
  );
}

/** The account must set a new password before any other request succeeds. */
export function isPasswordChangeRequiredError(
  error: unknown,
): boolean {
  return (
    error instanceof ApiError &&
    error.status === 403 &&
    isRecord(error.body) &&
    error.body.code ===
      "password_change_required"
  );
}

export function isInvalidResetLinkError(
  error: unknown,
): boolean {
  if (!(error instanceof ApiError)) {
    return false;
  }

  if (error.status === 404) {
    return true;
  }

  const detail = (
    getApiDetail(error) ?? ""
  ).toLowerCase();

  return (
    error.status === 400 &&
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
  if (!(error instanceof ApiError)) {
    return false;
  }

  if (error.status === 404) {
    return true;
  }

  const detail = (
    getApiDetail(error) ?? ""
  ).toLowerCase();

  return (
    error.status === 400 &&
    detail.includes("activation link") &&
    (
      detail.includes("invalid") ||
      detail.includes("expired")
    )
  );
}

export function isAlreadyActivatedError(
  error: unknown,
): boolean {
  if (!(error instanceof ApiError)) {
    return false;
  }

  const detail = (
    getApiDetail(error) ?? ""
  ).toLowerCase();

  return (
    error.status === 400 &&
    detail.includes(
      "already been activated",
    )
  );
}
