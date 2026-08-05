/**
 * Presentation catalog for the administration console.
 *
 * Role codes mirror `roles.models.ROLE_CODES` and audit action types mirror
 * `accounts.models.AuditLog.ActionType`; anything unknown falls back to a
 * neutral style so a new backend choice never breaks the table.
 */

export interface PillStyle {
  /** Tailwind classes for background, text and (optional) border. */
  className: string;
}

const NEUTRAL_PILL: PillStyle = {
  className:
    "border-mc-muted/35 bg-mc-muted/12 text-mc-muted",
};

export const ROLE_PILL_STYLES: Record<
  string,
  PillStyle
> = {
  ADMIN: {
    className:
      "border-mc-accent/35 bg-mc-accent/15 text-mc-accent",
  },
  COMMANDER: {
    className:
      "border-mc-info/35 bg-mc-info/15 text-mc-info",
  },
  DISPATCHER: {
    className:
      "border-mc-teal/35 bg-mc-teal/15 text-mc-teal",
  },
  OPERATOR: {
    className:
      "border-mc-success/35 bg-mc-success/15 text-mc-success",
  },
  TECHNICIAN: {
    className:
      "border-mc-orange/35 bg-mc-orange/15 text-mc-orange",
  },
  VIEWER: NEUTRAL_PILL,
};

export function getRolePillStyle(
  code: string,
): PillStyle {
  return (
    ROLE_PILL_STYLES[code.toUpperCase()] ??
    NEUTRAL_PILL
  );
}

export const AUDIT_ACTION_TYPES = [
  "LOGIN_SUCCESS",
  "LOGIN_FAILED",
  "LOGOUT",
  "USER_CREATED",
  "ROLE_CHANGED",
  "ACCOUNT_ACTIVATED",
  "ACCOUNT_DEACTIVATED",
  "PROFILE_UPDATED",
  "PASSWORD_CHANGED",
  "PASSWORD_RESET_REQUESTED",
  "PERMISSION_DENIED",
] as const;

const AUDIT_ACTION_TEXT: Record<
  string,
  string
> = {
  LOGIN_SUCCESS: "text-mc-info",
  LOGIN_FAILED: "text-mc-error",
  LOGOUT: "text-mc-muted",
  USER_CREATED: "text-mc-success",
  ROLE_CHANGED: "text-mc-accent",
  ACCOUNT_ACTIVATED: "text-mc-success",
  ACCOUNT_DEACTIVATED: "text-mc-error",
  PROFILE_UPDATED: "text-mc-teal",
  PASSWORD_CHANGED: "text-mc-accent",
  PASSWORD_RESET_REQUESTED: "text-mc-orange",
  PERMISSION_DENIED: "text-mc-error",
};

const AUDIT_ACTION_BACKGROUND: Record<
  string,
  string
> = {
  LOGIN_SUCCESS: "bg-mc-info/12",
  LOGIN_FAILED: "bg-mc-error/12",
  LOGOUT: "bg-mc-muted/12",
  USER_CREATED: "bg-mc-success/12",
  ROLE_CHANGED: "bg-mc-accent/12",
  ACCOUNT_ACTIVATED: "bg-mc-success/12",
  ACCOUNT_DEACTIVATED: "bg-mc-error/12",
  PROFILE_UPDATED: "bg-mc-teal/12",
  PASSWORD_CHANGED: "bg-mc-accent/12",
  PASSWORD_RESET_REQUESTED: "bg-mc-orange/12",
  PERMISSION_DENIED: "bg-mc-error/12",
};

export function getAuditActionStyle(
  actionType: string,
): PillStyle {
  const key = actionType.toUpperCase();

  const text =
    AUDIT_ACTION_TEXT[key] ?? "text-mc-muted";

  const background =
    AUDIT_ACTION_BACKGROUND[key] ??
    "bg-mc-muted/12";

  return {
    className: `${background} ${text}`,
  };
}

export const AUDIT_RESULTS = [
  {
    value: "SUCCESS",
    label: "Success",
  },
  {
    value: "FAILED",
    label: "Failure",
  },
] as const;

export const USER_STATUS_OPTIONS = [
  {
    value: "true",
    label: "Active",
  },
  {
    value: "false",
    label: "Inactive",
  },
] as const;

export const USERS_PAGE_SIZE = 10;
export const AUDIT_PAGE_SIZE = 15;

/** Upper bound used when loading reference data for filters and selects. */
export const CATALOG_PAGE_SIZE = 200;
