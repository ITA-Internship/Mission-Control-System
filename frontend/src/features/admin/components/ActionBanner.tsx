import {
  CircleAlert,
  CircleCheck,
  X,
} from "lucide-react";

export type BannerTone = "success" | "error";

export interface BannerMessage {
  tone: BannerTone;
  text: string;
}

interface ActionBannerProps {
  message: BannerMessage;
  onDismiss: () => void;
}

const toneStyles: Record<BannerTone, string> = {
  success:
    "border-mc-success/30 bg-mc-success/10 text-mc-success",
  error:
    "border-mc-error/30 bg-mc-error/10 text-mc-error",
};

export function ActionBanner({
  message,
  onDismiss,
}: ActionBannerProps) {
  const Icon =
    message.tone === "success"
      ? CircleCheck
      : CircleAlert;

  return (
    <div
      role="status"
      aria-live="polite"
      className={[
        "flex items-start gap-2.5 rounded-lg border px-3.5 py-2.5 text-sm",
        toneStyles[message.tone],
      ].join(" ")}
    >
      <Icon
        size={15}
        className="mt-0.5 shrink-0"
        aria-hidden="true"
      />

      <p className="flex-1">{message.text}</p>

      <button
        type="button"
        onClick={onDismiss}
        className="rounded p-0.5 transition-opacity hover:opacity-70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-current"
      >
        <X
          size={14}
          aria-hidden="true"
        />

        <span className="sr-only">
          Dismiss message
        </span>
      </button>
    </div>
  );
}
