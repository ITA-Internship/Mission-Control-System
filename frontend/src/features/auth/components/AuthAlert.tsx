/* AuthAlert is retained as a backward-compatible alias for the shared Alert so
 * existing auth call sites keep their import path. New code should import
 * `Alert` from `shared/components/Alert` directly. */
import { Alert } from "../../../shared/components/Alert";
import type { AlertVariant } from "../../../shared/components/Alert";

export type AuthAlertVariant = AlertVariant;
export const AuthAlert = Alert;
