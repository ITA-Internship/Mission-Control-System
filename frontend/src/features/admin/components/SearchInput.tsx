import { Search, X } from "lucide-react";

interface SearchInputProps {
  id: string;
  label: string;
  value: string;
  placeholder: string;
  onChange: (value: string) => void;
}

export function SearchInput({
  id,
  label,
  value,
  placeholder,
  onChange,
}: SearchInputProps) {
  return (
    <div className="relative w-full min-w-48 sm:max-w-72">
      <label
        htmlFor={id}
        className="sr-only"
      >
        {label}
      </label>

      <Search
        size={14}
        className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-mc-muted"
        aria-hidden="true"
      />

      <input
        id={id}
        type="search"
        value={value}
        placeholder={placeholder}
        onChange={(event) =>
          onChange(event.target.value)
        }
        autoComplete="off"
        spellCheck={false}
        className="h-9 w-full rounded-lg border border-white/9 bg-mc-panel pr-8 pl-9 text-sm text-mc-text transition-colors placeholder:text-mc-subtle focus:border-mc-accent/60 focus:ring-2 focus:ring-mc-accent/15 focus:outline-none [&::-webkit-search-cancel-button]:hidden"
      />

      {value ? (
        <button
          type="button"
          onClick={() => onChange("")}
          className="absolute top-1/2 right-2 -translate-y-1/2 rounded p-1 text-mc-muted transition-colors hover:text-mc-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mc-accent/40"
        >
          <X
            size={12}
            aria-hidden="true"
          />

          <span className="sr-only">
            Clear search
          </span>
        </button>
      ) : null}
    </div>
  );
}
