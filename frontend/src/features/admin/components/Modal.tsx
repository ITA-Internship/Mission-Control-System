import {
  useEffect,
  useId,
  useRef,
} from "react";
import type { ReactNode } from "react";
import { X } from "lucide-react";

interface ModalProps {
  title: string;
  description?: string;
  onClose: () => void;
  children: ReactNode;
}

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(", ");

export function Modal({
  title,
  description,
  onClose,
  children,
}: ModalProps) {
  const dialogRef =
    useRef<HTMLDivElement>(null);

  const titleId = useId();
  const descriptionId = useId();

  useEffect(() => {
    const previouslyFocused =
      document.activeElement as HTMLElement | null;

    const focusables =
      dialogRef.current?.querySelectorAll<HTMLElement>(
        FOCUSABLE_SELECTOR,
      );

    (
      focusables?.[0] ?? dialogRef.current
    )?.focus();

    return () => {
      previouslyFocused?.focus?.();
    };
  }, []);

  useEffect(() => {
    function handleKeyDown(
      event: KeyboardEvent,
    ) {
      if (event.key === "Escape") {
        event.stopPropagation();
        onClose();
        return;
      }

      if (event.key !== "Tab") {
        return;
      }

      const focusables = Array.from(
        dialogRef.current?.querySelectorAll<HTMLElement>(
          FOCUSABLE_SELECTOR,
        ) ?? [],
      );

      if (focusables.length === 0) {
        return;
      }

      const first = focusables[0];
      const last = focusables.at(-1)!;
      const active = document.activeElement;

      if (
        event.shiftKey &&
        (active === first ||
          !dialogRef.current?.contains(active))
      ) {
        event.preventDefault();
        last.focus();
        return;
      }

      if (
        !event.shiftKey &&
        (active === last ||
          !dialogRef.current?.contains(active))
      ) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener(
      "keydown",
      handleKeyDown,
    );

    return () => {
      document.removeEventListener(
        "keydown",
        handleKeyDown,
      );
    };
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-black/72 p-4">
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={
          description ? descriptionId : undefined
        }
        tabIndex={-1}
        className="my-auto w-full max-w-lg rounded-xl border border-white/10 bg-mc-card shadow-2xl focus:outline-none"
      >
        <div className="flex items-start justify-between gap-4 border-b border-white/8 px-6 py-4">
          <div>
            <h2
              id={titleId}
              className="text-base font-semibold text-mc-text"
            >
              {title}
            </h2>

            {description ? (
              <p
                id={descriptionId}
                className="mt-1 text-xs text-mc-muted"
              >
                {description}
              </p>
            ) : null}
          </div>

          <button
            type="button"
            onClick={onClose}
            className="-mt-1 rounded-lg p-1 text-mc-muted transition-colors hover:bg-white/5 hover:text-mc-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mc-accent/40"
          >
            <X
              size={16}
              aria-hidden="true"
            />

            <span className="sr-only">
              Close dialog
            </span>
          </button>
        </div>

        <div className="px-6 py-5">
          {children}
        </div>
      </div>
    </div>
  );
}
