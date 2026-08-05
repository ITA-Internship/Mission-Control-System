import { X } from "lucide-react";

interface FilterChipProps {
  label: string;
  onRemove: () => void;
}

export function FilterChip({ label, onRemove }: FilterChipProps) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-[#C8A24A]/30 bg-[#C8A24A]/15 px-2 py-0.5 text-[11px] font-medium text-[#C8A24A]">
      {label}
      <button onClick={onRemove} className="transition-colors hover:text-white">
        <X size={10} />
      </button>
    </span>
  );
}
