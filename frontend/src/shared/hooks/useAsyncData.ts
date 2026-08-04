import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import { isAbortError } from "../api/apiClient";

interface AsyncDataResult<T> {
  data: T | null;
  error: unknown;
  /** Identity of the request this result came from. */
  requestKey: object | null;
}

export interface AsyncData<T> {
  data: T | null;
  error: unknown;
  isLoading: boolean;
  reload: () => void;
  mutate: (data: T | ((prev: T | null) => T)) => void;
}

/**
 * Run an abortable loader and expose its lifecycle to the UI.
 *
 * `load` must be memoized by the caller (`useCallback`) because it is the
 * effect dependency: a new identity refetches, a stable one does not.
 *
 * Loading is derived by comparing the pending request identity with the one
 * the current result belongs to, so no state is written while the effect runs.
 */
export function useAsyncData<T>(
  load: (signal: AbortSignal) => Promise<T>,
): AsyncData<T> {
  const [reloadToken, setReloadToken] =
    useState(0);

  const [result, setResult] = useState<
    AsyncDataResult<T>
  >({
    data: null,
    error: null,
    requestKey: null,
  });

  const requestKey = useMemo(
    () => ({
      load,
      reloadToken,
    }),
    [load, reloadToken],
  );

  const reload = useCallback(() => {
    setReloadToken(
      (token) => token + 1,
    );
  }, []);

  const mutate = useCallback((updater: T | ((prev: T | null) => T)) => {
    setResult((prev) => {
      const nextData = typeof updater === "function" ? (updater as (prev: T | null) => T)(prev.data) : updater;
      return { ...prev, data: nextData };
    });
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    let isActive = true;

    requestKey
      .load(controller.signal)
      .then((data) => {
        if (!isActive) {
          return;
        }

        setResult({
          data,
          error: null,
          requestKey,
        });
      })
      .catch((error: unknown) => {
        if (
          !isActive ||
          isAbortError(error)
        ) {
          return;
        }

        setResult({
          data: null,
          error,
          requestKey,
        });
      });

    return () => {
      isActive = false;
      controller.abort();
    };
  }, [requestKey]);

  return {
    data: result.data,
    error: result.error,
    isLoading:
      result.requestKey !== requestKey,
    reload,
    mutate,
  };
}
