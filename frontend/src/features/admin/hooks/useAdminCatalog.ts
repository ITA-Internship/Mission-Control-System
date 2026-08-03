import { useCallback } from "react";

import {
  listRoles,
  listUnits,
} from "../api/adminApi";
import { useAsyncData } from "../../../shared/hooks/useAsyncData";

import type { AsyncData } from "../../../shared/hooks/useAsyncData";
import type {
  MilitaryUnit,
  Role,
} from "../types/admin";

export interface AdminCatalog {
  roles: Role[];
  units: MilitaryUnit[];
  /** Set when the roles endpoint failed — role selects degrade instead of the page. */
  rolesError: unknown;
  unitsError: unknown;
}

function createAbortError(): Error {
  const error = new Error(
    "The request was aborted.",
  );

  error.name = "AbortError";

  return error;
}

/**
 * Reference data used by filters and modals across tabs.
 *
 * Roles and units load independently: one missing endpoint must not blank out
 * the whole console, so failures are reported per resource.
 */
export function useAdminCatalog(): AsyncData<AdminCatalog> {
  const load = useCallback(
    async (
      signal: AbortSignal,
    ): Promise<AdminCatalog> => {
      const [rolesResult, unitsResult] =
        await Promise.allSettled([
          listRoles(signal),
          listUnits({}, signal),
        ]);

      if (signal.aborted) {
        throw createAbortError();
      }

      return {
        roles:
          rolesResult.status === "fulfilled"
            ? rolesResult.value
            : [],
        units:
          unitsResult.status === "fulfilled"
            ? unitsResult.value.results
            : [],
        rolesError:
          rolesResult.status === "rejected"
            ? rolesResult.reason
            : null,
        unitsError:
          unitsResult.status === "rejected"
            ? unitsResult.reason
            : null,
      };
    },
    [],
  );

  return useAsyncData(load);
}
