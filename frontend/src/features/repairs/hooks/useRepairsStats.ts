import { useEffect, useState } from "react";

import {
  fetchActiveOrdersCount,
  fetchOpenDefectsCount,
} from "../api/repairsApi";
import { isAbortError } from "../../../shared/api/apiClient";
import { useAbortableRequest } from "../../../shared/hooks/useAbortableRequest";

export interface RepairsStats {
  openDefects: number | null;
  criticalDefects: number | null;
  activeOrders: number | null;
}

export function useRepairsStats(reloadSignal = 0) {
  const { run } = useAbortableRequest();

  const [stats, setStats] = useState<RepairsStats>({
    openDefects: null,
    criticalDefects: null,
    activeOrders: null,
  });

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    void run(async (signal) => {
      setIsLoading(true);
      try {
        const [openDefects, criticalDefects, activeOrders] =
          await Promise.all([
            fetchOpenDefectsCount({}, signal),
            fetchOpenDefectsCount(
              { severity: "CRITICAL" },
              signal,
            ),
            fetchActiveOrdersCount(signal),
          ]);

        setStats({
          openDefects,
          criticalDefects,
          activeOrders,
        });
      } catch (error) {
        if (isAbortError(error)) return;
        setStats({
          openDefects: null,
          criticalDefects: null,
          activeOrders: null,
        });
      } finally {
        if (!signal.aborted) {
          setIsLoading(false);
        }
      }
    });
  }, [reloadSignal, run]);

  return { stats, isLoading };
}
