import { NetworkError } from "../../../shared/api/apiClient";
import {
  getFormError,
  isForbiddenError,
  isNotFoundError,
  isUnauthenticatedError,
} from "../../../shared/utils/apiErrors";

export interface TableErrorInfo {
  title: string;
  message: string;
  /** True when the endpoint itself is missing — retrying will not help. */
  isEndpointMissing: boolean;
  canRetry: boolean;
}

/**
 * Turn a failed list request into something a console operator can act on.
 *
 * `404` is called out separately: the Administration brief specifies user-list
 * and military-unit endpoints that the API does not expose yet, and telling the
 * operator "no users found" in that case would be a lie.
 */
export function describeTableError(
  error: unknown,
  resource: string,
  endpoint: string,
): TableErrorInfo {
  if (isNotFoundError(error)) {
    return {
      title: `${resource} endpoint unavailable`,
      message: `The API has no ${endpoint} endpoint yet, so ${resource.toLowerCase()} cannot be listed.`,
      isEndpointMissing: true,
      canRetry: false,
    };
  }

  if (isForbiddenError(error)) {
    return {
      title: "Access denied",
      message: `Your role does not include permission to view ${resource.toLowerCase()}.`,
      isEndpointMissing: false,
      canRetry: false,
    };
  }

  if (isUnauthenticatedError(error)) {
    return {
      title: "Session expired",
      message:
        "Sign in again to continue working in the administration console.",
      isEndpointMissing: false,
      canRetry: false,
    };
  }

  if (error instanceof NetworkError) {
    return {
      title: "Connection lost",
      message:
        "Mission Control could not be reached. Check your connection and retry.",
      isEndpointMissing: false,
      canRetry: true,
    };
  }

  return {
    title: `${resource} could not be loaded`,
    message: getFormError(
      error,
      "The request failed unexpectedly. Retry, or check the API logs.",
    ),
    isEndpointMissing: false,
    canRetry: true,
  };
}
