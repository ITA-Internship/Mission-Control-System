import { useState } from "react";
import { ChevronDown, Search, X } from "lucide-react";
import type { Result, Status } from "../types";
import { STATUS_META } from "./Pills";

export interface Chip {
  key: string;
  label: string;
}

export interface Filters {
  search: string;
  status: Status | "";
  commander: string;
  result: Result | "";
}

export interface FilterBarProps {
  filters: Filters;
  setFilters: (f: Filters) => void;
  chips: Chip[];
  removeChip: (key: string) => void;
  availableCommanders: string[];
}

function FilterChip({ chip, onRemove }: { chip: Chip; onRemove: () => void }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[9px] font-mono bg-[#C8A24A]/[0.12] text-[#C8A24A] border border-[#C8A24A]/25"
    >
      {chip.label}
      <button
        onClick={onRemove}
        className="hover:opacity-70 transition-opacity"
        aria-label="Remove filter"
      >
        <X size={10} />
      </button>
    </span>
  );
}

export function FilterBar({
  filters,
  setFilters,
  chips,
  removeChip,
  availableCommanders,
}: FilterBarProps) {
  const [statusOpen, setStatusOpen] = useState(false);
  const [cmdOpen, setCmdOpen] = useState(false);
  const [resultOpen, setResultOpen] = useState(false);

  const dropdownClass = "absolute top-full left-0 mt-1 min-w-[160px] rounded-lg border py-1 z-50 bg-[#1E2733] border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.5)]";
  const optClass = "flex items-center gap-2 w-full text-left px-2.5 py-1.5 text-[9px] font-mono text-[#E6EAF0] hover:bg-white/5 transition-colors";

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 flex-wrap">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search size={11} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#8A94A6]" />
          <input
            type="text"
            placeholder="Search title or location…"
            value={filters.search}
            onChange={e => setFilters({ ...filters, search: e.target.value })}
            className="w-full pl-7 pr-2.5 py-1.5 rounded-lg text-[9px] font-mono text-[#E6EAF0] placeholder-[#8A94A6] outline-none focus:ring-1 focus:ring-[#C8A24A]/40 transition-all bg-[#161D26] border border-white/[0.08]"
          />
        </div>

        {/* Status dropdown */}
        <div className="relative">
          <button
            onClick={() => { setStatusOpen(o => !o); setCmdOpen(false); setResultOpen(false); }}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[9px] font-mono text-[#8A94A6] hover:text-[#E6EAF0] transition-colors bg-[#161D26] border border-white/[0.08]"
          >
            Status {filters.status && <span className="text-[#C8A24A]">·</span>}
            {filters.status || "All"}
            <ChevronDown size={11} />
          </button>
          {statusOpen && (
            <div className={dropdownClass}>
              {(["", "Planned", "Active", "Completed", "Aborted"] as const).map(s => (
                <button
                  key={s || "all"}
                  className={optClass}
                  onClick={() => { setFilters({ ...filters, status: s }); setStatusOpen(false); }}
                >
                  {s ? <span className="w-1.5 h-1.5 rounded-full" style={{ background: STATUS_META[s].color }} /> : <span className="w-1.5 h-1.5" />}
                  {s || "All Statuses"}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Commander dropdown */}
        <div className="relative">
          <button
            onClick={() => { setCmdOpen(o => !o); setStatusOpen(false); setResultOpen(false); }}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[9px] font-mono text-[#8A94A6] hover:text-[#E6EAF0] transition-colors bg-[#161D26] border border-white/[0.08]"
          >
            Commander {filters.commander && <span className="text-[#C8A24A]">·</span>}
            {filters.commander ? filters.commander.split(" ").slice(-1)[0] : "All"}
            <ChevronDown size={11} />
          </button>
          {cmdOpen && (
            <div className={dropdownClass}>
              <button className={optClass} onClick={() => { setFilters({ ...filters, commander: "" }); setCmdOpen(false); }}>
                All Commanders
              </button>
              {availableCommanders.map(c => (
                <button key={c} className={optClass} onClick={() => { setFilters({ ...filters, commander: c }); setCmdOpen(false); }}>
                  {c}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Result dropdown */}
        <div className="relative">
          <button
            onClick={() => { setResultOpen(o => !o); setStatusOpen(false); setCmdOpen(false); }}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[9px] font-mono text-[#8A94A6] hover:text-[#E6EAF0] transition-colors bg-[#161D26] border border-white/[0.08]"
          >
            Result {filters.result && <span className="text-[#C8A24A]">·</span>}
            {filters.result || "All"}
            <ChevronDown size={11} />
          </button>
          {resultOpen && (
            <div className={dropdownClass}>
              {(["", "Success", "Failure"] as const).map(r => (
                <button
                  key={r || "all"}
                  className={optClass}
                  onClick={() => { setFilters({ ...filters, result: r }); setResultOpen(false); }}
                >
                  {r || "All Results"}
                </button>
              ))}
            </div>
          )}
        </div>

        {chips.length > 0 && (
          <button
            onClick={() => setFilters({ search: "", status: "", commander: "", result: "" })}
            className="text-[9px] font-mono text-[#8A94A6] hover:text-[#E5484D] transition-colors"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Active chips */}
      {chips.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          {chips.map(chip => (
            <FilterChip key={chip.key} chip={chip} onRemove={() => removeChip(chip.key)} />
          ))}
        </div>
      )}
    </div>
  );
}
