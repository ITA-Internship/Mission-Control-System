import type { AuditResult } from "../types/admin";

interface ResultPillProps {
  result: AuditResult;
}

export function ResultPill({
  result,
}: ResultPillProps) {
  const isSuccess = result === "SUCCESS";

  return (
    <span
      className={[
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5",
        "text-[11px] font-semibold whitespace-nowrap",
        isSuccess
          ? "bg-mc-success/12 text-mc-success"
          : "bg-mc-error/12 text-mc-error",
      ].join(" ")}
    >
      <span
        className="size-1.5 rounded-full bg-current"
        aria-hidden="true"
      />

      {isSuccess ? "Success" : "Failure"}
    </span>
  );
}
