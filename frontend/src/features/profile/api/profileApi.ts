import { apiRequest } from "../../auth/api/apiClient";

import type { CurrentUser } from "../../auth/types/auth";

export interface UpdateProfilePayload {
  firstName: string;
  lastName: string;
  rank: string;
  contact: string;
  profilePicture?: File | null;
}

export function updateCurrentUserProfile(
  payload: UpdateProfilePayload,
  signal?: AbortSignal,
): Promise<CurrentUser> {
  const formData = new FormData();

  formData.set("first_name", payload.firstName);
  formData.set("last_name", payload.lastName);
  formData.set("rank", payload.rank);
  formData.set("contact", payload.contact);

  if (payload.profilePicture instanceof File) {
    formData.set(
      "profile_picture",
      payload.profilePicture,
    );
  }

  return apiRequest<CurrentUser>(
    "/api/accounts/users/me/",
    {
      method: "PATCH",
      formData,
      signal,
    },
  );
}
