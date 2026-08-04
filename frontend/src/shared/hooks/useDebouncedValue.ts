import {
  useEffect,
  useState,
} from "react";

export function useDebouncedValue<T>(
  value: T,
  delayMs = 300,
): T {
  const [debounced, setDebounced] =
    useState(value);

  useEffect(() => {
    if (value === debounced) {
      return;
    }

    const timeout = setTimeout(() => {
      setDebounced(value);
    }, delayMs);

    return () => {
      clearTimeout(timeout);
    };
  }, [value, debounced, delayMs]);

  return debounced;
}
