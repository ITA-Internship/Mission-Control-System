import { useEffect, useState } from "react";

import {
  fetchActiveOrdersCount,
  fetchOpenDefectsCount,
} from "../api/repairsApi";
import { isAbortError } from "../../../shared/api/apiClient";

export interface RepairsStats {
  openDefects: number | null;
  criticalDefects: number | null;
  activeOrders: number | null;
}

export function useRepairsStats(reloadSignal = 0) {
  const [stats, setStats] = useState<RepairsStats>({
    openDefects: null,
    criticalDefects: null,
    activeOrders: null,
  });

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();

    setIsLoading(true);

    Promise.all([
      fetchOpenDefectsCount({}, controller.signal),
      fetchOpenDefectsCount(
        { severity: "CRITICAL" },
        controller.signal,
      ),
      fetchActiveOrdersCount(controller.signal),
    ])
      .then(([openDefects, criticalDefects, activeOrders]) => {
        setStats({
          openDefects,
          criticalDefects,
          activeOrders,
        });
      })
      .catch((error) => {
        if (isAbortError(error)) return;
        setStats({
          openDefects: null,
          criticalDefects: null,
          activeOrders: null,
        });
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });

    return () => controller.abort();
  }, [reloadSignal]);

  return { stats, isLoading };
}
