import type { CurrentUser } from "../../../shared/types/accounts";
import type {
  PasswordRequirement,
  PasswordStrength,
  ProfileFormState,
} from "../types/profile";

export function getInitials(user: CurrentUser): string {
  const first =
    user.first_name?.[0] ??
    user.username?.[0] ??
    "U";

  const last =
    user.last_name?.[0] ?? "";

  return `${first}${last}`.toUpperCase();
}

export function getRoleLabel(user: CurrentUser): string {
  return (
    user.role_name ??
    user.role_code ??
    (user.role !== null
      ? `Role #${user.role}`
      : "Unassigned")
  );
}

export function getUnitLabel(user: CurrentUser): string {
  if (user.unit_name) {
    return user.unit_name;
  }

  return user.unit !== null
    ? `Unit #${user.unit}`
    : "Not assigned";
}

export function getUserIdentifier(
  user: CurrentUser,
): string {
  return `USR-${String(user.id).padStart(
    4,
    "0",
  )}`;
}

export function formatDate(
  value: string | null | undefined,
): string | null {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      dateStyle: "medium",
    },
  ).format(parsed);
}

export function formatDateTime(
  value: string | null | undefined,
): string | null {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(parsed);
}

export function getProfileFormState(
  user: CurrentUser,
): ProfileFormState {
  return {
    firstName: user.first_name,
    lastName: user.last_name,
    rank: user.rank ?? "",
    contact: user.contact ?? "",
  };
}

export function getStrength(
  password: string,
): PasswordStrength {
  if (!password) {
    return {
      score: 0,
      label: "",
      color: "transparent",
    };
  }

  let score = 0;

  if (password.length >= 8) {
    score += 1;
  }
  if (/[a-z]/.test(password)) {
    score += 1;
  }
  if (/[A-Z]/.test(password)) {
    score += 1;
  }
  if (/[0-9]/.test(password)) {
    score += 1;
  }
  if (/[^A-Za-z0-9]/.test(password)) {
    score += 1;
  }

  if (score <= 2) {
    return {
      score,
      label: "Weak",
      color: "#E5484D",
    };
  }

  if (score <= 4) {
    return {
      score,
      label: "Moderate",
      color: "#C8A24A",
    };
  }

  return {
    score,
    label: "Strong",
    color: "#3FB950",
  };
}

export function getPasswordRequirements(
  password: string,
): PasswordRequirement[] {
  return [
    {
      label: "At least 8 characters",
      ok: password.length >= 8,
    },
    {
      label: "Uppercase letter (A-Z)",
      ok: /[A-Z]/.test(password),
    },
    {
      label: "Lowercase letter (a-z)",
      ok: /[a-z]/.test(password),
    },
    {
      label: "Number (0-9)",
      ok: /[0-9]/.test(password),
    },
    {
      label: "Special character (!@#...)",
      ok: /[^A-Za-z0-9]/.test(password),
    },
  ];
}
