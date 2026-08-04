export const DEFAULT_AUTHENTICATED_ROUTE =
  "/my-profile";

const INTERNAL_URL_BASE =
  "https://mission-control.local";

const BLOCKED_AUTH_ROUTES = [
  "/login",
  "/logout",
  "/forgot-password",
  "/reset-password",
  "/activate",
  "/change-password/required",
] as const;

function isBlockedAuthRoute(
  pathname: string,
): boolean {
  return BLOCKED_AUTH_ROUTES.some(
    (route) =>
      pathname === route ||
      pathname.startsWith(`${route}/`),
  );
}

function hasControlCharacters(
  value: string,
): boolean {
  return Array.from(value).some(
    (character) => {
      const characterCode =
        character.charCodeAt(0);

      return (
        characterCode <= 0x1f ||
        characterCode === 0x7f
      );
    },
  );
}

export function getSafeReturnTo(
  value: string | null | undefined,
): string | null {
  if (!value) {
    return null;
  }

  const candidate = value.trim();

  if (
    !candidate.startsWith("/") ||
    candidate.startsWith("//") ||
    candidate.includes("\\") ||
    hasControlCharacters(candidate)) {
    return null;
  }

  try {
    // Reject malformed percent encoding.
    decodeURIComponent(candidate);

    const parsedUrl = new URL(
      candidate,
      INTERNAL_URL_BASE,
    );

    if (
      parsedUrl.origin !==
        INTERNAL_URL_BASE ||
      isBlockedAuthRoute(
        parsedUrl.pathname,
      )
    ) {
      return null;
    }

    return [
      parsedUrl.pathname,
      parsedUrl.search,
      parsedUrl.hash,
    ].join("");
  } catch {
    return null;
  }
}

export function getReturnDestination(
  value: string | null | undefined,
): string {
  return (
    getSafeReturnTo(value) ??
    DEFAULT_AUTHENTICATED_ROUTE
  );
}

export function buildLoginPath(
  returnTo: string | null | undefined,
): string {
  const safeReturnTo =
    getSafeReturnTo(returnTo);

  if (!safeReturnTo) {
    return "/login";
  }

  return (
    "/login?returnTo=" +
    encodeURIComponent(safeReturnTo)
  );
}

export function buildRequiredPasswordChangePath(
  returnTo: string | null | undefined,
): string {
  const safeReturnTo =
    getSafeReturnTo(returnTo);

  if (!safeReturnTo) {
    return "/change-password/required";
  }

  return (
    "/change-password/required?returnTo=" +
    encodeURIComponent(safeReturnTo)
  );
}