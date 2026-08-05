import { useState } from "react";
import { ChevronDown, ArrowUpDown, ChevronUp, ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import type { AuditEntry, AuditAction } from "../types/mediaTypes";
import { AuditActionPill, ResultPill } from "./ui/Pills";

interface AuditLogTableProps {
  logs: AuditEntry[];
  isLoading: boolean;
}

export function AuditLogTable({ logs, isLoading }: AuditLogTableProps) {
  const [actionFilter, setActionFilter] = useState("");
  const [actorFilter, setActorFilter] = useState("");
  const [sortCol, setSortCol] = useState<keyof AuditEntry | null>("timestamp");
  const [sortDir, setSortDir] = useState<"asc" | "desc" | null>("desc");
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 8;

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-[#8A94A6]">
        <Loader2 className="animate-spin mb-4" size={32} />
        <p>Loading audit logs...</p>
      </div>
    );
  }

  function toggleSort(col: keyof AuditEntry) {
    if (sortCol === col) {
      if (sortDir === "desc") setSortDir("asc");
      else if (sortDir === "asc") {
        setSortCol(null);
        setSortDir(null);
      }
    } else {
      setSortCol(col);
      setSortDir("desc");
    }
    setPage(0);
  }

  const actors = Array.from(new Set(logs.map((e) => e.actor))).sort();

  const filtered = logs.filter(
    (e) =>
      (!actionFilter || e.action === actionFilter) &&
      (!actorFilter || e.actor === actorFilter)
  );

  const sorted = [...filtered];
  if (sortCol && sortDir) {
    sorted.sort((a, b) => {
      const av = String(a[sortCol] || "");
      const bv = String(b[sortCol] || "");
      return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
    });
  }

  const total = sorted.length;
  const paged = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const totalPages = Math.ceil(total / PAGE_SIZE);

  type ColDef = { key: keyof AuditEntry; label: string };
  const COLS: ColDef[] = [
    { key: "action", label: "Action" },
    { key: "actor", label: "Actor" },
    { key: "targetMedia", label: "Media" },
    { key: "mission", label: "Mission" },
    { key: "timestamp", label: "Timestamp" },
    { key: "result", label: "Result" },
  ];

  function SortIcon({ col }: { col: keyof AuditEntry }) {
    if (sortCol !== col || !sortDir) {
      return <ArrowUpDown size={11} className="text-[#3A4558]" />;
    }
    return sortDir === "asc"
      ? <ChevronUp size={11} className="text-mc-accent" />
      : <ChevronDown size={11} className="text-mc-accent" />;
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <select
            value={actionFilter}
            onChange={(e) => { setActionFilter(e.target.value); setPage(0); }}
            className="pl-3 pr-7 py-2 rounded-lg bg-[#161D26] border border-[#1E2733] text-sm text-[#8A94A6] focus:outline-none focus:border-mc-accent/40 transition-colors appearance-none cursor-pointer"
          >
            <option value="">All actions</option>
            {(["View", "Download", "Upload", "Update", "Delete", "Denied"] as AuditAction[]).map((a) => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
          <ChevronDown size={12} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#8A94A6] pointer-events-none" />
        </div>

        <div className="relative">
          <select
            value={actorFilter}
            onChange={(e) => { setActorFilter(e.target.value); setPage(0); }}
            className="pl-3 pr-7 py-2 rounded-lg bg-[#161D26] border border-[#1E2733] text-sm text-[#8A94A6] focus:outline-none focus:border-mc-accent/40 transition-colors appearance-none cursor-pointer"
          >
            <option value="">All actors</option>
            {actors.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
          <ChevronDown size={12} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#8A94A6] pointer-events-none" />
        </div>

        <span className="text-xs text-[#8A94A6] ml-auto">
          {total} {total === 1 ? "entry" : "entries"}
        </span>
      </div>

      {/* Table */}
      <div className="bg-[#161D26] border border-[#1E2733] rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[780px] text-sm">
            <thead>
              <tr className="border-b border-[#1E2733]">
                {COLS.map((col) => (
                  <th
                    key={col.key}
                    onClick={() => toggleSort(col.key)}
                    className="px-4 py-3 text-left text-[10px] font-semibold text-[#8A94A6] uppercase tracking-[0.1em] cursor-pointer hover:text-[#E6EAF0] select-none group transition-colors"
                  >
                    <div className="flex items-center gap-1.5">
                      {col.label}
                      <SortIcon col={col.key} />
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {paged.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-sm text-[#8A94A6]">
                    No audit entries match the current filters.
                  </td>
                </tr>
              ) : paged.map((entry) => {
                const flagged = entry.action === "Denied" || entry.result === "Denied";
                return (
                  <tr
                    key={entry.id}
                    className={`border-b border-[#1E2733]/40 transition-colors ${
                      flagged
                        ? "bg-red-500/5 hover:bg-red-500/8"
                        : "hover:bg-white/[0.018]"
                    }`}
                  >
                    <td className="px-4 py-3">
                      <AuditActionPill action={entry.action} />
                    </td>
                    <td className="px-4 py-3 text-[#E6EAF0] text-sm">{entry.actor}</td>
                    <td className="px-4 py-3">
                      <div className="max-w-[200px]">
                        <p className="text-[#E6EAF0] text-sm truncate">{entry.targetMedia}</p>
                        <p className="text-xs text-[#8A94A6] font-mono mt-0.5">{entry.targetId}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-[#8A94A6] whitespace-nowrap">{entry.mission}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-[#8A94A6] font-mono whitespace-nowrap">{entry.timestamp}</span>
                    </td>
                    <td className="px-4 py-3">
                      <ResultPill result={entry.result} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-4 py-3 border-t border-[#1E2733] flex items-center justify-between">
            <span className="text-xs text-[#8A94A6]">
              {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} of {total}
            </span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="p-1.5 rounded-lg hover:bg-white/5 text-[#8A94A6] hover:text-[#E6EAF0] disabled:opacity-25 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft size={14} />
              </button>
              {Array.from({ length: totalPages }, (_, i) => (
                <button
                  key={i}
                  onClick={() => setPage(i)}
                  className={`w-7 h-7 rounded-lg text-xs font-medium transition-colors ${
                    i === page
                      ? "bg-mc-accent/15 text-mc-accent"
                      : "text-[#8A94A6] hover:bg-white/5 hover:text-[#E6EAF0]"
                  }`}
                >
                  {i + 1}
                </button>
              ))}
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="p-1.5 rounded-lg hover:bg-white/5 text-[#8A94A6] hover:text-[#E6EAF0] disabled:opacity-25 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
