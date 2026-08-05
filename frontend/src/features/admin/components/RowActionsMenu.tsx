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

  const triggerRef =
    useRef<HTMLButtonElement>(null);

  const itemRefs = useRef<
    Array<HTMLButtonElement | null>
  >([]);

  function closeMenu(restoreFocus: boolean) {
    setIsOpen(false);

    if (restoreFocus) {
      triggerRef.current?.focus();
    }
  }

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    // Move focus into the menu on open so keyboard/SR users land on the first
    // action rather than being left on the (now-expanded) trigger.
    itemRefs.current[0]?.focus();

    function handlePointerDown(
      event: MouseEvent,
    ) {
      if (
        !containerRef.current?.contains(
          event.target as Node,
        )
      ) {
        // Pointer dismissal: don't yank focus back to the trigger — it belongs
        // wherever the user clicked.
        setIsOpen(false);
      }
    }

    function handleKeyDown(
      event: KeyboardEvent,
    ) {
      if (event.key === "Escape") {
        closeMenu(true);
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

  function handleMenuKeyDown(
    event: React.KeyboardEvent,
  ) {
    const items =
      itemRefs.current.filter(
        (item): item is HTMLButtonElement =>
          item !== null,
      );

    if (items.length === 0) {
      return;
    }

    const current = items.indexOf(
      document.activeElement as HTMLButtonElement,
    );

    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        items[
          current < 0
            ? 0
            : (current + 1) % items.length
        ].focus();
        break;
      case "ArrowUp":
        event.preventDefault();
        items[
          current < 0
            ? items.length - 1
            : (current - 1 + items.length) %
              items.length
        ].focus();
        break;
      case "Home":
        event.preventDefault();
        items[0].focus();
        break;
      case "End":
        event.preventDefault();
        items[items.length - 1].focus();
        break;
    }
  }

  return (
    <div
      ref={containerRef}
      className="relative inline-block text-left"
    >
      <button
        ref={triggerRef}
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
          onKeyDown={handleMenuKeyDown}
          className="absolute right-0 z-20 mt-1 w-46 rounded-lg border border-white/10 bg-mc-elevated py-1 shadow-xl"
        >
          {actions.map((action, index) => (
            <button
              key={action.key}
              ref={(element) => {
                itemRefs.current[index] =
                  element;
              }}
              type="button"
              role="menuitem"
              tabIndex={index === 0 ? 0 : -1}
              onClick={() => {
                closeMenu(true);
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
