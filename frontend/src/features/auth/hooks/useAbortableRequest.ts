import {
  useCallback,
  useEffect,
  useRef,
} from "react";

export function useAbortableRequest() {
  const controllerRef =
    useRef<AbortController | null>(null);

  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;

    return () => {
      mountedRef.current = false;
      controllerRef.current?.abort();
    };
  }, []);

  const run = useCallback(
    async function runRequest<T>(
      request: (
        signal: AbortSignal,
      ) => Promise<T>,
    ): Promise<T> {
      controllerRef.current?.abort();

      const controller =
        new AbortController();

      controllerRef.current = controller;

      try {
        return await request(
          controller.signal,
        );
      } finally {
        if (
          controllerRef.current === controller
        ) {
          controllerRef.current = null;
        }
      }
    },
    [],
  );

  const isMounted = useCallback(
    () => mountedRef.current,
    [],
  );

  return {
    run,
    isMounted,
  };
}