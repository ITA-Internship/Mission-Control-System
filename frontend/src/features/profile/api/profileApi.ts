import { apiRequest } from "../../../shared/api/apiClient";

import type { CurrentUser } from "../../../shared/types/accounts";

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
  const fields = {
    first_name: payload.firstName,
    last_name: payload.lastName,
    rank: payload.rank,
    contact: payload.contact,
  };

  if (payload.profilePicture === null) {
    return apiRequest<CurrentUser>(
      "/api/accounts/users/me/",
      {
        method: "PATCH",
        json: {
          ...fields,
          profile_picture: null,
        },
        signal,
      },
    );
  }

  const formData = new FormData();

  Object.entries(fields).forEach(
    ([key, value]) => {
      formData.set(key, value);
    },
  );

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
