import { ApiError } from "../../../shared/api/apiClient";
import { getApiDetail } from "../../../shared/utils/apiErrors";

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
