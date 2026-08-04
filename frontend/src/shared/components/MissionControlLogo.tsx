interface MissionControlLogoProps {
  className?: string;
}

export function MissionControlLogo({
  className,
}: MissionControlLogoProps) {
  return (
    <svg
      className={className}
      width="40"
      height="40"
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <circle
        cx="20"
        cy="20"
        r="19"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeDasharray="3 2"
      />

      <circle
        cx="20"
        cy="20"
        r="13"
        stroke="currentColor"
        strokeWidth="1"
        opacity="0.4"
      />

      <line
        x1="20"
        y1="1"
        x2="20"
        y2="8"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <line
        x1="20"
        y1="32"
        x2="20"
        y2="39"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <line
        x1="1"
        y1="20"
        x2="8"
        y2="20"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <line
        x1="32"
        y1="20"
        x2="39"
        y2="20"
        stroke="currentColor"
        strokeWidth="1.5"
      />

      <circle cx="20" cy="20" r="3" fill="currentColor" />

      <line
        x1="20"
        y1="20"
        x2="14"
        y2="14"
        stroke="currentColor"
        opacity="0.7"
      />
      <line
        x1="20"
        y1="20"
        x2="26"
        y2="14"
        stroke="currentColor"
        opacity="0.7"
      />
      <line
        x1="20"
        y1="20"
        x2="14"
        y2="26"
        stroke="currentColor"
        opacity="0.7"
      />
      <line
        x1="20"
        y1="20"
        x2="26"
        y2="26"
        stroke="currentColor"
        opacity="0.7"
      />

      <circle
        cx="13"
        cy="13"
        r="2"
        stroke="currentColor"
        opacity="0.6"
      />
      <circle
        cx="27"
        cy="13"
        r="2"
        stroke="currentColor"
        opacity="0.6"
      />
      <circle
        cx="13"
        cy="27"
        r="2"
        stroke="currentColor"
        opacity="0.6"
      />
      <circle
        cx="27"
        cy="27"
        r="2"
        stroke="currentColor"
        opacity="0.6"
      />
    </svg>
  );
}
