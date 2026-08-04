const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Mirrors Django's `UnicodeUsernameValidator` (Unicode `\w`): Unicode letters,
// digits and underscore, plus @ . + -. A plain JS `\w` is ASCII-only and would
// reject valid non-ASCII usernames the backend accepts, so match the Unicode
// letter/number classes explicitly.
const USERNAME_PATTERN =
  /^[\p{L}\p{N}_.@+-]+$/u;

export function validateRequired(
  value: string,
  label: string,
): string | undefined {
  return value.trim()
    ? undefined
    : `${label} is required.`;
}

export function validateEmail(
  value: string,
): string | undefined {
  const email = value.trim();

  if (!email) {
    return "Email is required.";
  }

  return EMAIL_PATTERN.test(email)
    ? undefined
    : "Enter a valid email address.";
}

/** Mirrors Django's default `UnicodeUsernameValidator` character set. */
export function validateUsername(
  value: string,
): string | undefined {
  const username = value.trim();

  if (!username) {
    return "Username is required.";
  }

  return USERNAME_PATTERN.test(username)
    ? undefined
    : "Use letters, digits and @ . + - _ only.";
}

export function validateUnitCode(
  value: string,
): string | undefined {
  const code = value.trim();

  if (!code) {
    return "Unit code is required.";
  }

  return /^[A-Z0-9-]+$/.test(code)
    ? undefined
    : "Use uppercase letters, digits and hyphens only.";
}

/** Split a display name into Django's `first_name` / `last_name` pair. */
export function splitFullName(
  fullName: string,
): {
  firstName: string;
  lastName: string;
} {
  const parts = fullName
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  if (parts.length <= 1) {
    return {
      firstName: parts[0] ?? "",
      lastName: "",
    };
  }

  return {
    firstName: parts[0],
    lastName: parts.slice(1).join(" "),
  };
}
