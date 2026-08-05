import type {
  AdminUser,
  AuditLogEntry,
  AuditResult,
  MilitaryUnit,
  Page,
  Role,
} from "../types/admin";

/**
 * Defensive readers for API payloads.
 *
 * The administration console consumes several endpoints whose serializers may
 * return related objects either expanded (`{"id": 3, "code": "ADMIN"}`) or as
 * bare primary keys. Parsing here keeps every table cell renderable instead of
 * letting a shape mismatch blank out the page.
 */

export type Reference<T> = number | T | null;

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function readString(
  source: Record<string, unknown>,
  key: string,
): string {
  const value = source[key];

  return typeof value === "string" ? value : "";
}

function readNullableString(
  source: Record<string, unknown>,
  key: string,
): string | null {
  const value = source[key];

  return typeof value === "string" && value
    ? value
    : null;
}

function readNumber(
  source: Record<string, unknown>,
  key: string,
): number | null {
  const value = source[key];

  if (typeof value === "number") {
    return value;
  }

  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);

    return Number.isFinite(parsed)
      ? parsed
      : null;
  }

  return null;
}

function readBoolean(
  source: Record<string, unknown>,
  key: string,
  fallback: boolean,
): boolean {
  const value = source[key];

  return typeof value === "boolean"
    ? value
    : fallback;
}

/** Unwrap a DRF page, a bare array, or an unexpected payload. */
export function parsePage<T>(
  payload: unknown,
  parseItem: (value: unknown) => T | null,
): Page<T> {
  const rawResults = Array.isArray(payload)
    ? payload
    : isRecord(payload) &&
        Array.isArray(payload.results)
      ? payload.results
      : [];

  const results = rawResults
    .map(parseItem)
    .filter(
      (item): item is T => item !== null,
    );

  const count =
    isRecord(payload) &&
    typeof payload.count === "number"
      ? payload.count
      : results.length;

  return {
    count,
    results,
  };
}

export function parseRole(
  value: unknown,
): Role | null {
  if (!isRecord(value)) {
    return null;
  }

  const id = readNumber(value, "id");

  if (id === null) {
    return null;
  }

  const code = readString(value, "code");
  const name = readString(value, "name");

  return {
    id,
    code: code || name || `Role ${id}`,
    name: name || code || `Role ${id}`,
  };
}

export function parseUnit(
  value: unknown,
): MilitaryUnit | null {
  if (!isRecord(value)) {
    return null;
  }

  const id = readNumber(value, "id");

  if (id === null) {
    return null;
  }

  return {
    id,
    name: readString(value, "name"),
    code: readString(value, "code"),
    description: readString(
      value,
      "description",
    ),
    is_active: readBoolean(
      value,
      "is_active",
      true,
    ),
    drone_count:
      readNumber(value, "drone_count") ??
      readNumber(value, "drones_count"),
    user_count:
      readNumber(value, "user_count") ??
      readNumber(value, "users_count"),
  };
}

export interface ParsedUser
  extends Omit<AdminUser, "role" | "unit"> {
  role: Reference<Role>;
  unit: Reference<MilitaryUnit>;
}

function parseReference<T>(
  value: unknown,
  parse: (input: unknown) => T | null,
): Reference<T> {
  if (typeof value === "number") {
    return value;
  }

  return parse(value);
}

function parseActorName(
  source: Record<string, unknown>,
): string | null {
  const direct =
    readNullableString(
      source,
      "created_by_username",
    ) ?? readNullableString(source, "created_by");

  if (direct) {
    return direct;
  }

  const nested = source.created_by;

  if (isRecord(nested)) {
    return (
      readNullableString(nested, "username") ??
      readNullableString(nested, "email")
    );
  }

  return null;
}

export function parseUser(
  value: unknown,
): ParsedUser | null {
  if (!isRecord(value)) {
    return null;
  }

  const id = readNumber(value, "id");

  if (id === null) {
    return null;
  }

  const username = readString(
    value,
    "username",
  );

  const firstName = readString(
    value,
    "first_name",
  );

  const lastName = readString(
    value,
    "last_name",
  );

  const fullName =
    [firstName, lastName]
      .filter(Boolean)
      .join(" ")
      .trim() || username;

  return {
    id,
    username,
    email: readString(value, "email"),
    first_name: firstName,
    last_name: lastName,
    full_name: fullName,
    role: parseReference(
      value.role,
      parseRole,
    ),
    unit: parseReference(
      value.unit,
      parseUnit,
    ),
    is_active: readBoolean(
      value,
      "is_active",
      true,
    ),
    created_by: parseActorName(value),
    last_login: readNullableString(
      value,
      "last_login",
    ),
  };
}

/** Turn primary-key references into the objects loaded for filters/selects. */
export function resolveUser(
  user: ParsedUser,
  roles: Role[],
  units: MilitaryUnit[],
): AdminUser {
  const role =
    typeof user.role === "number"
      ? (roles.find(
          (item) => item.id === user.role,
        ) ?? null)
      : user.role;

  const unit =
    typeof user.unit === "number"
      ? (units.find(
          (item) => item.id === user.unit,
        ) ?? null)
      : user.unit;

  return {
    ...user,
    role,
    unit,
  };
}

export function parseAuditEntry(
  value: unknown,
): AuditLogEntry | null {
  if (!isRecord(value)) {
    return null;
  }

  const id = readNumber(value, "id");

  if (id === null) {
    return null;
  }

  const result = readString(value, "result");

  return {
    id,
    actor: readNumber(value, "actor"),
    actor_username: readNullableString(
      value,
      "actor_username",
    ),
    target_user: readNumber(
      value,
      "target_user",
    ),
    target_user_username: readNullableString(
      value,
      "target_user_username",
    ),
    action_type: readString(
      value,
      "action_type",
    ),
    result: (result === "FAILED"
      ? "FAILED"
      : "SUCCESS") as AuditResult,
    description: readString(
      value,
      "description",
    ),
    ip_address: readNullableString(
      value,
      "ip_address",
    ),
    user_agent: readString(
      value,
      "user_agent",
    ),
    created_at: readString(
      value,
      "created_at",
    ),
  };
}
