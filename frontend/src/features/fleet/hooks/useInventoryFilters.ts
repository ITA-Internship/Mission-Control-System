import { useState, useCallback } from "react";
import type { Classification, DroneStatus, SortDir, SortKey } from "../types";

export interface FilterState {
  search: string;
  statusFilter: DroneStatus[];
  classFilter: Classification[];
  sortKey: SortKey;
  sortDir: SortDir;
  page: number;
  pageSize: number;
}

export function useInventoryFilters() {
  const [filters, setFilters] = useState<FilterState>({
    search: "",
    statusFilter: ["ACTIVE"] as DroneStatus[],
    classFilter: [],
    sortKey: "serial_number",
    sortDir: "desc",
    page: 1,
    pageSize: 10,
  });

  const updateSearch = useCallback((search: string) => {
    setFilters((prev) => ({ ...prev, search, page: 1 }));
  }, []);

  const toggleStatus = useCallback((status: DroneStatus) => {
    setFilters((prev) => ({
      ...prev,
      statusFilter: prev.statusFilter.includes(status)
        ? prev.statusFilter.filter((s) => s !== status)
        : [...prev.statusFilter, status],
      page: 1,
    }));
  }, []);

  const toggleClassification = useCallback((classification: Classification) => {
    setFilters((prev) => ({
      ...prev,
      classFilter: prev.classFilter.includes(classification)
        ? prev.classFilter.filter((c) => c !== classification)
        : [...prev.classFilter, classification],
      page: 1,
    }));
  }, []);

  const setSort = useCallback((sortKey: SortKey) => {
    setFilters((prev) => {
      if (prev.sortKey !== sortKey) {
        return { ...prev, sortKey, sortDir: "asc", page: 1 };
      }
      if (prev.sortDir === "asc") {
        return { ...prev, sortDir: "desc", page: 1 };
      }
      return { ...prev, sortDir: "asc", page: 1 };
    });
  }, []);

  const setPage = useCallback((page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  }, []);

  const setPageSize = useCallback((pageSize: number) => {
    setFilters((prev) => ({ ...prev, pageSize, page: 1 }));
  }, []);

  const clearAll = useCallback(() => {
    setFilters({
      search: "",
      statusFilter: ["ACTIVE"] as DroneStatus[],
      classFilter: [],
      sortKey: "serial_number",
      sortDir: "desc",
      page: 1,
      pageSize: 10,
    });
  }, []);

  const isDefaultStatus =
    filters.statusFilter.length === 1 && filters.statusFilter[0] === "ACTIVE";

  const hasFilters =
    Boolean(filters.search) ||
    !isDefaultStatus ||
    filters.classFilter.length > 0;

  return {
    filters,
    updateSearch,
    toggleStatus,
    toggleClassification,
    setSort,
    setPage,
    setPageSize,
    clearAll,
    hasFilters,
  };
}
