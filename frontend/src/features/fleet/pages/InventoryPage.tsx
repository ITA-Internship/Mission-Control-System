import { useState, useEffect } from "react";
import {
  ArrowLeft,
  ArrowRight,
  CheckSquare,
  ChevronDown,
  ChevronUp,
  ChevronsUpDown,
  GitCompare,
  Minus,
  Plus,
  Square,
  Upload,
  Download,
} from "lucide-react";

import { AppShell } from "../../../components/layout/AppShell";
import { CompareModal } from "../components/CompareModal";
import { DroneDrawer } from "../components/DroneDrawer";
import { ImportModal } from "../components/ImportModal";
import { FilterSection } from "../components/FilterSection";
import { DroneRow } from "../components/DroneRow";
import { useInventoryFilters } from "../hooks/useInventoryFilters";
import { STATUS_UI } from "../utils/constants";
import { EmptyState, Skeleton } from "../../../shared/components/states";

import { fetchDrones } from "../api/dronesApi";

import type {
  DrawerMode,
  Drone,
  SortDir,
  SortKey,
} from "../types";

function SortIcon({ dir }: { dir: SortDir }) {
  if (!dir) return <ChevronsUpDown size={12} className="text-[#8A94A6]" />;
  if (dir === "asc") return <ChevronUp size={12} className="text-[#C8A24A]" />;
  return <ChevronDown size={12} className="text-[#C8A24A]" />;
}

function SkeletonRow() {
  return (
    <tr className="border-b border-white/5">
      {[...Array(9)].map((_, index) => (
        <td key={index} className="px-3 py-[11px]">
          <Skeleton className="h-3 w-full opacity-40" />
        </td>
      ))}
    </tr>
  );
}

export function InventoryPage() {
  const [drones, setDrones] = useState<Drone[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Set<string | number>>(new Set());

  const {
    filters,
    updateSearch,
    toggleStatus,
    toggleClassification,
    setSort,
    setPage,
    setPageSize,
    clearAll,
    hasFilters,
  } = useInventoryFilters();

  const [statusOpen, setStatusOpen] = useState(false);
  const [classOpen, setClassOpen] = useState(false);
  const [activeKebab, setActiveKebab] = useState<string | number | null>(null);

  const [drawer, setDrawer] = useState<{
    open: boolean;
    mode: DrawerMode;
    drone?: Drone;
  }>({ open: false, mode: "add" });
  const [importOpen, setImportOpen] = useState(false);
  const [compareOpen, setCompareOpen] = useState(false);

  const handleExport = async () => {
    try {
      const queryParams = new URLSearchParams();

      if (filters.search) queryParams.append("search", filters.search);

      if (filters.statusFilter.length > 0) {
        filters.statusFilter.forEach(s => queryParams.append("status", s));
      }

      if (filters.classFilter.length > 0) {
        filters.classFilter.forEach(c => queryParams.append("classification", c));
      }

      if (filters.sortDir && filters.sortKey) {
        const ordering = filters.sortDir === "desc" ? `-${filters.sortKey}` : filters.sortKey;
        queryParams.append("ordering", ordering);
      }

      const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
      const exportUrl = `${API_URL}/drones/export/?${queryParams.toString()}`;

      const response = await fetch(exportUrl, {
        method: "GET",
        credentials: "include",
      });

      if (!response.ok) throw new Error("Failed to export data");

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = "drones_export.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error("Export error:", error);
      alert("Не вдалося експортувати дані.");
    }
  };

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    const delayDebounceFn = setTimeout(() => {
      let ordering = "";
      if (filters.sortDir && filters.sortKey) {
        ordering = filters.sortDir === "desc" ? `-${filters.sortKey}` : filters.sortKey;
      }

      const statusParam =
        filters.statusFilter.length > 0 ? filters.statusFilter : undefined;
      const classParam =
        filters.classFilter.length > 0 ? filters.classFilter : undefined;

      fetchDrones({
        page: filters.page,
        pageSize: filters.pageSize,
        search: filters.search,
        status: statusParam,
        classification: classParam,
        ordering,
      })
        .then((data: any) => {
          if (isMounted) {
            const fetchedDrones = Array.isArray(data?.results)
              ? data.results
              : (Array.isArray(data) ? data : []);

            setDrones(fetchedDrones);
            setTotalCount(data?.count || fetchedDrones.length);
            setLoading(false);
          }
        })
        .catch((err) => {
          if (isMounted) {
            console.error("Помилка завантаження дронів:", err);
            setLoading(false);
          }
        });
    }, 400);

    return () => {
      isMounted = false;
      clearTimeout(delayDebounceFn);
    };
  }, [filters]);

  const totalPages = Math.ceil(totalCount / filters.pageSize);
  const pageStart = (filters.page - 1) * filters.pageSize;

  const statusCounts = (drones || []).reduce((acc, drone) => {
    acc[drone.status] = (acc[drone.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const selectedDrones = drones.filter((drone) => selected.has(drone.id));

  const colHeader = (label: string, key: SortKey, cls = "") => (
    <th
      className={`group cursor-pointer px-3 py-2.5 text-left text-[11px] font-medium uppercase tracking-wider text-[#8A94A6] select-none hover:text-[#E6EAF0] ${cls}`}
      onClick={() => setSort(key)}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        <SortIcon dir={filters.sortKey === key ? filters.sortDir : null} />
      </span>
    </th>
  );

  const toggleSelect = (id: string | number) => {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selected.size === drones.length && drones.length > 0) {
      setSelected(new Set());
      return;
    }
    setSelected(new Set(drones.map((row) => row.id)));
  };

  return (
    <AppShell>
      <main className="flex-1 overflow-auto">
        <div className="space-y-4 p-5">
          {/* Header Section */}
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-[22px] font-semibold tracking-tight text-[#E6EAF0]">
                Drone Inventory
              </h1>
              <p className="mt-0.5 text-[13px] text-[#8A94A6]">
                <span className="font-semibold text-[#C8A24A]">{totalCount}</span>{" "}
                drones found in database
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-end gap-2">
              <button
                onClick={() => setImportOpen(true)}
                className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-[12px] text-[#8A94A6] transition-all hover:bg-white/8 hover:text-[#E6EAF0]"
              >
                <Upload size={13} />
                Import CSV
              </button>
              <button
                onClick={handleExport}
                className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-[12px] text-[#8A94A6] transition-all hover:bg-white/8 hover:text-[#E6EAF0]"
              >
                <Download size={13} />
                Export CSV
              </button>
              <button
                onClick={() => selected.size >= 2 && setCompareOpen(true)}
                disabled={selected.size < 2}
                className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-[12px] text-[#8A94A6] transition-all hover:bg-white/8 hover:text-[#E6EAF0] disabled:cursor-not-allowed disabled:opacity-40"
              >
                <GitCompare size={13} />
                Compare{selected.size >= 2 ? ` (${selected.size})` : ""}
              </button>
              <button
                onClick={() => setDrawer({ open: true, mode: "add" })}
                className="flex items-center gap-1.5 rounded-lg bg-[#C8A24A] px-3 py-1.5 text-[12px] font-semibold text-[#0B0F14] transition-colors hover:bg-[#d4ae5c]"
              >
                <Plus size={13} />
                Add Drone
              </button>
            </div>
          </div>

          {/* Filters Section */}
          <FilterSection
            search={filters.search}
            onSearchChange={updateSearch}
            statusFilter={filters.statusFilter}
            onStatusToggle={toggleStatus}
            statusOpen={statusOpen}
            onStatusOpenChange={setStatusOpen}
            classFilter={filters.classFilter}
            onClassificationToggle={toggleClassification}
            classOpen={classOpen}
            onClassOpenChange={setClassOpen}
            hasFilters={hasFilters}
            onClearAll={clearAll}
          />

          {/* Table Section */}
          <div className="overflow-hidden rounded-xl border border-white/8 bg-[#161D26]">
            <div className="overflow-auto" style={{ maxHeight: "calc(100vh - 340px)" }}>
              <table className="w-full border-collapse text-[13px]">
                <thead className="sticky top-0 z-10">
                  <tr className="border-b border-white/8 bg-[#1C2535]">
                    <th className="w-9 px-3 py-2.5">
                      <button
                        onClick={toggleSelectAll}
                        className="text-[#8A94A6] transition-colors hover:text-[#C8A24A]"
                      >
                        {selected.size > 0 && selected.size < drones.length ? (
                          <Minus size={13} />
                        ) : selected.size === drones.length && drones.length > 0 ? (
                          <CheckSquare size={13} className="text-[#C8A24A]" />
                        ) : (
                          <Square size={13} />
                        )}
                      </button>
                    </th>
                    {colHeader("Serial / Inv #", "serial_number", "min-w-[160px]")}
                    {colHeader("Name", "name", "min-w-[140px]")}
                    {colHeader("Class", "classification", "min-w-[110px]")}
                    {colHeader("Status", "status", "min-w-[120px]")}
                    <th className="px-3 py-2.5 text-left text-[11px] font-medium uppercase tracking-wider text-[#8A94A6]">Military Unit</th>
                    <th className="w-10 px-3 py-2.5" />
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    [...Array(filters.pageSize)].map((_, index) => <SkeletonRow key={index} />)
                  ) : drones.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-6 py-16">
                        <div className="flex flex-col items-center">
                          <EmptyState
                            title="No drones match these filters"
                            description="Try adjusting your search or filters"
                          />
                          <button
                            onClick={clearAll}
                            className="mt-2 text-[12px] text-[#C8A24A] hover:underline"
                          >
                            Clear all filters
                          </button>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    drones.map((drone, index) => (
                      <DroneRow
                        key={drone.id}
                        drone={drone}
                        isSelected={selected.has(drone.id)}
                        isEven={index % 2 === 0}
                        activeKebab={activeKebab}
                        onToggleSelect={toggleSelect}
                        onToggleKebab={(id) =>
                          setActiveKebab((current) =>
                            current === id ? null : id,
                          )
                        }
                        onEdit={(drone) =>
                          setDrawer({ open: true, mode: "edit", drone })
                        }
                        onCompare={() => {}}
                        onWriteOff={() => {}}
                      />
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="flex items-center justify-between border-t border-white/8 bg-[#161D26] px-4 py-3">
              <div className="flex items-center gap-3 text-[12px] text-[#8A94A6]">
                <span>Rows per page:</span>
                <select
                  value={filters.pageSize}
                  onChange={(event) => setPageSize(Number(event.target.value))}
                  className="rounded-lg border border-white/10 bg-[#0F1620] px-2 py-1 text-[12px] text-[#E6EAF0] focus:outline-none focus:ring-1 focus:ring-[#C8A24A]/40"
                >
                  {[10, 25, 50].map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-4 text-[12px]">
                <span className="text-[#8A94A6]">
                  Showing{" "}
                  <span className="font-medium text-[#E6EAF0]">
                    {Math.min(pageStart + 1, totalCount > 0 ? totalCount : 0)}–{Math.min(pageStart + drones.length, totalCount)}
                  </span>{" "}
                  of <span className="font-medium text-[#E6EAF0]">{totalCount}</span>
                </span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setPage(Math.max(1, filters.page - 1))}
                    disabled={filters.page === 1}
                    className="rounded-lg border border-white/10 p-1.5 text-[#8A94A6] transition-all hover:bg-white/5 hover:text-[#E6EAF0] disabled:cursor-not-allowed disabled:opacity-30"
                  >
                    <ArrowLeft size={13} />
                  </button>
                  {[...Array(Math.min(totalPages, 7))].map((_, index) => {
                    const currentPage = index + 1;
                    return (
                      <button
                        key={currentPage}
                        onClick={() => setPage(currentPage)}
                        className={`h-7 w-7 rounded-lg text-[12px] font-medium transition-all ${
                          currentPage === filters.page
                            ? "bg-[#C8A24A] text-[#0B0F14]"
                            : "border border-white/10 text-[#8A94A6] hover:bg-white/5 hover:text-[#E6EAF0]"
                        }`}
                      >
                        {currentPage}
                      </button>
                    );
                  })}
                  <button
                    onClick={() => setPage(Math.min(totalPages, filters.page + 1))}
                    disabled={filters.page >= totalPages || totalPages === 0}
                    className="rounded-lg border border-white/10 p-1.5 text-[#8A94A6] transition-all hover:bg-white/5 hover:text-[#E6EAF0] disabled:cursor-not-allowed disabled:opacity-30"
                  >
                    <ArrowRight size={13} />
                  </button>
                </div>
              </div>
            </div>
            {/* Status Counts Footer */}
            <div className="flex flex-wrap items-center gap-4 border-t border-white/8 bg-[#1C2535] px-4 py-3 text-[12px]">
              {Object.entries(STATUS_UI).map(([statusKey, config]) => (
                <div key={statusKey} className="flex items-center gap-1.5 text-[#8A94A6]">
                  <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${config.dot}`} />
                  <span>{config.label}:</span>
                  <span className="font-semibold text-[#E6EAF0]">
                    {statusCounts[statusKey] || 0}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      {(statusOpen || classOpen || activeKebab) && (
        <div
          className="fixed inset-0 z-20"
          onClick={() => {
            setStatusOpen(false);
            setClassOpen(false);
            setActiveKebab(null);
          }}
        />
      )}

      {drawer.open && (
        <DroneDrawer
          mode={drawer.mode}
          drone={drawer.drone}
          onClose={() => setDrawer((current) => ({ ...current, open: false }))}
          onSave={(savedDrone) => {
            if (drawer.mode === "add") {
              setDrones((current) => [savedDrone, ...current]);
              setTotalCount((current) => current + 1);
            } else {
              setDrones((current) =>
                current.map((d) => (d.id === savedDrone.id ? savedDrone : d))
              );
            }
          }}
        />
      )}
      {importOpen && <ImportModal onClose={() => setImportOpen(false)} />}
      {compareOpen && selectedDrones.length >= 2 && (
        <CompareModal
          drones={selectedDrones.slice(0, 4)}
          onClose={() => setCompareOpen(false)}
        />
      )}
    </AppShell>
  );
}