import {
  ChevronDown,
  Filter,
  Search,
  CheckCircle2,
} from "lucide-react";
import { STATUS_UI, CLASSIFICATIONS } from "../utils/constants";
import { FilterChip } from "./FilterChip";
import { ClassPill } from "./ClassPill";
import type { Classification, DroneStatus } from "../types";

interface FilterSectionProps {
  search: string;
  onSearchChange: (value: string) => void;
  statusFilter: DroneStatus[];
  onStatusToggle: (status: DroneStatus) => void;
  statusOpen: boolean;
  onStatusOpenChange: (open: boolean) => void;
  classFilter: Classification[];
  onClassificationToggle: (classification: Classification) => void;
  classOpen: boolean;
  onClassOpenChange: (open: boolean) => void;
  hasFilters: boolean;
  onClearAll: () => void;
}

export function FilterSection({
  search,
  onSearchChange,
  statusFilter,
  onStatusToggle,
  statusOpen,
  onStatusOpenChange,
  classFilter,
  onClassificationToggle,
  classOpen,
  onClassOpenChange,
  hasFilters,
  onClearAll,
}: FilterSectionProps) {
  const statusEntries = Object.entries(STATUS_UI) as [
    DroneStatus,
    (typeof STATUS_UI)[DroneStatus],
  ][];

  const handleStatusClick = () => {
    onStatusOpenChange(!statusOpen);
    onClassOpenChange(false);
  };

  const handleClassClick = () => {
    onClassOpenChange(!classOpen);
    onStatusOpenChange(false);
  };

  return (
    <div className="rounded-xl border border-white/8 bg-[#161D26] p-3">
      <div className="flex flex-wrap items-center gap-2">
        {/* Search Input */}
        <div className="relative min-w-[200px] flex-1">
          <Search
            size={13}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8A94A6]"
          />
          <input
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search serial, inventory, name…"
            className="w-full rounded-lg border border-white/8 bg-[#0F1620] py-2 pl-8 pr-3 text-[13px] text-[#E6EAF0] placeholder-[#8A94A6]/50 transition-all focus:outline-none focus:ring-1 focus:ring-[#C8A24A]/40"
          />
        </div>

        {/* Status Filter */}
        <div className="relative">
          <button
            onClick={handleStatusClick}
            className={`flex items-center gap-1.5 rounded-lg border px-3 py-2 text-[12px] transition-all ${
              statusFilter.length
                ? "border-[#C8A24A]/40 bg-[#C8A24A]/8 text-[#C8A24A]"
                : "border-white/10 bg-white/3 text-[#8A94A6] hover:text-[#E6EAF0]"
            }`}
          >
            <Filter size={12} />
            Status{statusFilter.length ? ` (${statusFilter.length})` : ""}
            <ChevronDown
              size={11}
              className={statusOpen ? "rotate-180 transition-transform" : "transition-transform"}
            />
          </button>
          {statusOpen && (
            <div className="absolute left-0 top-full z-30 mt-1 min-w-[180px] rounded-xl border border-white/10 bg-[#1C2535] p-1 shadow-2xl">
              {statusEntries.map(([key, status]) => (
                <button
                  key={key}
                  onClick={() => onStatusToggle(key)}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-[12px] transition-colors hover:bg-white/5"
                >
                  <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${status.dot}`} />
                  <span className="flex-1 text-[#E6EAF0]">{status.label}</span>
                  {statusFilter.includes(key) && (
                    <CheckCircle2 size={12} className="text-[#C8A24A]" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Classification Filter */}
        <div className="relative">
          <button
            onClick={handleClassClick}
            className={`flex items-center gap-1.5 rounded-lg border px-3 py-2 text-[12px] transition-all ${
              classFilter.length
                ? "border-[#C8A24A]/40 bg-[#C8A24A]/8 text-[#C8A24A]"
                : "border-white/10 bg-white/3 text-[#8A94A6] hover:text-[#E6EAF0]"
            }`}
          >
            <Filter size={12} />
            Classification{classFilter.length ? ` (${classFilter.length})` : ""}
            <ChevronDown
              size={11}
              className={classOpen ? "rotate-180 transition-transform" : "transition-transform"}
            />
          </button>
          {classOpen && (
            <div className="absolute left-0 top-full z-30 mt-1 min-w-[160px] rounded-xl border border-white/10 bg-[#1C2535] p-1 shadow-2xl">
              {CLASSIFICATIONS.map((classification) => (
                <button
                  key={classification}
                  onClick={() => onClassificationToggle(classification)}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-[12px] transition-colors hover:bg-white/5"
                >
                  <ClassPill c={classification} />
                  <span className="flex-1" />
                  {classFilter.includes(classification) && (
                    <CheckCircle2 size={12} className="text-[#C8A24A]" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Active Filters */}
      {hasFilters && (
        <div className="mt-2.5 flex flex-wrap items-center gap-2 border-t border-white/5 pt-2.5">
          {statusFilter.map((status) => (
            <FilterChip
              key={status}
              label={STATUS_UI[status]?.label || status}
              onRemove={() => onStatusToggle(status)}
            />
          ))}
          {classFilter.map((classification) => (
            <FilterChip
              key={classification}
              label={classification}
              onRemove={() => onClassificationToggle(classification)}
            />
          ))}
          {search && (
            <FilterChip label={`"${search}"`} onRemove={() => onSearchChange("")} />
          )}
          <button
            onClick={onClearAll}
            className="ml-1 text-[11px] text-[#8A94A6] transition-colors hover:text-[#E5484D]"
          >
            Clear all
          </button>
        </div>
      )}
    </div>
  );
}
