import {
  ApiError,
  NetworkError,
} from "../../../shared/api/apiClient";

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function collectMessages(
  value: unknown,
): string[] {
  if (typeof value === "string") {
    return [value];
  }

  if (Array.isArray(value)) {
    return value.flatMap(collectMessages);
  }

  if (isRecord(value)) {
    return Object.values(value).flatMap(
      collectMessages,
    );
  }

  return [];
}

function uniqueMessages(
  value: unknown,
): string[] {
  return [
    ...new Set(
      collectMessages(value),
    ),
  ];
}

export function getApiFieldError(
  error: unknown,
  field: string,
): string | undefined {
  if (
    !(error instanceof ApiError) ||
    !isRecord(error.body)
  ) {
    return undefined;
  }

  const messages = uniqueMessages(
    error.body[field],
  );

  return messages.length > 0
    ? messages.join(" ")
    : undefined;
}

export function getApiDetail(
  error: unknown,
): string | undefined {
  if (
    !(error instanceof ApiError) ||
    !isRecord(error.body)
  ) {
    return undefined;
  }

  const detail = error.body.detail;

  return typeof detail === "string"
    ? detail
    : undefined;
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

  if (error instanceof ApiError) {
    if (error.status === 429) {
      return (
        "Too many attempts. " +
        "Please wait and try again."
      );
    }

    if (error.status === 401) {
      return (
        "Your session has expired. " +
        "Sign in and try again."
      );
    }

    if (error.status === 403) {
      return (
        "The request could not be completed. " +
        "Refresh the page and try again."
      );
    }

    if (error.status >= 500) {
      return fallback;
    }

    const detail = getApiDetail(error);

    if (detail) {
      return detail;
    }

    const messages =
      uniqueMessages(error.body);

    if (messages.length > 0) {
      return messages.join(" ");
    }
  }

  return fallback;
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
