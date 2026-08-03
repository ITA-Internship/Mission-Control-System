/* Types backed by the `accounts` app: the signed-in user, roles, and the audit
 * log. Shared because the app shell and every feature page reads them. */

/* Role codes as returned by `GET /api/accounts/users/me/` (`role_code`). */
export type RoleCode =
  | "ADMIN"
  | "COMMANDER"
  | "DISPATCHER"
  | "OPERATOR"
  | "TECHNICIAN"
  | "VIEWER";

export const ROLE_CODES: RoleCode[] = [
  "ADMIN",
  "COMMANDER",
  "DISPATCHER",
  "OPERATOR",
  "TECHNICIAN",
  "VIEWER",
];

export interface CurrentUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  rank: string | null;
  contact: string | null;
  profile_picture: string | null;
  role: number | null;
  role_code: string | null;
  role_name: string | null;
  unit: number | null;
  unit_name?: string | null;
  unit_code?: string | null;
  is_active: boolean;
  must_change_password: boolean;
  /* Only returned by the profile detail representation. */
  last_login?: string | null;
  created_at?: string | null;
  created_by_username?: string | null;
}

/* Nested user representation embedded in other payloads (e.g. a mission
 * commander) — id and name only. */
export interface UserBrief {
  id: number;
  username: string;
  first_name?: string;
  last_name?: string;
}

export interface AuditLogItem {
  id: number;
  actor: number | null;
  actor_username: string | null;
  target_user: number | null;
  target_user_username: string | null;
  action_type: string;
  result: string;
  description: string;
  created_at: string;
}
