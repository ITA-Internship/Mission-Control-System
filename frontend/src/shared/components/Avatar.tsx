export type AvatarSize = "sm" | "md";

interface AvatarProps {
  name: string;
  size?: AvatarSize;
}

const sizeStyles: Record<AvatarSize, string> = {
  sm: "size-7 text-[11px]",
  md: "size-8 text-sm",
};

function getInitial(name: string): string {
  const parts = name
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  const lastPart = parts.at(-1) ?? "";

  return (
    lastPart.charAt(0).toUpperCase() || "?"
  );
}

export function Avatar({
  name,
  size = "sm",
}: AvatarProps) {
  return (
    <span
      className={[
        "flex shrink-0 items-center justify-center rounded-full",
        "bg-mc-accent/15 font-bold text-mc-accent",
        sizeStyles[size],
      ].join(" ")}
      aria-hidden="true"
    >
      {getInitial(name)}
    </span>
  );
}
