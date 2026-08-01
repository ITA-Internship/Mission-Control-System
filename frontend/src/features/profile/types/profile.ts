export type AvatarState =
  | "idle"
  | "dragging"
  | "uploading"
  | "success"
  | "error";

export type ActiveSection =
  | "profile"
  | "avatar"
  | "password"
  | "security";

export type PasswordVisibilityKey =
  | "current"
  | "next"
  | "confirm";

export interface ProfileFormState {
  firstName: string;
  lastName: string;
  rank: string;
  contact: string;
}

export interface PasswordFormState {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export interface PasswordRequirement {
  label: string;
  ok: boolean;
}

export interface PasswordStrength {
  score: number;
  label: string;
  color: string;
}

export interface StatusBanner {
  type: "success" | "error";
  message: string;
}
