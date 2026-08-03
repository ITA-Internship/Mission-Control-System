import {
  useEffect,
  useRef,
  useState,
} from "react";
import type { ReactNode } from "react";
import { Ellipsis } from "lucide-react";

export type ActionTone =
  | "default"
  | "danger"
  | "success";

export interface RowAction {
  key: string;
  label: string;
  icon: ReactNode;
  tone?: ActionTone;
  onSelect: () => void;
}

interface RowActionsMenuProps {
  label: string;
  actions: RowAction[];
}

const toneClasses: Record<
  ActionTone,
  string
> = {
  default: "text-mc-text",
  danger: "text-mc-error",
  success: "text-mc-success",
};

export function RowActionsMenu({
  label,
  actions,
}: RowActionsMenuProps) {
  const [isOpen, setIsOpen] = useState(false);

  const containerRef =
    useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    function handlePointerDown(
      event: MouseEvent,
    ) {
      if (
        !containerRef.current?.contains(
          event.target as Node,
        )
      ) {
        setIsOpen(false);
      }
    }

    function handleKeyDown(
      event: KeyboardEvent,
    ) {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    }

    document.addEventListener(
      "mousedown",
      handlePointerDown,
    );

    document.addEventListener(
      "keydown",
      handleKeyDown,
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handlePointerDown,
      );

      document.removeEventListener(
        "keydown",
        handleKeyDown,
      );
    };
  }, [isOpen]);

  return (
    <div
      ref={containerRef}
      className="relative inline-block text-left"
    >
      <button
        type="button"
        onClick={() =>
          setIsOpen((open) => !open)
        }
        aria-haspopup="menu"
        aria-expanded={isOpen}
        className="rounded p-1.5 text-mc-muted transition-colors hover:bg-white/5 hover:text-mc-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mc-accent/40"
      >
        <Ellipsis
          size={16}
          aria-hidden="true"
        />

        <span className="sr-only">
          {label}
        </span>
      </button>

      {isOpen ? (
        <div
          role="menu"
          aria-label={label}
          className="absolute right-0 z-20 mt-1 w-46 rounded-lg border border-white/10 bg-mc-elevated py-1 shadow-xl"
        >
          {actions.map((action) => (
            <button
              key={action.key}
              type="button"
              role="menuitem"
              onClick={() => {
                setIsOpen(false);
                action.onSelect();
              }}
              className={[
                "flex w-full items-center gap-2 px-3 py-2 text-left text-xs",
                "transition-colors hover:bg-white/5",
                "focus-visible:outline-none focus-visible:bg-white/5",
                toneClasses[
                  action.tone ?? "default"
                ],
              ].join(" ")}
            >
              <span
                className="shrink-0"
                aria-hidden="true"
              >
                {action.icon}
              </span>

              {action.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
