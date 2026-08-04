import { useState, useMemo } from "react";
import { AlertTriangle, ChevronDown, ChevronUp, ChevronsUpDown, Eye, Navigation, ChevronLeft, ChevronRight } from "lucide-react";
import type { Mission } from "../types";
import { ResultPill, StatusPill } from "./Pills";

type SortKey = keyof Mission;
type SortDir = "asc" | "desc";

export function DataTable({
  missions,
  onOpen,
}: {
  missions: Mission[];
  onOpen: (m: Mission) => void;
}) {
  const [sortKey, setSortKey] = useState<SortKey | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [selected, setSelected] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const perPage = 15;

  const sorted = useMemo(() => {
    if (!sortKey) return [...missions];
    return [...missions].sort((a, b) => {
      const av = a[sortKey] ?? "";
      const bv = b[sortKey] ?? "";
      if (av < bv) return sortDir === "asc" ? -1 : 1;
      if (av > bv) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
  }, [missions, sortKey, sortDir]);

  const totalPages = Math.ceil(sorted.length / perPage) || 1;
  const pageData = sorted.slice((page - 1) * perPage, page * perPage);

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      if (sortDir === "asc") {
        setSortDir("desc");
      } else {
        setSortKey(null);
        setSortDir("asc");
      }
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  function renderSortIcon(col: SortKey) {
    if (sortKey !== col) return <ChevronsUpDown size={11} className="text-[#3a4455]" />;
    return sortDir === "asc" ? <ChevronUp size={11} className="text-[#C8A24A]" /> : <ChevronDown size={11} className="text-[#C8A24A]" />;
  }

  const thClass = "px-4 py-3 text-left text-[10px] font-mono font-medium tracking-widest text-[#8A94A6] select-none cursor-pointer hover:text-[#E6EAF0] transition-colors whitespace-nowrap";

  return (
    <div className="flex flex-col gap-3">
      <div
        className="rounded-xl overflow-hidden border border-white/[0.07]"
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px]">
            <thead>
              <tr className="bg-[#0F1621] border-b border-white/[0.07]">
                <th className={thClass} onClick={() => handleSort("title")}>
                  <div className="flex items-center gap-1.5">MISSION {renderSortIcon("title")}</div>
                </th>
                <th className={thClass} onClick={() => handleSort("status")}>
                  <div className="flex items-center gap-1.5">STATUS {renderSortIcon("status")}</div>
                </th>
                <th className={thClass} onClick={() => handleSort("commander")}>
                  <div className="flex items-center gap-1.5">COMMANDER {renderSortIcon("commander")}</div>
                </th>
                <th className={thClass} onClick={() => handleSort("location")}>
                  <div className="flex items-center gap-1.5">LOCATION {renderSortIcon("location")}</div>
                </th>
                <th className={thClass} onClick={() => handleSort("startedAt")}>
                  <div className="flex items-center gap-1.5">STARTED {renderSortIcon("startedAt")}</div>
                </th>
                <th className={thClass} onClick={() => handleSort("endedAt")}>
                  <div className="flex items-center gap-1.5">ENDED {renderSortIcon("endedAt")}</div>
                </th>
                <th className={thClass} onClick={() => handleSort("result")}>
                  <div className="flex items-center gap-1.5">RESULT {renderSortIcon("result")}</div>
                </th>
                <th className={thClass} onClick={() => handleSort("droneCount")}>
                  <div className="flex items-center gap-1.5">DRONES {renderSortIcon("droneCount")}</div>
                </th>
                <th className="px-4 py-3 text-left text-[10px] font-mono font-medium tracking-widest text-[#8A94A6]">ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {pageData.length === 0 ? (
                <tr>
                  <td colSpan={9}>
                    <div className="flex flex-col items-center justify-center py-16 gap-3">
                      <AlertTriangle size={24} color="#8A94A6" />
                      <div className="text-[13px] font-mono text-[#8A94A6]">No missions match your filters</div>
                    </div>
                  </td>
                </tr>
              ) : (
                pageData.map((mission) => {
                  const isSelected = selected === mission.id;
                  return (
                    <tr
                      key={mission.id}
                      onClick={() => setSelected(isSelected ? null : mission.id)}
                      className={`cursor-pointer transition-colors duration-100 border-b border-white/[0.04] ${
                        isSelected
                          ? "bg-[#C8A24A]/[0.08]"
                          : "even:bg-[#161D26] odd:bg-[#131920] hover:bg-white/[0.03]"
                      }`}
                    >
                      <td className="px-4 py-3">
                        <div>
                          <div className="text-[10px] font-mono text-[#8A94A6]">{mission.id}</div>
                          <div className="text-[13px] font-semibold text-[#E6EAF0] tracking-wide">{mission.title}</div>
                        </div>
                      </td>
                      <td className="px-4 py-3"><StatusPill status={mission.status} /></td>
                      <td className="px-4 py-3 text-[12px] font-mono text-[#8A94A6] whitespace-nowrap">{mission.commander}</td>
                      <td className="px-4 py-3 text-[11px] font-mono text-[#8A94A6] whitespace-nowrap">{mission.location}</td>
                      <td className="px-4 py-3 text-[11px] font-mono text-[#8A94A6] whitespace-nowrap">{mission.startedAt ?? "—"}</td>
                      <td className="px-4 py-3 text-[11px] font-mono text-[#8A94A6] whitespace-nowrap">{mission.endedAt ?? "—"}</td>
                      <td className="px-4 py-3"><ResultPill result={mission.result} /></td>
                      <td className="px-4 py-3 text-[12px] font-mono text-[#8A94A6]">
                        <span className="flex items-center gap-1"><Navigation size={10} />{mission.droneCount}</span>
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={e => { e.stopPropagation(); onOpen(mission); }}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-mono text-[#C8A24A] hover:bg-[rgba(200,162,74,0.08)] transition-all"
                        >
                          <Eye size={13} /> Details
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex items-center justify-between px-2">
        <div className="text-[11px] font-mono text-[#8A94A6]">
          Showing {(page - 1) * perPage + 1} to {Math.min(page * perPage, sorted.length)} of {sorted.length}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="p-1.5 rounded-lg text-[#8A94A6] hover:bg-white/5 disabled:opacity-30 disabled:hover:bg-transparent transition-all"
          >
            <ChevronLeft size={14} />
          </button>
          <div className="text-[11px] font-mono text-[#E6EAF0] px-2 border border-white/10 rounded px-2 py-1 bg-[#161D26]">
            {page} / {totalPages}
          </div>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="p-1.5 rounded-lg text-[#8A94A6] hover:bg-white/5 disabled:opacity-30 disabled:hover:bg-transparent transition-all"
          >
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
