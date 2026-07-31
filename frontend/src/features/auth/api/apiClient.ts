/**
 * Backwards-compatible re-export.
 *
 * The API client now lives in `src/shared/api/apiClient.ts` so it can be
 * shared across features. This module is kept so existing auth imports
 * (`../api/apiClient`) continue to work.
 */
export {
  ApiError,
  NetworkError,
  apiRequest,
  isAbortError,
} from "../../../shared/api/apiClient";
