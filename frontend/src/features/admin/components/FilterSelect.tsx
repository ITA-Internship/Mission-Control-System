import {
  ChevronDown,
  Funnel,
} from "lucide-react";

export interface FilterOption {
  value: string;
  label: string;
}

interface FilterSelectProps {
  id: string;
  label: string;
  value: string;
  placeholder: string;
  options: readonly FilterOption[];
  disabled?: boolean;
  onChange: (value: string) => void;
}

export function FilterSelect({
  id,
  label,
  value,
  placeholder,
  options,
  disabled = false,
  onChange,
}: FilterSelectProps) {
  return (
    <div className="relative">
      <label
        htmlFor={id}
        className="sr-only"
      >
        {label}
      </label>

      <Funnel
        size={14}
        className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-mc-muted"
        aria-hidden="true"
      />

      <select
        id={id}
        value={value}
        disabled={disabled}
        onChange={(event) =>
          onChange(event.target.value)
        }
        className={[
          "h-9 appearance-none rounded-lg border border-white/9 bg-mc-panel",
          "cursor-pointer pr-8 pl-8 text-sm transition-colors",
          "focus:border-mc-accent/60 focus:ring-2 focus:ring-mc-accent/15 focus:outline-none",
          "disabled:cursor-not-allowed disabled:opacity-50",
          value ? "text-mc-text" : "text-mc-muted",
        ].join(" ")}
      >
        <option value="">{placeholder}</option>

        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
          >
            {option.label}
          </option>
        ))}
      </select>

      <ChevronDown
        size={14}
        className="pointer-events-none absolute top-1/2 right-2.5 -translate-y-1/2 text-mc-muted"
        aria-hidden="true"
      />
    </div>
  );
}
