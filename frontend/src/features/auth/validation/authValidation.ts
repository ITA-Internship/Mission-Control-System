const EMAIL_PATTERN =
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateEmail(
  value: string,
): string | undefined {
  const email = value.trim();

  if (!email) {
    return "Email is required.";
  }

  if (!EMAIL_PATTERN.test(email)) {
    return "Enter a valid email address.";
  }

  return undefined;
}

export function validateRequiredPassword(
  value: string,
  label: string,
): string | undefined {
  if (value.length === 0) {
    return `${label} is required.`;
  }

  return undefined;
}

export function validatePasswordConfirmation(
  newPassword: string,
  confirmPassword: string,
): string | undefined {
  if (confirmPassword.length === 0) {
    return "Confirm new password is required.";
  }

  if (newPassword !== confirmPassword) {
    return "Passwords do not match.";
  }

  return undefined;
}

export function hasResetRouteParams(
  uid: string | undefined,
  token: string | undefined,
): boolean {
  return Boolean(
    uid?.trim() &&
      token?.trim(),
  );
}

export function hasActivationRouteParams(
  userId: string | undefined,
  token: string | undefined,
): boolean {
  return Boolean(
    userId &&
      /^[1-9]\d*$/.test(userId) &&
      token?.trim(),
  );
}
