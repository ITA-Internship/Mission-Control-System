import type { Classification } from "../types";
import { CLASS_COLORS } from "../utils/constants";

interface ClassPillProps {
  c: Classification;
}

export function ClassPill({ c }: ClassPillProps) {
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium tracking-wide ${CLASS_COLORS[c]}`}>
      {c}
    </span>
  );
}
