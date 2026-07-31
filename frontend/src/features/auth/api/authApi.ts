import { apiRequest } from "./apiClient";

import type {
  CurrentUser,
  DetailResponse,
} from "../types/auth";

export function requestPasswordReset(
  email: string,
  signal?: AbortSignal,
): Promise<DetailResponse> {
  return apiRequest<DetailResponse>(
    "/api/accounts/users/password-reset/",
    {
      method: "POST",
      json: {
        email,
      },
      signal,
    },
  );
}

export function signIn(
  identifier: string,
  password: string,
  signal?: AbortSignal,
): Promise<CurrentUser> {
  return apiRequest<CurrentUser>(
    "/api/accounts/login/",
    {
      method: "POST",
      json: {
        identifier,
        password,
      },
      signal,
    },
  );
}

export function confirmPasswordReset(
  uid: string,
  token: string,
  newPassword: string,
  signal?: AbortSignal,
): Promise<DetailResponse> {
  const encodedUid = encodeURIComponent(uid);
  const encodedToken =
    encodeURIComponent(token);

  return apiRequest<DetailResponse>(
    `/api/accounts/users/password-reset-confirm/${encodedUid}/${encodedToken}/`,
    {
      method: "POST",
      json: {
        new_password: newPassword,
      },
      signal,
    },
  );
}

export function activateAccount(
  userId: string,
  token: string,
  password: string,
  signal?: AbortSignal,
): Promise<DetailResponse> {
  const encodedUserId =
    encodeURIComponent(userId);

  const encodedToken =
    encodeURIComponent(token);

  return apiRequest<DetailResponse>(
    `/api/accounts/activate/${encodedUserId}/${encodedToken}/`,
    {
      method: "POST",
      json: {
        password,
      },
      signal,
    },
  );
}

export function getCurrentUser(
  signal?: AbortSignal,
): Promise<CurrentUser> {
  return apiRequest<CurrentUser>(
    "/api/accounts/users/me/",
    {
      signal,
    },
  );
}

export function changePassword(
  oldPassword: string,
  newPassword: string,
  signal?: AbortSignal,
): Promise<DetailResponse> {
  return apiRequest<DetailResponse>(
    "/api/accounts/users/me/change-password/",
    {
      method: "POST",
      json: {
        old_password: oldPassword,
        new_password: newPassword,
      },
      signal,
    },
  );
}
